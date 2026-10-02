#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Report, per class, how much of the MODULE's method surface the C++ has actually declared.

**THE OBJECTIVE'S SECOND HALF.** The members are now supported everywhere, and the methods are not: a class can declare three methods while the
module's vtable has eight, and nothing says so. This counts both sides.

    declared methods   the member functions in the class's own `.hpp` declaration, minus the destructor and the accessors that just return a member
    module slots       the slots re/vtables.json records, minus the destructor pair (slots 0 and 1 in every class of this family)

**AND IT DOES NOT PRETEND TO MAP THEM.** Matching a declared name to a slot would need names the module does not carry -- the RTTI has the class
and the slots have addresses -- so the two counts are printed side by side and the gap is the work. Guessing the correspondence is exactly the
"fix a layout on a shape that matches" this project forbids.

    python -u g_method_coverage.py [--class NAME]
"""
import argparse
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

METHOD = re.compile(r"^\s{4,}(?:virtual\s+)?(?:[\w:<>,\*&\s]+?)\s+(\w+)\s*\([^;{)]*\)\s*(?:const\s*)?(?:override\s*)?[;{]", re.M)
# a method whose body is `{ return member_; }` or `{ member_ = value; }` is an ACCESSOR for a member already placed, and it is not a claim about
# the module's method surface
ACCESSOR = re.compile(r"\{\s*(?:return\s+[\w>\-\.\(\)\s]*;|[\w_]+\s*=\s*[\w]+;|\(void\)[\w]+;)\s*\}")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner")
    args = parser.parse_args(argv)

    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    by_name = {}
    for _mangled, entry in data.items():
        name = (entry.get("demangled") or "").strip()
        if name:
            by_name[name] = entry

    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "*.hpp"))):
        header = os.path.basename(path)
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in re.finditer(r"^class (\w+)[^\{]*\{(?P<body>.*?)^\};", text, re.M | re.S):
            short = match.group(1)
            body = match.group("body")
            instances = [name for name in by_name if name.split("::")[-1] == short]
            if not instances:
                continue
            full = instances[0]
            entry = by_name[full]
            slots = len(entry.get("slots") or [])
            methods = [m.group(1) for m in METHOD.finditer(body)]
            methods = [name for name in methods if name not in ("if", "for", "while", "switch", "return")]
            accessors = len(ACCESSOR.findall(body))
            substantive = len(methods) - accessors
            rows.append((header, short, full, slots - 2, len(methods), accessors, max(0, substantive)))

    if args.owner:
        rows = [r for r in rows if r[1] == args.owner]
    rows.sort(key=lambda r: -(r[3] - r[6]))

    print("%-16s %-28s %-14s %-8s %-9s %s" % ("header", "class", "rtti", "module-2", "declared", "accessors"))
    for header, short, full, surface, declared, accessors, substantive in rows:
        gap = surface - substantive
        print("%-16s %-28s %-14s %-8d %-9d %-9d%s" % (header[:16], short[:28], full.split("::")[0][:14], surface,
                                                       declared, accessors, "   <-- GAP %d" % gap if gap > 0 else ""))
    print("")
    total_gap = sum(max(0, r[3] - r[6]) for r in rows)
    print("classes listed: %d, and the sum of their undeclared module methods: %d" % (len(rows), total_gap))
    print("**THE GAP IS NOT A DEFECT BY ITSELF** -- a method the module has and the port does not need is a decision, and this file does not know")
    print("which. What it does say is where the surface is UNEXPLORED, which is the next reading rather than a guess.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
