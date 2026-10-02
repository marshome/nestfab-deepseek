#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Report every derived class's vtable address, slot count and slot addresses, for one base.

**THE ADDRESSES ARE THE POINT.** `re/vtables.json` keys a class by its `vtable_rva`, and the RTTI region of this module has MANY adjacent tables: the
dump at 0xA3D370 is `Tiling::MultiOrientedPartPattern` with EIGHT slots while 0xA3D310 is a DIFFERENT class -- **and I once read the second and
reported a slot-count discrepancy about the first.** So the address a class's vtable starts at belongs beside the class, and this prints it.

    python -u g_class_tables.py --base N6Tiling9EvaluatorE
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
from lib import load_prof  # noqa: E402

IMAGE_BASE = 0x6B4C0000


def read_name(rva):
    try:
        offset = lib.rva2off(rva)
        end = lib.data.index(b"\x00", offset)
        return lib.data[offset:min(end, offset + 256)].decode("ascii", "replace")
    except Exception:
        return None


def base_of(entry):
    pointer = struct.unpack_from("<Q", lib.data, lib.rva2off(entry["vtable_rva"]) + 8)[0]
    if pointer == 0:
        return None
    following = struct.unpack_from("<Q", lib.data, lib.rva2off(pointer - IMAGE_BASE) + 0x10)[0]
    if following == 0:
        return None
    return read_name(struct.unpack_from("<Q", lib.data, lib.rva2off(following - IMAGE_BASE) + 8)[0] - IMAGE_BASE)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", dest="base", required=True)
    args = parser.parse_args(argv)

    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    profile = load_prof()
    print("%-34s %-10s %-6s %s" % ("class", "vtable", "slots", "slot addresses (the first four)"))
    for _mangled, entry in sorted(data.items(), key=lambda kv: kv[1]["vtable_rva"]):
        name = (entry.get("demangled") or "").strip()
        if any(part in name for part in ("std::", "boost::", "CryptoPP", "__", "<subst>")):
            continue
        if base_of(entry) != args.base:
            continue
        slots = entry.get("slots") or []
        sizes = []
        for address in slots[:4]:
            size = (profile.get(address) or {}).get("size")
            sizes.append("0x%X(%s)" % (address, size if size else "?"))
        print("%-34s 0x%-8X %-6d %s" % (name[:34], entry["vtable_rva"], len(slots), " ".join(sizes)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
