# -*- coding: utf-8 -*-
"""Every named parameter in the module: the name, the call site, and the field the value lands in.

RE 0x82A3E0 is 109 bytes and has 51 callers. Its callers pass a NAME in rdx and test the result, and when the lookup succeeds they store
a value into a field of the object they are filling. So each call site is a NAME-TO-FIELD mapping the module itself declares, and this
extracts them all.

    python g_param_names.py [--top 60]
Output: re/param_names.json

The pattern at a site, from 0x4EC00 which is the one verified by hand:

    0x4F496  lea rdx, [rip + 0x960a7d]      ; -> 'nesting_pow_boost'
    0x4F4A0  call 0x82a3e0                  ; look it up
    0x4F4A5  test eax, eax / jne <skip>
    0x4F4A9  movsd [rsi + 0x100], xmm6      ; THE FIELD

so after the call this looks for the first store into a struct field in the next few instructions, and records the offset when it finds
one. The name comes from the `lea` immediately before the call.

A SELF-CHECK, per the rule, against the one site already verified: the site at 0x4F4A0 must yield the name 'nesting_pow_boost' and the
offset +0x100. If it does not, the extraction is wrong and nothing else it says can be used.
"""
import argparse
import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib as LIB           # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

LOOKUP = 0x82A3E0
DIRECT = re.compile(r"^0x([0-9a-f]+)$")
LEA_RIP = re.compile(r"^[a-z0-9]+, \[rip \+ (0x[0-9a-f]+)\]$")
STORE_FIELD = re.compile(r"^(byte|word|dword|qword) ptr \[([a-z0-9]+) \+ (0x[0-9a-f]+)\], ")
SELF_CHECK_SITE = 0x4F4A0
SELF_CHECK_NAME = "nesting_pow_boost"
SELF_CHECK_OFFSET = 0x100


def image():
    return LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data


def string_at(rva, blob):
    offset = rva2off(rva)
    if offset is None or offset < 0 or offset >= len(blob):
        return None
    end = blob.find(b"\x00", offset)
    if end < 0 or end == offset or end - offset > 120:
        return None
    raw = blob[offset:end]
    if sum(1 for b in raw if 32 <= b < 127) < len(raw) * 0.9:
        return None
    return raw.decode("ascii", "replace")


def sites_in(address, profile, blob):
    size = (profile.get(address) or {}).get("size") or 0
    body = [i for i in disasm(address) if i.address < address + size]
    out = []
    for index, ins in enumerate(body):
        if ins.mnemonic != "call":
            continue
        match = DIRECT.match(ins.op_str.strip())
        if not match or int(match.group(1), 16) != LOOKUP:
            continue
        # the name: the nearest preceding lea of a rip-relative address
        name = None
        for back in range(index - 1, max(-1, index - 6), -1):
            previous = body[back]
            if previous.mnemonic != "lea":
                continue
            moved = LEA_RIP.match(previous.op_str.strip())
            if moved:
                target = previous.address + previous.size + int(moved.group(1), 16)
                name = string_at(target, blob)
            break
        # the field: the first store into [reg + offset] within the next few instructions
        field = None
        for forward in range(index + 1, min(index + 8, len(body))):
            stored = STORE_FIELD.match(body[forward].op_str.strip())
            if stored:
                field = (stored.group(2), int(stored.group(3), 16), stored.group(1))
                break
        out.append((ins.address, name, field))
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=60)
    args = parser.parse_args(argv)
    profile = load_prof()
    blob = image()

    # ---- the self-check against the site verified by hand ----------------------------------------------------------------
    check = [entry for entry in sites_in(0x4EC00, profile, blob) if entry[0] == SELF_CHECK_SITE]
    ok = check and check[0][1] == SELF_CHECK_NAME and check[0][2] and check[0][2][1] == SELF_CHECK_OFFSET
    print("SELF-CHECK: 0x%X yields %r with field %s?  %s"
          % (SELF_CHECK_SITE, check[0][1] if check else None, check[0][2] if check else None, bool(ok)))
    if not ok:
        print("REFUSING TO REPORT: the one site read by hand is not reproduced, so this extraction means nothing.")
        return 2
    print("")

    callers = sorted(set((profile.get(LOOKUP) or {}).get("callers") or []))
    payload = {}
    names = collections.Counter()
    with_field = 0
    total = 0
    for address in callers:
        entries = sites_in(address, profile, blob)
        if not entries:
            continue
        payload["0x%X" % address] = [{"site": "0x%X" % at, "name": name,
                                      "field": ("%s+0x%X" % (field[0], field[1])) if field else None}
                                     for at, name, field in entries]
        for _at, name, field in entries:
            total += 1
            if name:
                names[name] += 1
            if field:
                with_field += 1
    io.open(os.path.join(HERE, "param_names.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps({"parameters": payload}, indent=1, sort_keys=True))

    print("functions calling the lookup: %d" % len(callers))
    print("call sites: %d, of which %d name a parameter and %d land in a field" % (total, sum(names.values()), with_field))
    print("distinct NAMES: %d" % len(names))
    print("")
    print("the names, with how often each is looked up:")
    for name, count in names.most_common(args.top):
        print("   x%-3d %s" % (count, name[:110]))
    print("")
    print("wrote re/param_names.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
