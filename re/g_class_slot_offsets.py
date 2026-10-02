#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""What each of a class's MODULE SLOTS reads and writes ON THE OBJECT, with the object register properly established.

**THE METHOD-SIDE COMPANION TO re/g_members_without_instructions.py, AND IT APPLIES THE SAME RULE.** An offset is evidence only if the base register
was loaded from rcx (the object) and not reassigned since -- **a scan that accepts five registers at once cannot tell an argument from an
instance**, which is the mistake that produced two false readings in this project: `MultiOrientedPartPattern` slot 3 "reading [this + 0x10]" (it was
`lea rbx, [r12 + 8]` with r12 = rdx, the second argument) and `BestObserver` slot 4 "writing +0x10 through +0x60" (it writes none of them).

    python -u g_class_slot_offsets.py --class NoFillNester
    python -u g_class_slot_offsets.py --all --max-slots 6
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

ACCESS = re.compile(r"\[(\w+)(?: \+ (0x[0-9a-f]+))?\]")
STORE = re.compile(r"^(byte|word|dword|qword) ptr \[(\w+)(?: \+ (0x[0-9a-f]+))?\", ")
STORE = re.compile(r"^(?:byte|word|dword|qword) ptr \[(\w+)(?: \+ (0x[0-9a-f]+))?\], ")


def slot_offsets(function, profile):
    """(reads, writes) of the OBJECT, with `this` established from rcx and tracked until it is reassigned.

    **A LIMIT THAT MUST BE STATED RATHER THAN HIDDEN.** `this` is followed into whatever register it is copied to -- `0x7F266 mov rbp, rcx` in
    `NoFillNester`'s slot 5 makes rbp the object -- and once it is there, EVERY store through that register is counted. In an 8440 byte routine with
    a 0x508 byte frame that means the count includes stores that are not fields of `this` at all: 40 offsets are reported for that slot, and the
    routine takes its remaining arguments on the stack (`mov r15, [rsp + 0x578]`), so some of those offsets belong to a parameter block.

    **SO THE OUTPUT IS A CANDIDATE LIST AND NOT A FIELD LIST.** It is a reliable way to find which slots touch the OBJECT at all -- a slot that
    writes nothing here touches no field, and that is a sound negative -- and a starting point for reading a specific slot, not a substitute for it.
    The alternative, deciding from the assembly which stores are field writes, is what reading the routine is.
    """
    size = (profile.get(function) or {}).get("size") or 0
    if not size:
        return set(), set()
    holds = {"rcx"}
    reads, writes = set(), set()
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        text = instruction.op_str
        store = STORE.match(text)
        if store and store.group(1) in holds:
            writes.add(int(store.group(2), 16) if store.group(2) else 0)
        for found in ACCESS.finditer(text):
            if found.group(1) in holds and found.group(2):
                reads.add(int(found.group(2), 16))
        copy = re.match(r"^(\w+), (\w+)$", text)
        if instruction.mnemonic == "mov" and copy:
            destination, source = copy.group(1), copy.group(2)
            if source in holds:
                holds.add(destination)
            elif destination in holds:
                holds.discard(destination)
    return reads - writes, writes


def report(class_name, profile, data):
    entry = None
    for _mangled, value in data.items():
        if (value.get("demangled") or "").strip().split("::")[-1] == class_name:
            entry = value
            break
    if entry is None:
        print("%-30s no RTTI entry" % class_name)
        return
    slots = entry.get("slots") or []
    print("%s   vtable 0x%X, %d slots" % (entry.get("demangled"), entry["vtable_rva"], len(slots)))
    printed = 0
    for index, address in enumerate(slots):
        if index < 2:
            continue          # the destructor pair, established for every class in this family
        reads, writes = slot_offsets(address, profile)
        size = (profile.get(address) or {}).get("size") or 0
        print("    slot %d  0x%-8X %5d bytes  reads %-28s writes %s"
              % (index, address, size,
                 " ".join("+0x%X" % o for o in sorted(reads)[:6]) or "-- none --",
                 " ".join("+0x%X" % o for o in sorted(writes)[:6]) or "-- none --"))
        printed += 1
    if not printed:
        print("    -- no slot beyond the destructor pair --")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--max-slots", type=int, default=6)
    args = parser.parse_args(argv)

    profile = load_prof()
    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())

    if args.owner:
        names = [args.owner]
    elif args.all:
        names = []
        for path in sorted(glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "*.hpp"))):
            text = io.open(path, encoding="utf-8", errors="replace").read()
            names += re.findall(r"^class (\w+)", text, re.M)
        names = [n for n in names if any((v.get("demangled") or "").split("::")[-1] == n for v in data.values())]
    else:
        parser.error("give --class or --all")

    for name in names:
        report(name, profile, data)
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
