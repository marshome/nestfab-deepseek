#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Read a vtable's typeinfo name from a table BASE, with the two rules that a first attempt gets wrong.

**RULE ONE: A CONSTRUCTOR STORES `base + 0x10`, SO A STORED ADDRESS IS NOT A TABLE BASE.** `[base]` holds NULL, `[base + 8]` the typeinfo pointer, and `slots[0]`
is at `base + 0x10`. **Reading a stored address as a base is the mistake that produced two false readings earlier in this project**, so `--stored` is given a
stored address and subtracts 0x10, while `--base` is given a base directly.

**RULE TWO: `lib.u64` TAKES AN RVA AND THIS IMAGE'S BASE IS NOT ZERO.** A table at virtual 0xA3BCE0 is at RVA 0x387CE0 for `lib.IB` = 0x6B4C0000. Passing the
virtual address reads past the image and returns garbage -- which is exactly what the first version of this probe did.

**AND IT REPORTS WHAT IT COULD NOT READ RATHER THAN A GUESS**, because a name invented from a failed read is worse than no name.

    python -u g_vtable_name.py --stored 0xA3BCF0
    python -u g_vtable_name.py --base 0xA3B4D0
"""
import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib  # noqa: E402

IMAGE_SIZE = 0xB43000


def name_at(typeinfo_rva):
    """The Itanium typeinfo name: `{vptr, name*}` at the typeinfo, and the name is a NUL-terminated string after a 16 byte header."""
    if not (0 < typeinfo_rva < IMAGE_SIZE):
        return None
    name_rva = lib.u64(typeinfo_rva + 8)
    if not (0 < name_rva < IMAGE_SIZE):
        return None
    offset = lib.rva2off(name_rva)
    if offset is None:
        return None
    raw = lib.pe.get_data(offset, 400)
    return raw.split(b"\x00", 1)[0].decode("utf-8", "replace")


def as_rva(stored_word):
    """**A WORD STORED IN A TABLE IS A VIRTUAL ADDRESS.** The loader writes absolute pointers after relocation, so a slot holds `IB + rva` and the image base
    comes off before the value can be read or looked up. Returning None keeps "not a pointer" distinct from "points at zero"."""
    if stored_word == 0:
        return 0
    if lib.IB <= stored_word < lib.IB + IMAGE_SIZE:
        return stored_word - lib.IB
    if 0 < stored_word < IMAGE_SIZE:
        return stored_word                     # already an RVA, which some tables hold before relocation
    return None


def describe(base_rva, recorded):
    if not (0 < base_rva < IMAGE_SIZE):
        return "0x%X is not an RVA in this image" % base_rva
    try:
        first = lib.u64(base_rva)
        raw_typeinfo = lib.u64(base_rva + 8)
    except Exception as problem:                                   # noqa: BLE001 -- report, do not crash
        return "unreadable: %s" % problem
    lines = ["base 0x%X (rva 0x%X)" % (base_rva + lib.IB, base_rva),
             "   [base + 0x00] = 0x%X  %s" % (first, "NULL, as a base must be" if first == 0 else "**NOT NULL**")]
    if not raw_typeinfo:
        lines.append("   [base + 0x08] = 0")
        return "\n".join(lines)
    typeinfo_rva = as_rva(raw_typeinfo)
    if typeinfo_rva is None:
        lines.append("   [base + 0x08] = 0x%X, which is neither an RVA nor a virtual address in this image" % raw_typeinfo)
        return "\n".join(lines)
    name = name_at(typeinfo_rva)
    lines.append("   [base + 0x08] = 0x%X (rva 0x%X)  ->  %s"
                 % (raw_typeinfo, typeinfo_rva, name if name else "(the typeinfo did not resolve)"))
    slots = []
    for index in range(48):
        try:
            word = lib.u64(base_rva + 0x10 + index * 8)
        except Exception:                                          # noqa: BLE001
            break
        rva = as_rva(word)
        if rva is None:
            break
        slots.append(rva)
    lines.append("   %d slot(s): %s" % (len(slots), ", ".join("0x%X" % word for word in slots[:8])))
    known = recorded.get(base_rva + lib.IB)
    lines.append("   recorded in re/vtables.json as: %s" % (", ".join(known) if known else "NOT RECORDED"))
    return "\n".join(lines)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--stored", dest="stored")
    parser.add_argument("--base", dest="base")
    parser.add_argument("--many", dest="many", help="comma-separated stored addresses")
    args = parser.parse_args(argv)

    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    recorded = {}
    for value in data.values():
        if value.get("demangled"):
            recorded.setdefault(value["vtable_rva"] + lib.IB, []).append(value["demangled"])

    targets = []
    if args.many:
        targets = [int(part, 0) for part in args.many.split(",")]
    elif args.stored:
        targets = [int(args.stored, 0)]
    elif args.base:
        print(describe(int(args.base, 0) - lib.IB, recorded))
        return 0
    else:
        parser.error("give --stored, --base or --many")

    # **THE ADDRESSES IN THIS PROJECT'S NOTES ARE RVAs AND NOT VIRTUAL ADDRESSES.** `re/vtables.json` records `vtable_rva`, the tools print `0xA3B4E0` for a
    # stored pointer, and `lib.u64` reads at an RVA -- so `--stored` takes an RVA and subtracts only the 0x10. The first version subtracted `lib.IB` as well and
    # every target came out negative.
    for stored in targets:
        print(describe(stored - 0x10, recorded))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
