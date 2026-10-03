#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Recover a class's FIELDS from the functions that write them, one instruction per position.

THE RULE, which is this project's: a field's POSITION needs an instruction, and the instruction must be a store whose base is the object.
That makes the this-pointer the crux -- a function's `rcx` on entry is the object only when the code treats it as one -- so this tool
requires the base register to have been LOADED FROM `rcx` (or from another register already known to hold it), and refuses offsets from a
register it cannot place.

WHAT IT IS FOR. Multi::NestingNester's constructor 0x342E0 writes only SEVEN fields, while the archive's dossier records 132 offsets across
the class's methods. **The constructor gives a class's own storage; its methods give the rest**, and both are the same measurement, so this
runs over any set of functions.

    python g_class_fields.py --class Multi::NestingNester [--widths] [--json re/class_fields.json]
    python g_class_fields.py --functions 0x342E0 0x33100 --json out.json
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

STORE = re.compile(r"^(byte|word|dword|qword) ptr \[(\w+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\], (.+)$")
LOADS_FROM_RCX = re.compile(r"^rcx(?:d|w|b)?$")


def fields_of(function, profile):
    """[(offset, width, address, instruction)] for stores into an object the function received in rcx.

    THE RULE, AND WHY IT IS STRICTER THAN IT LOOKS. A register holds the object from `mov reg, rcx` until it is REASSIGNED, so a store
    through it after a reassignment is a store into something else. Multi::NestingNester's constructor sets rbx once (0x342EC) and pops it at
    the end, so all seven of its offsets are the object's; 0x33100 sets rbp from rcx at 0x3311F and then REASSIGNS it from a return value at
    0x3392B, so the stores through rbp after that point are not fields. **A first version ignored the reassignment and reported offsets for
    a register whose value had been replaced**, which is the same failure as counting values where addresses are needed: the right
    measurement over the wrong object.
    """
    size = (profile.get(function) or {}).get("size") or 0
    if not size:
        return []
    body = [i for i in disasm(function) if i.address < function + size]

    holds = {"rcx"}
    dropped = {}
    out = []
    for instruction in body:
        text = instruction.op_str
        match = STORE.match(text)
        if match:
            width, base, offset, _value = match.group(1), match.group(2), match.group(3), match.group(4)
            if base in holds:
                out.append((int(offset, 16) if offset else 0, width, instruction.address,
                            "%s %s" % (instruction.mnemonic, text)))
            continue
        copy = re.match(r"^(\w+), (\w+)$", text)
        if instruction.mnemonic == "mov" and copy:
            destination, source = copy.group(1), copy.group(2)
            if source in holds:
                holds.add(destination)
            elif destination in holds:
                holds.discard(destination)
                dropped[destination] = instruction.address
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner")
    parser.add_argument("--functions", nargs="*", default=[])
    parser.add_argument("--json")
    parser.add_argument("--widths", action="store_true")
    args = parser.parse_args(argv)

    profile = load_prof()
    functions = [int(value, 16) for value in args.functions]

    if args.owner:
        data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
        for mangled, entry in data.items():
            if (entry.get("demangled") or "").strip() != args.owner:
                continue
            base = int(entry["vtable_rva"])
            # the slots are VALUES, so they are code addresses to read; the address point is base+0x10 (see g_find_ctors.py)
            for index, value in enumerate(entry.get("slots") or []):
                functions.append(int(value))
            # and the constructor candidate: a function referencing slot 0's ADDRESS. Found by scanning, since the tool that does it is
            # g_find_ctors.py and duplicating it here would be a second implementation of one rule.
            from lib import rip_targets
            slot0 = base + 0x10
            for address, info in profile.items():
                if info.get("size") and slot0 in rip_targets(address):
                    functions.append(address)
            break

    functions = sorted(set(functions))
    if not functions:
        print("no functions to scan; pass --class or --functions")
        return 2

    per_function = {}
    all_offsets = collections.Counter()
    for function in functions:
        found = fields_of(function, profile)
        if found:
            per_function[function] = found
            for offset, _width, _address, _text in found:
                all_offsets[offset] += 1

    print("functions scanned: %d; of those, %d write a field" % (len(functions), len(per_function)))
    print("distinct field offsets: %d" % len(all_offsets))
    print("")
    if args.widths:
        widths = collections.Counter()
        for rows in per_function.values():
            for _offset, width, _address, _text in rows:
                widths[width] += 1
        print("by width: %s" % dict(widths))
        print("")
    for function in sorted(per_function):
        rows = per_function[function]
        offsets = sorted(set(offset for offset, _w, _a, _t in rows))
        print("0x%-8X %4d bytes, %3d stores, %3d distinct offsets: %s"
              % (function, (profile.get(function) or {}).get("size") or 0, len(rows), len(offsets),
                 " ".join("+0x%X" % o for o in offsets[:10]) + (" ..." if len(offsets) > 10 else "")))

    if args.json:
        payload = {"class": args.owner,
                   "functions": {("0x%X" % f): [{"offset": o, "width": w, "address": ("0x%X" % a), "instruction": t}
                                                for o, w, a, t in rows] for f, rows in sorted(per_function.items())},
                   "distinct_offsets": {"0x%X" % o: n for o, n in sorted(all_offsets.items())}}
        io.open(args.json, "w", encoding="utf-8", newline="\n").write(json.dumps(payload, indent=1, sort_keys=True))
        print("")
        print("wrote %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
