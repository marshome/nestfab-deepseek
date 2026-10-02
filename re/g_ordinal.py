# -*- coding: utf-8 -*-
"""Resolve an IDA-style `liblcns_NN` label to this module's export at that ordinal.

Usage: python g_ordinal.py 52         -> one ordinal
       python g_ordinal.py --list     -> every ordinal with its rva, name and size

Why this matters, and it corrected a wrong conclusion the same round it arrived. A disassembler labelling a DLL that exports by
ORDINAL and names nothing shows each entry as `<dllname>_<ordinal>`, so `liblcns_52` is this module's ordinal 52 and not an
imported symbol. This project's `re/exports_table.json` already carries the mapping rva <-> ordinal pair <-> recovered name, so
the label was never opaque -- it was an index into a table that was sitting in the repository, and a round was spent treating
`0x63F228` as an unknown import for want of the lookup.

The module has 168 entries and 336 ordinals: every entry owns a PAIR, so ordinal 52 and ordinal 51 are the same function, which
is why the table records `[51, 52]` rather than one number. That is a property worth stating because it means a label can be off
by one and still name the right entry.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import load_prof  # noqa: E402


def table():
    return json.loads(open(os.path.join(HERE, "exports_table.json"), encoding="utf-8").read())


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("ordinal", nargs="?", type=int, default=None)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--dll", default="liblcns")
    args = parser.parse_args(argv)
    profile = load_prof()
    rows = table()

    if args.list or args.ordinal is None:
        print("%-14s %-10s %-9s %-8s %s" % ("ida label", "ordinals", "rva", "bytes", "recovered name"))
        for entry in that_are_sorted(rows):
            ordinals = entry.get("ords") or []
            label = "%s_%d" % (args.dll, ordinals[0]) if ordinals else "?"
            size = (profile.get(entry["rva"]) or {}).get("size") or 0
            print("%-14s %-10s 0x%-7X %-8d %s"
                  % (label, ",".join(str(o) for o in ordinals), entry["rva"], size, entry.get("name") or "(no label)"))
        return 0

    for entry in rows:
        ordinals = entry.get("ords") or []
        if args.ordinal in ordinals:
            size = (profile.get(entry["rva"]) or {}).get("size") or 0
            print("%s_%d is ordinal pair [%s] of this module" % (args.dll, args.ordinal, ", ".join(str(o) for o in ordinals)))
            print("    rva  0x%X" % entry["rva"])
            print("    size %d bytes" % size)
            print("    name %s" % (entry.get("name") or "(no recovered label)"))
            callees = [c for c in (profile.get(entry["rva"]) or {}).get("callees") or [] if c in profile]
            print("    calls %d functions" % len(callees))
            return 0
    print("%s_%d does not name an export of this module" % (args.dll, args.ordinal))
    return 2


def that_are_sorted(rows):
    return sorted(rows, key=lambda e: (e.get("ords") or [0])[0])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
