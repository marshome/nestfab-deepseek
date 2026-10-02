#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Every class's constructor and the fields it writes, for the whole module, in one pass.

The two tools are joined here: re/g_find_ctors.py finds a class's constructor by the vtable slot-0 ADDRESS it installs, and
re/g_class_fields.py reads that constructor's stores. Running them one class at a time is what the last two rounds did; this does the
population, because a fact about one class is worth less than a measurement over all of them.

    python g_all_class_fields.py [--limit 25] [--json re/all_class_fields.json]

WHAT A ROW MEANS. `fields` is the number of DISTINCT offsets the class's constructor writes, and `functions` is how many of the class's
functions write any field at all. A class with a constructor and NO field writes is one whose constructor only installs the vtable -- which
is a real shape, not a failure -- and this reports it as 0 rather than omitting the class.
"""
import argparse
import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import load_prof, rip_targets  # noqa: E402
import g_class_fields  # noqa: E402
import g_find_ctors  # noqa: E402


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--json")
    args = parser.parse_args(argv)

    profile = load_prof()
    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    index = g_find_ctors.vtable_index()

    # invert the index: vtable base -> its class
    base_to_class = {}
    for _address, (qualified, _slot, base) in index.items():
        base_to_class[base] = qualified

    # and the reverse lookup the constructor scan needs: slot-0 address -> base
    slot0_to_base = {}
    for address, (qualified, slot, base) in index.items():
        if slot == 0:
            slot0_to_base[address] = base

    # ONE PASS over the profile, collecting every function that references a slot-0 address
    ctors = collections.defaultdict(set)
    for address, info in profile.items():
        if not info.get("size"):
            continue
        for target in rip_targets(address):
            base = slot0_to_base.get(target)
            if base is not None:
                ctors[base].add(address)

    rows = []
    for base, candidates in ctors.items():
        qualified = base_to_class.get(base, "?")
        if qualified.startswith(("CryptoPP", "boost", "std::", "<subst>", "__gnu_cxx", "Json::")):
            continue
        # the constructor is the candidate with the MOST field writes, since the destructor pair writes only the vtable
        best = None
        best_fields = None
        for candidate in sorted(candidates):
            found = g_class_fields.fields_of(candidate, profile)
            offsets = {offset for offset, _w, _a, _t in found}
            if best is None or len(offsets) > len(best_fields):
                best, best_fields = candidate, offsets
        per_function = {c: len({o for o, _w, _a, _t in g_class_fields.fields_of(c, profile)}) for c in candidates}
        rows.append((qualified, base, best, len(best_fields), len(candidates),
                     sum(1 for n in per_function.values() if n > 0)))

    rows.sort(key=lambda row: (-row[3], row[0]))
    print("classes with a constructor candidate: %d" % len(rows))
    print("")
    print("%-40s %-10s %-9s %-7s %-6s %s" % ("class", "constructor", "vtable", "fields", "ctors", "functions with fields"))
    for qualified, base, ctor, fields, candidates, writing in rows[:args.limit]:
        print("%-40s 0x%-8X 0x%-7X %-7d %-6d %d" % (qualified[:40], ctor or 0, base, fields, candidates, writing))
    print("")
    with_fields = [r for r in rows if r[3] > 0]
    print("%d of %d classes have a constructor that writes at least one field; the rest install only the vtable." %
          (len(with_fields), len(rows)))

    if args.json:
        payload = {"classes": [{"class": q, "constructor": "0x%X" % c if c else None, "vtable": "0x%X" % b,
                                "fields": f, "candidates": n, "functions_writing": w}
                               for q, b, c, f, n, w in rows]}
        io.open(args.json, "w", encoding="utf-8", newline="\n").write(json.dumps(payload, indent=1, sort_keys=True))
        print("wrote %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
