#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Find a class's real constructor by the displacement of the `lea` that produces ITS vtable POINTER.

THE CORRECTION THIS MAKES, and it took three attempts to get here:

  1. "a function that references the vtable's slot-0 ADDRESS" -- true of a destructor as well, which is how a class got paired with its destructor.
  2. "the candidate that writes the most fields" -- `Engine::InfiniteEngine` was paired with 0x24FD0, **which is another class's constructor**:
     it allocates a 0x30 byte object and a 0x18 byte object and stores them at its own +0 and +8.
  3. **THE VTABLE POINTER IS THE VALUE STORED INTO [object+0]**, and for `Engine::InfiniteEngine` that value is 0xA3CFE0 -- which
     `re/vtables.json` records as `vtable_rva` 0xA3CFD0, sixteen bytes earlier than the pointer the code installs. **So the JSON's field is the
     vtable BASE and the code installs base+0x10, and a search for the base finds nothing.**

THIS SEARCHES FOR THE INSTRUCTION: an `lea reg, [rip + disp]` whose target is the vtable pointer this class installs, followed by a store of
that register into `[object + 0]`. **That sequence IS a constructor's first act**, and the function containing it is the constructor.

    python -u g_find_ctor_by_vtable_store.py --class Engine::InfiniteEngine
"""
import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

STORE = re.compile(r"^qword ptr \[(\w+)(?: \+ (0x[0-9a-f]+))?\], (\w+)$")


def find(class_name, profile, data):
    entry = None
    for _mangled, value in data.items():
        if (value.get("demangled") or "").strip() == class_name:
            entry = value
            break
    if entry is None:
        print("no RTTI entry for %s" % class_name)
        return 2

    base = int(entry["vtable_rva"])
    # THE POINTER THE CODE INSTALLS. The dump at 0xA3CFD0 shows a NULL at +0, the typeinfo at +8 and the first slot at +0x10, so the pointer a
    # constructor stores is base + 0x10.
    installed = base + 0x10
    print("%s" % class_name)
    print("   vtable BASE 0x%X (what re/vtables.json records)" % base)
    print("   vtable POINTER the code installs: 0x%X = base + 0x10" % installed)
    print("")
    print("functions containing an instruction that stores 0x%X into [object + 0]:" % installed)
    hits = []
    for address, info in profile.items():
        if not info.get("size"):
            continue
        loaded = set()
        for instruction in disasm(address):
            if instruction.address >= address + info["size"]:
                break
            # `lea reg, [rip + d]` -- lib's disasm resolves nothing itself, so the target is computed from the operands
            if instruction.mnemonic == "lea":
                for operand in instruction.operands:
                    if operand.type == 3 and operand.mem.base == 41:
                        target = instruction.address + instruction.size + operand.mem.disp
                        if target == installed:
                            loaded.add(instruction.op_str.split(",")[0].strip())
            match = STORE.match(instruction.op_str)
            if match and match.group(3) in loaded and (match.group(2) is None or int(match.group(2), 16) == 0):
                hits.append((address, instruction.address, info["size"]))
                loaded.clear()
    if not hits:
        print("   NONE. **So no function in the profile installs this class's vtable**, which means its constructor is not in the profile, or it")
        print("   was inlined into a caller, or the pointer it installs is not base+0x10 for this class.")
        return 1
    for function, site, size in hits:
        callers = len(set((profile.get(function) or {}).get("callers") or []))
        print("   0x%-8X at 0x%-8X  %d bytes, %d callers" % (function, site, size, callers))
    return 0


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner", required=True)
    args = parser.parse_args(argv)
    profile = load_prof()
    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    return find(args.owner, profile, data)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
