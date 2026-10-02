#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""What the audit CANNOT see: members whose NAME and TYPE no instruction supports.

The full audit catches SHAPES -- `at_0020`, a stack store cited as a field, a placeholder class. **It cannot catch a member called `ratio_` whose
instruction does not exist**, because there is nothing to compare against: the member was never placed by anything.

This checks the other direction. For every hand-written class, it asks whether the class's RECOVERED CONSTRUCTOR actually writes the members the
class declares:

    FilterNester   rng_ at +0x20 and index at +0x9E0 -- RE 0xB3AB0 and 0xB3AC1 write both.  SUPPORTED
    FlipNester     record_, compare_ at +0x20 and +0x21 -- RE 0x4B59B and 0x4B5AE write both.   SUPPORTED
    LimitedNester  maxParts_, maxAngles_ -- WHICH INSTRUCTION WRITES +0x08 AND +0x0C? If none, they are a guess.

    python g_members_without_instructions.py [--class LimitedNester]
"""
import argparse
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

STORE = re.compile(r"^(byte|word|dword|qword) ptr \[(\w+)(?: \+ (0x[0-9a-f]+))?\], ")
MEMBER = re.compile(r"^ {4,}([\w:<>,\s\*&]+?)\s+(\w+)\s*(?:=\s*[^;]*)?;", re.M)


def written_offsets(function, profile):
    """The offsets one function writes through a base register loaded from rcx, with that register's own evidence."""
    size = (profile.get(function) or {}).get("size") or 0
    if not size:
        return set()
    holds = {"rcx"}
    offsets = set()
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        match = STORE.match(instruction.op_str)
        if match:
            base, offset = match.group(2), match.group(3)
            if base in holds and offset:
                offsets.add(int(offset, 16))
            continue
        copy = re.match(r"^(\w+), (\w+)$", instruction.op_str)
        if instruction.mnemonic == "mov" and copy:
            destination, source = copy.group(1), copy.group(2)
            if source in holds:
                holds.add(destination)
            elif destination in holds:
                holds.discard(destination)
    return offsets


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner")
    args = parser.parse_args(argv)

    profile = load_prof()
    data = json.loads(io.open(os.path.join(HERE, "all_class_fields.json"), encoding="utf-8").read())
    by_short = {}
    for entry in data["classes"]:
        if entry.get("constructor"):
            by_short[entry["class"].split("::")[-1]] = int(entry["constructor"], 16)

    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "*.hpp"))):
        name = os.path.basename(path)
        if name in ("exports_impl.hpp", "parameter_report.hpp", "option_keys.hpp", "miplib_names.hpp", "recovery.hpp"):
            continue
        text = io.open(path, encoding="utf-8", errors="replace").read()
        # the hand-written classes in this header, and the members each declares in its private section
        for match in re.finditer(r"^class (\w+)[^\{]*\{(?P<body>.*?)^\};", text, re.M | re.S):
            short = match.group(1)
            if short not in by_short:
                continue
            body = match.group("body")
            members = [(m.group(1).strip(), m.group(2)) for m in MEMBER.finditer(body)]
            if not members:
                continue
            written = written_offsets(by_short[short], profile)
            rows.append((name, short, by_short[short], written, members))

    if args.owner:
        rows = [r for r in rows if r[1] == args.owner]

    print("hand-written classes whose recovered constructor can be checked: %d" % len(rows))
    print("")
    print("%-22s %-18s %-10s %-10s %s" % ("class", "header", "ctor", "writes", "declared members"))
    for name, short, ctor, written, members in rows:
        print("%-22s %-18s 0x%-8X %-10s %s"
              % (short[:22], name[:18], ctor,
                 " ".join("+0x%X" % o for o in sorted(written)[:4]) or "-- none --",
                 ", ".join(m[1] for m in members)[:44]))
    print("")
    print("WHERE `writes` IS EMPTY, the class's members have NO INSTRUCTION BEHIND THEM from that constructor -- **which is the case the full")
    print("audit cannot see**, and the one the human found four times. It does not prove the members wrong; it says no instruction in the")
    print("recovered constructor places them, and that has to be resolved by reading or by removing them.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
