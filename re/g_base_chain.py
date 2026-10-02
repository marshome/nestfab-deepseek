#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Read every class's BASE CLASS CHAIN out of the module's own RTTI, and report the ones this project does not declare.

**THE ORACLE FOR AN ABSTRACT BASE.** `re/vtables.json` is keyed on vtable symbols, and an abstract base has no instantiated vtable -- which is why
`Multi::Nester` has no entry there and why the fields of the Nester family's base were undeclared. **But every derived class's typeinfo points at its
base's typeinfo, and the base's name is a string in the module.** In the Itanium C++ ABI a single-inheritance typeinfo is

    __si_class_type_info  { vptr, name*, base* }

so the chain is walked by following +0x10 and reading the name at +8 of each node.

    python -u g_base_chain.py                    every class with RTTI
    python -u g_base_chain.py --class NoFillNester
    python -u g_base_chain.py --out re/base_chains.txt
"""
import argparse
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import lib  # noqa: E402

IMAGE_BASE = 0x6B4C0000


def read_name(rva):
    """The mangled name at a typeinfo, decoded. Returns None when the pointer is not a readable string."""
    try:
        offset = lib.rva2off(rva)
        end = lib.data.index(b"\x00", offset)
        raw = lib.data[offset:min(end, offset + 256)]
    except Exception:
        return None
    return raw.decode("ascii", "replace")


def in_code(rva):
    """Whether an RVA is inside the module's EXECUTABLE sections, where a typeinfo's own vtable lives.

    **THE FIRST VERSION USED A CODE-ONLY RANGE AND REJECTED EVERY TYPEINFO.** For `NoFillNester` the first word of the typeinfo at 0xA18010 is
    0x6BEFAED0, an RVA of 0xA3AED0 -- inside `BAB0` (0x1000..0x725000), which IS where a vtable is, but compared against the FUNCTION profile's
    range it is absent because a typeinfo's vtable is not a function. **The section table is the right oracle**, and `lib.SEC` carries it.
    """
    for _name, virtual, _raw, rawsize, _flags, characteristics in lib.SEC:
        if virtual <= rva < virtual + rawsize and characteristics & 0x20000000:
            return True
    return False


def demangle(name):
    """The project's own Itanium demangler, from re/09_rtti_vtables.py, LOADED rather than reimplemented.

    **A SECOND DEMANGLER WOULD BE A SECOND VERSION OF ONE THING**, which this project checks for, so the existing function is extracted rather than
    copied. It is read out of the file by regex and compiled ALONE, because loading that module would run its top-level report -- 142 KB of vtable
    dump -- and a tool that prints someone else's output cannot be read.
    """
    import re as _re
    path = os.path.join(HERE, "09_rtti_vtables.py")
    try:
        source = io.open(path, encoding="utf-8", errors="replace").read()
        start = source.index("def demangle(")
    except (OSError, ValueError):
        return name
    # the function ends at the first line that starts at column zero after its body
    body = source[start:]
    lines = body.split("\n")
    end = len(lines)
    for index in range(1, len(lines)):
        line = lines[index]
        if line and not line[0].isspace() and not line.startswith(")"):
            end = index
            break
    namespace = {}
    try:
        exec(compile("\n".join(lines[:end]), "demangle", "exec"), namespace)
        return namespace["demangle"](name)
    except Exception:
        return name


def chain_for(entry, depth=6):
    """The typeinfo names from the class up to AND INCLUDING the root class.

    **THE WALK HAS TO RECOGNISE WHERE IT ENDS.** Following +0x10 blindly ran past a ROOT class -- `Nester` has no base -- and turned the next
    unrelated bytes into names, which is where garbage like `SH?? H???J>` came from. A genuine typeinfo's first word points into an executable
    section, so the walk verifies that before reading a name; anything else means the previous node had no base and the chain is over.
    """
    pointer = struct.unpack_from("<Q", lib.data, lib.rva2off(entry["vtable_rva"]) + 8)[0]
    if pointer == 0:
        return []
    typeinfo = pointer - IMAGE_BASE
    names = []
    for _ in range(depth):
        own = struct.unpack_from("<Q", lib.data, lib.rva2off(typeinfo))[0]
        if not in_code(own - IMAGE_BASE):
            break                     # not a typeinfo: the previous node had no base, so the chain ended
        name = read_name(struct.unpack_from("<Q", lib.data, lib.rva2off(typeinfo) + 8)[0] - IMAGE_BASE)
        if name is None or not name.startswith("N"):
            break
        names.append(name)
        following = struct.unpack_from("<Q", lib.data, lib.rva2off(typeinfo) + 0x10)[0]
        if following == 0:
            break
        typeinfo = following - IMAGE_BASE
    return names


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner")
    parser.add_argument("--out", dest="out")
    args = parser.parse_args(argv)

    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    declared = set()
    for path in os.listdir(os.path.join(ROOT, "lcns", "include", "lcns")):
        if path.endswith(".hpp"):
            text = io.open(os.path.join(ROOT, "lcns", "include", "lcns", path), encoding="utf-8", errors="replace").read()
            declared |= set(json.loads(json.dumps(__import__("re").findall(r"^class (\w+)", text, __import__("re").M))))

    lines = []
    undeclared_bases = {}
    for _mangled, entry in sorted(data.items(), key=lambda kv: (kv[1].get("demangled") or "")):
        name = (entry.get("demangled") or "").strip()
        short = name.split("::")[-1]
        if args.owner and short != args.owner:
            continue
        # skip the standard library's own hierarchies: they are not this project's to declare
        if any(part in name for part in ("std::", "boost::", "CryptoPP", "__cxxabiv1", "__gnu", "<subst>")):
            continue
        names = chain_for(entry)
        readables = [demangle(item) for item in names[1:]]
        lines.append("%-46s %s" % (name[:46], "  <-  ".join(readables) or "(no base)"))

    if args.out:
        io.open(args.out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
        print("wrote %s with %d class(es)" % (args.out, len(lines)))
        return 0

    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
