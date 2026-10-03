#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""A class's vtable, its destructor pair and the offsets its own functions touch -- so a small class can be written from measurements.

**THE OBJECTIVE'S CORE LOOP, AS A TOOL**: read the table, read the slots beyond the destructor pair, and read what those slots touch ON THE OBJECT. **The rule
that an offset is evidence only if the base register is the object applies here too**, which is why the destructor pair is separated from the rest and the rest
are reported with `rcx` tracked.

    python -u g_class_probe.py --class SplitNode
    python -u g_class_probe.py --class TerminalNode --all-slots
"""
import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[(\w+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]")
STORE = re.compile(r"^(?:byte|word|dword|qword) ptr \[(\w+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\], ")
FREE = 0x9984B0


def touches(function, profile):
    """The offsets read and written ON THE OBJECT, with `this` taken from rcx and followed until reassigned.

    **AND `rcx` IS NOT ALWAYS THE OBJECT, WHICH THE FIRST VERSION GOT WRONG.** `Multi::AllSheetSelector`'s slot 2 at 0x7D2500 begins

        7D250E  mov r12, rcx          ; this
        7D2511  mov qword [rcx], 0    ; and rcx is the DESTINATION this method FILLS
        7D2518  mov rsi, rdx          ; the argument
        7D251E  mov qword [rcx + 8], 0
        7D2526  mov qword [rcx + 0x10], 0

    **so the writes the first version reported at "+0x0" and "+0x10" are the CALLER'S BUFFER and not the object at all.** The object is what a register is
    COPIED OUT OF `rcx` at the top -- here `r12` -- and that is what this follows once it sees one. **It still reports `rcx` when nothing copies it**, because
    for the four node accessors `[rcx + 0x48]` genuinely is the object; the difference is stated per function rather than assumed.
    """
    size = (profile.get(function) or {}).get("size") or 0
    if not size:
        return set(), set()
    holds = {"rcx"}
    # **THE OBJECT REGISTER, ESTABLISHED FIRST.** A `mov <reg>, rcx` before the first store means `rcx` is a destination and `<reg>` is the object.
    for instruction in disasm(function, count=14):
        if instruction.address >= function + size:
            break
        copy = re.match(r"^(\w+), rcx$", instruction.op_str)
        if instruction.mnemonic == "mov" and copy:
            holds.add(copy.group(1))
            if STORE.match(instruction.op_str) is None:
                holds.discard("rcx")
    reads, writes = set(), set()
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        store = STORE.match(instruction.op_str)
        if store and store.group(1) in holds:
            writes.add(int(store.group(2), 16) if store.group(2) else 0)
        for found in ACCESS.finditer(instruction.op_str):
            if found.group(1) in holds and found.group(2):
                reads.add(int(found.group(2), 16))
        copy = re.match(r"^(\w+), (\w+)$", instruction.op_str)
        if instruction.mnemonic == "mov" and copy:
            destination, source = copy.group(1), copy.group(2)
            if source in holds:
                holds.add(destination)
            elif destination in holds:
                holds.discard(destination)
    return reads - writes, writes


def is_free_thunk(function, profile):
    size = (profile.get(function) or {}).get("size") or 0
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        if instruction.mnemonic == "jmp" and instruction.op_str.strip() == "0x%x" % FREE:
            return True
    return False


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner", required=True)
    parser.add_argument("--all-slots", action="store_true", help="include the destructor pair")
    args = parser.parse_args(argv)

    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    entry = None
    for _mangled, value in data.items():
        if (value.get("demangled") or "").strip().split("::")[-1] == args.owner:
            entry = value
            break
    if entry is None:
        print("no RTTI entry for %s" % args.owner)
        return 2

    profile = load_prof()
    slots = entry.get("slots") or []
    print("%s   vtable 0x%X, %d slots" % (entry.get("demangled"), entry["vtable_rva"], len(slots)))
    print("")
    for index, address in enumerate(slots):
        size = (profile.get(address) or {}).get("size")
        if index < 2 and not args.all_slots:
            kind = "the deleting destructor" if index == 0 else "the destructor"
            print("   slot %d  0x%-8X %-6s %s%s" % (index, address, size, kind,
                                                    "  (a tail call to the allocator)" if is_free_thunk(address, profile) else ""))
            continue
        reads, writes = touches(address, profile)
        print("   slot %d  0x%-8X %-6s reads %-24s writes %s"
              % (index, address, size,
                 " ".join("+0x%X" % o for o in sorted(reads)[:5]) or "-- none --",
                 " ".join("+0x%X" % o for o in sorted(writes)[:5]) or "-- none --"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
