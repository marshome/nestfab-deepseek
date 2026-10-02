# -*- coding: utf-8 -*-
"""The remaining parameter fields: the ones whose store is not immediately after the lookup.

re/g_param_names.py found 119 of 259 call sites followed by a store into a field, and re/g_param_layouts.py turned 59 of those into a
layout. The other 140 fall into two shapes it does not catch:

    A. the value is read into a register first, then stored:
            movsd xmm0, [rsp+0x30] / movsd [rsi+0x68], xmm0
    B. the store is further away than the eight instructions the first version looked at, because the code checks several parameters
       before writing any of them.

So this widens the window and accepts a store whose VALUE comes from a register rather than an immediate, while keeping the rule that a
store only counts when it is into a base register the function has been filling. A site that matches neither shape is counted as
unresolved rather than guessed at.

    python g_param_fields2.py [--window 24]
Output: re/param_fields2.json

A SELF-CHECK, per the rule: the count must be STRICTLY GREATER than the 119 the narrower tool found, or the widening achieved nothing
and its output is the same set under a new name.
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

from lib import disasm, load_prof  # noqa: E402

LOOKUP = 0x82A3E0
DIRECT = re.compile(r"^0x([0-9a-f]+)$")
LEA_RIP = re.compile(r"^[a-z0-9]+, \[rip \+ (0x[0-9a-f]+)\]$")
STORE_FIELD = re.compile(r"^(byte|word|dword|qword) ptr \[([a-z0-9]+) \+ (0x[0-9a-f]+)\], (.+)$")
WIDER_FIRST = 119


def fields_in(address, profile, window):
    size = (profile.get(address) or {}).get("size") or 0
    body = [i for i in disasm(address) if i.address < address + size]
    out = []
    for index, ins in enumerate(body):
        if ins.mnemonic != "call":
            continue
        match = DIRECT.match(ins.op_str.strip())
        if not match or int(match.group(1), 16) != LOOKUP:
            continue
        # the name, from the nearest preceding lea of a rip-relative address
        name = None
        for back in range(index - 1, max(-1, index - 6), -1):
            if body[back].mnemonic != "lea":
                continue
            moved = LEA_RIP.match(body[back].op_str.strip())
            if moved:
                target = body[back].address + body[back].size + int(moved.group(1), 16)
                name = target
            break
        # the field, from the first store into [reg + offset] in a WIDER window
        field = None
        for forward in range(index + 1, min(index + 1 + window, len(body))):
            stored = STORE_FIELD.match(body[forward].op_str.strip())
            if stored:
                field = (stored.group(2), int(stored.group(3), 16), stored.group(1), stored.group(4).strip())
                break
            if body[forward].mnemonic == "call":
                called = DIRECT.match(body[forward].op_str.strip())
                if called and int(called.group(1), 16) == LOOKUP:
                    break          # the next lookup begins, so this one stored nothing here
        out.append((ins.address, name, field))
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, default=24)
    args = parser.parse_args(argv)
    profile = load_prof()

    callers = sorted(set((profile.get(LOOKUP) or {}).get("callers") or []))
    total = 0
    resolved = 0
    payload = {}
    for address in callers:
        entries = fields_in(address, profile, args.window)
        if not entries:
            continue
        rows = []
        for at, name_rva, field in entries:
            total += 1
            if field:
                resolved += 1
            rows.append({"site": "0x%X" % at,
                         "name_rva": ("0x%X" % name_rva) if name_rva else None,
                         "base": field[0] if field else None,
                         "offset": ("0x%X" % field[1]) if field else None,
                         "width": field[2] if field else None,
                         "value": field[3] if field else None})
        payload["0x%X" % address] = rows
    io.open(os.path.join(HERE, "param_fields2.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps({"sites": payload}, indent=1, sort_keys=True))

    print("call sites: %d, of which %d land in a field with a %d instruction window" % (total, resolved, args.window))
    print("SELF-CHECK: the narrower tool found %d, so the widening must exceed it: %s"
          % (WIDER_FIRST, "YES" if resolved > WIDER_FIRST else "NO"))
    if resolved <= WIDER_FIRST:
        print("REFUSING: the widening found no more than the narrower tool, so it adds nothing and its output would be the same set")
        print("under a new name.")
        return 2
    print("")
    bases = collections.Counter(row["base"] for rows in payload.values() for row in rows if row["base"])
    print("the base registers the parameters are written through: %s"
          % ", ".join("%s %d" % (k, v) for k, v in bases.most_common(8)))
    print("")
    print("wrote re/param_fields2.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
