# -*- coding: utf-8 -*-
"""Read a class's BASE CLASS NAMES out of the module's own RTTI typeinfo structures.

**THIS IS THE ORACLE FOR A BASE CLASS WHOSE NAME IS NOT A KEY IN re/vtables.json.** The JSON was built from the vtable symbols, and an ABSTRACT base
has no instantiated vtable to key on -- which is exactly why `Nester` has no entry and why its fields are not declared here. But each derived class's
typeinfo holds a pointer to its base's typeinfo, and that base's name is a string in the module.

    gcc's layouts, from the Itanium C++ ABI, in a 64 bit PE:
        __class_type_info          { vptr, name* }
        __si_class_type_info       { vptr, name*, base* }              -- SINGLE INHERITANCE
        __vmi_class_type_info      { vptr, name*, flags, count, bases[] }

so for a single-inheritance derived class the base's name is the string at `[[typeinfo + 0x10] + 8]`.

    python -u g_base_names.py --class NoFillNester
"""
import argparse
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib  # noqa: E402

IMAGE_BASE = 0x6B4C0000


def read_c_string(rva, limit=256):
    offset = lib.rva2off(rva)
    end = lib.data.index(b"\x00", offset)
    return lib.data[offset:min(end, offset + limit)].decode("utf-8", "replace")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner", required=True)
    parser.add_argument("--depth", type=int, default=4)
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

    # the vtable holds NULL, the typeinfo pointer, then the slots -- so the typeinfo is the second word
    base = entry["vtable_rva"]
    typeinfo = struct.unpack_from("<Q", lib.data, lib.rva2off(base) + 8)[0] - IMAGE_BASE
    print("%s: vtable 0x%X, typeinfo 0x%X" % (args.owner, base, typeinfo))

    current = typeinfo
    for step in range(args.depth):
        name = read_c_string(struct.unpack_from("<Q", lib.data, lib.rva2off(current) + 8)[0] - IMAGE_BASE)
        print("   %sname at 0x%X: %s" % ("  " * step, current, name))
        # a single-inheritance typeinfo carries the base at +0x10
        pointer = struct.unpack_from("<Q", lib.data, lib.rva2off(current) + 0x10)[0]
        if pointer == 0:
            print("   %sno base recorded -- the chain ends here" % ("  " * step))
            break
        current = pointer - IMAGE_BASE
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
