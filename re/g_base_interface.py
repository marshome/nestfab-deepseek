#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Read an ABSTRACT BASE's interface from the sibling that does have a vtable.

**AN ABSTRACT BASE HAS NO INSTANTIATED VTABLE, SO re/vtables.json CANNOT DESCRIBE IT** -- which is why the whole base layer went unnoticed. But a
base's surface is still in the module twice over:

  * its DERIVED classes' vtables, whose first slots are the base's own methods where the derived class does not override them; and
  * its SIBLINGS' vtables, where a sibling that DOES get instantiated shows the same slots.

So this reports, for a base class's derived classes, the slots they SHARE -- a slot whose address is the same in several derived tables is the base's
implementation, and a slot that differs is the derived class's own. **WHICH IS THE SAME PRINCIPLE AS THE BASE CHAIN ITSELF: the answer is in what the
module has, not in what a shape suggests.**

    python -u g_base_interface.py --base Tiling::Evaluator
    python -u g_base_interface.py --base Engine::Engine
"""
import argparse
import collections
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib  # noqa: E402
from lib import disasm, load_prof  # noqa: E402

IMAGE_BASE = 0x6B4C0000


def read_name(rva):
    try:
        offset = lib.rva2off(rva)
        end = lib.data.index(b"\x00", offset)
        return lib.data[offset:min(end, offset + 256)].decode("ascii", "replace")
    except Exception:
        return None


def base_of(entry):
    """The mangled name of the class's base, from its typeinfo."""
    pointer = struct.unpack_from("<Q", lib.data, lib.rva2off(entry["vtable_rva"]) + 8)[0]
    if pointer == 0:
        return None
    typeinfo = pointer - IMAGE_BASE
    following = struct.unpack_from("<Q", lib.data, lib.rva2off(typeinfo) + 0x10)[0]
    if following == 0:
        return None
    return read_name(struct.unpack_from("<Q", lib.data, lib.rva2off(following - IMAGE_BASE) + 8)[0] - IMAGE_BASE)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", dest="base", required=True)
    args = parser.parse_args(argv)

    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    derived = []
    for _mangled, entry in data.items():
        name = (entry.get("demangled") or "").strip()
        if any(part in name for part in ("std::", "boost::", "CryptoPP", "__", "<subst>")):
            continue
        if base_of(entry) == args.base:
            derived.append((name, entry))
    if not derived:
        print("no class in re/vtables.json derives from %s" % args.base)
        return 0

    print("%s has %d instantiated derived class(es):" % (args.base, len(derived)))
    for name, _entry in derived:
        print("   %s" % name)
    print("")

    # a slot address shared by several derived tables is the BASE's own implementation
    counts = collections.Counter()
    tables = {}
    for name, entry in derived:
        slots = entry.get("slots") or []
        tables[name] = slots
        for address in set(slots):
            counts[address] += 1
    width = max(len(entry.get("slots") or []) for _name, entry in derived)
    profile = load_prof()
    print("slot-by-slot, over %d slots:" % width)
    for index in range(width):
        column = {name: (tables[name][index] if index < len(tables[name]) else None) for name, _e in derived}
        seen = collections.Counter(column.values())
        address, shared = seen.most_common(1)[0]
        size = (profile.get(address) or {}).get("size") if address else None
        mark = "SHARED by %d" % shared if shared > 1 else "own"
        print("   slot %-2d  %-28s %-10s %s" % (
            index,
            ("0x%X (%s bytes)" % (address, size)) if address else "--- abstract ---",
            mark,
            ", ".join("%s=%s" % (name.split("::")[-1], "0x%X" % value if value else "--") for name, value in column.items())[:96]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
