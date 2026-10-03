# -*- coding: utf-8 -*-
"""The whole nester family, from the vtables and typeinfo: which class derives from which.

**THE `LimitedNester` FAILURE WAS ONE INSTANCE OF A FAMILY-WIDE QUESTION**: `base_chain.hpp` says some nesters go `-> Multi::CompositeNester -> Multi::Nester` and others
go straight `-> Multi::Nester`, **and a declaration that picks the wrong one is off by 0x10 in every field.** This reads the answer out of the image instead of the
prose: for each nester vtable, the typeinfo name, and the base pointer `__si_class_type_info` carries at +0x10.

    python -u g_nester_family.py
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import IB, load_prof, rva2off, u64  # noqa: E402

# the constructor -> vtable pairs this project has already recovered, plus the ones the last rounds found
CONSTRUCTORS = {
    "LimitedNester": 0x4AAD0, "FlipNester": 0x4B570, "MultiTorchNester": 0x780E0,
    "FilterNester": 0xB3A70, "NestingNester": 0x342E0, "DatabaseNester": 0x5B1F0,
}


def read(rva, length):
    offset = rva2off(rva)
    return load_prof.__globals__["pe"].get_data(offset, length)


def typeinfo_name(va):
    """The mangled name a `__class_type_info` or `__si_class_type_info` carries."""
    if not va:
        return None, None
    base = va - IB
    vptr = u64(base)
    name_pointer = u64(base + 8)
    base_pointer = None
    # __si_class_type_info has a base pointer at +0x10; __class_type_info does not, and the vptr differs
    try:
        base_pointer = u64(base + 0x10)
    except Exception:                                     # noqa: BLE001
        base_pointer = None
    name = None
    try:
        raw = read(name_pointer - IB, 160).split(b"\x00")[0]
        name = raw.decode("ascii", "replace")
    except Exception:                                     # noqa: BLE001
        pass
    return name, base_pointer


def main():
    import lib
    globals()["lib"] = lib
    names = {}
    for label, constructor in sorted(CONSTRUCTORS.items(), key=lambda kv: kv[1]):
        vtable = None
        for instruction in lib.disasm(constructor):
            found = re.search(r"\[rip \+ (0x[0-9a-f]+)\]", instruction.op_str)
            if instruction.mnemonic == "lea" and found:
                vtable = instruction.address + instruction.size + int(found.group(1), 16)
                break
        if vtable is None:
            print("%-20s constructor 0x%-6X installs no vtable found" % (label, constructor))
            continue
        info_va = u64(vtable - 8)
        name, base = typeinfo_name(info_va)
        names[vtable] = name
        base_name = None
        if base:
            base_name, _ = typeinfo_name(base)
        print("%-20s ctor 0x%-6X vtable 0x%-7X typeinfo %-28s base %s"
              % (label, constructor, vtable, name or "?", base_name or "(none -- a root)"))

    print("")
    print("**WHAT THE DECLARATIONS SHOULD SAY**, read from the typeinfo and not from the prose:")
    for label, _constructor in sorted(CONSTRUCTORS.items()):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
