# -*- coding: utf-8 -*-
"""Write every group of identical functions to re/identical_groups.json, so one read covers all its copies.

re/g_identical_functions.py counts the groups; this records them, because the count is a finding and the ADDRESSES are a resource.
Thirty-five functions identical to 0x923110 means one implementation and one ledger claim for thirty-five addresses, and that has to
be machine-readable or every later tool will keep reporting thirty-five separate items.

Format:

    {"groups": [{"fingerprint": "<sha1 of the normalised shape>", "instructions": 113, "copies": 35,
                 "addresses": [0x923110, 0x923480, ...]}, ...]}

The fingerprint is a hash rather than the shape itself, because the shape of a 400-instruction function is a large string and the
addresses are what a consumer needs. A consumer wanting the shape can call the same normaliser.

CONSUMERS. Two exist already in intent: re/g_fanout.py, which counts DISTINCT CALLEES and should count a group once, and
re/g_cheapest.py, whose byte totals are inflated by every duplicate. This does not change them yet; it makes the data available so
that the change is a small edit rather than another reading of every function.

A SELF-CHECK, per the rule: the tool knows 0x923110 is in a group of thirty-five, because the previous round established it by
running the other tool. If this one does not find that group, it refuses to write.
"""
import collections
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib as LIB           # noqa: E402
from lib import disasm, load_prof  # noqa: E402

OUT = os.path.join(HERE, "identical_groups.json")
HEX = re.compile(r"0x([0-9a-f]+)")
RIP = re.compile(r"\[rip \+ 0x[0-9a-f]+\]")
CODE_LOW, CODE_HIGH = 0x400000, 0x9C0000

SELF_CHECK_ADDRESS = 0x923110
SELF_CHECK_COPIES = 35


def normalise(ins):
    text = RIP.sub("[rip]", ins.op_str.replace(" ", ""))

    def replace(match):
        value = int(match.group(1), 16)
        if CODE_LOW <= value < CODE_HIGH:
            return "<addr>"
        if ins.mnemonic in ("call", "jmp") or ins.mnemonic.startswith("j"):
            return "<addr>"
        if value > 0x100000:
            return "<addr>"
        return match.group(0)

    return "%s %s" % (ins.mnemonic, HEX.sub(replace, text))


def shape(address, profile):
    size = (profile.get(address) or {}).get("size") or 0
    out = []
    for ins in disasm(address):
        if ins.address >= address + size:
            break
        out.append(normalise(ins))
    return out


def main():
    profile = load_prof()
    groups = collections.defaultdict(list)
    for address, info in profile.items():
        size = info.get("size") or 0
        if not (8 <= size <= 20000) or not (CODE_LOW <= address < CODE_HIGH):
            continue
        text = shape(address, profile)
        if len(text) < 8:
            continue
        groups[tuple(text)].append(address)

    # ---- the self-check: the group the previous round established -----------------------------------------------------------------
    check = None
    for text, addresses in groups.items():
        if SELF_CHECK_ADDRESS in addresses:
            check = (len(text), len(addresses))
            break
    print("SELF-CHECK: 0x%X is in a group of %s functions of %s instructions (expected %d)"
          % (SELF_CHECK_ADDRESS, check[1] if check else "?", check[0] if check else "?", SELF_CHECK_COPIES))
    if not check or check[1] != SELF_CHECK_COPIES:
        print("REFUSING TO WRITE: the group the previous round established is not found, so this run's grouping is suspect.")
        return 2

    payload = []
    for text, addresses in groups.items():
        if len(addresses) < 2:
            continue
        payload.append({
            "fingerprint": hashlib.sha1("\n".join(text).encode("utf-8")).hexdigest()[:16],
            "instructions": len(text),
            "copies": len(addresses),
            "addresses": sorted(addresses),
        })
    payload.sort(key=lambda g: (-g["copies"], -g["instructions"]))
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"groups": payload}, indent=1, sort_keys=True))

    total = sum(g["copies"] for g in payload)
    saved = total - len(payload)
    print("")
    print("groups written: %d, covering %d function addresses" % (len(payload), total))
    print("reading one implementation per group means %d reads instead of %d, a saving of %d" % (len(payload), total, saved))
    print("")
    print("the five largest groups:")
    for group in payload[:5]:
        print("   %3d copies x %4d instructions   first 0x%X" % (group["copies"], group["instructions"], group["addresses"][0]))
    print("")
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
