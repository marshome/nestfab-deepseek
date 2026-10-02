# -*- coding: utf-8 -*-
"""Group the named parameters by BASE OBJECT, so each group is one struct's field list.

A name-to-field pair is only half a fact: the field belongs to whichever object the parser was filling, and `rsi` in one function is not
`rsi` in another. What makes the pairs usable is that a function which fills many parameters fills them into ONE object, so a function's
pairs are that object's fields -- and two functions whose offsets do not collide are probably the same object seen twice.

    python g_param_layouts.py [--min 4]
Output: re/param_layouts.json

A group with many parameters and no duplicate offsets is a candidate layout. A group with duplicate offsets means the function fills
MORE THAN ONE object, and then the base register alone is not enough to separate them -- which is stated per group rather than assumed
away, because that is exactly the failure the element50 claim recorded.

A SELF-CHECK, per the rule: 0x4EC00 must produce a group containing +0x100 named nesting_pow_boost, which was verified by hand.
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
STORE_FIELD = re.compile(r"^(byte|word|dword|qword) ptr \[([a-z0-9]+) \+ (0x[0-9a-f]+)\], ")
SELF_CHECK = (0x4EC00, "nesting_pow_boost", 0x100)


def pairs_in(address, profile):
    size = (profile.get(address) or {}).get("size") or 0
    body = [i for i in disasm(address) if i.address < address + size]
    out = []
    for index, ins in enumerate(body):
        if ins.mnemonic != "call":
            continue
        match = DIRECT.match(ins.op_str.strip())
        if not match or int(match.group(1), 16) != LOOKUP:
            continue
        for forward in range(index + 1, min(index + 8, len(body))):
            stored = STORE_FIELD.match(body[forward].op_str.strip())
            if stored:
                out.append((stored.group(2), int(stored.group(3), 16), stored.group(1)))
                break
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=int, default=4)
    args = parser.parse_args(argv)
    profile = load_prof()

    check = pairs_in(SELF_CHECK[0], profile)
    ok = any(base == "rsi" and offset == SELF_CHECK[2] for base, offset, _w in check)
    print("SELF-CHECK: 0x%X fills rsi+0x%X?  %s" % (SELF_CHECK[0], SELF_CHECK[2], ok))
    if not ok:
        print("REFUSING TO REPORT: the function verified by hand does not produce its field.")
        return 2
    print("")

    groups = {}
    for caller in sorted(set((profile.get(LOOKUP) or {}).get("callers") or [])):
        pairs = pairs_in(caller, profile)
        if len(pairs) >= args.min:
            groups[caller] = pairs

    print("functions filling %d or more parameters: %d" % (args.min, len(groups)))
    print("")
    payload = {}
    for caller, pairs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        by_base = collections.defaultdict(dict)
        for base, offset, width in pairs:
            by_base[base].setdefault(offset, []).append(width)
        best = max(by_base.items(), key=lambda kv: len(kv[1]))
        base, fields = best
        duplicates = {offset: widths for offset, widths in fields.items() if len(widths) > 1}
        size = (profile.get(caller) or {}).get("size") or 0
        print("0x%-8X %6d B  %2d params into `%s`%s"
              % (caller, size, len(fields), base,
                 "  AND %d duplicate offset(s)" % len(duplicates) if duplicates else ""))
        payload["0x%X" % caller] = {"base": base,
                                    "fields": {"+0x%X" % o: w for o, w in sorted(fields.items())},
                                    "duplicates": ["+0x%X" % o for o in sorted(duplicates)]}
    io.open(os.path.join(HERE, "param_layouts.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps({"layouts": payload}, indent=1, sort_keys=True))
    print("")
    print("A group with NO duplicate offsets is a candidate layout for one struct. A group WITH duplicates fills more than one object,")
    print("and then the base register alone does not separate them -- stated per group rather than assumed away.")
    print("")
    print("wrote re/param_layouts.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
