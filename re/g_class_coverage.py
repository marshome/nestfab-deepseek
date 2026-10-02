#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Which of the module's 96 classes have a C++ definition, and which have only a row in a generated table?

The human's point is that many classes need doing, and the answer has to be measured rather than guessed. A class counts as DEFINED when its
name appears in a hand-written header under lcns/include/lcns -- not in classes.hpp or virtual_methods.hpp, which are generated tables of
RTTI rows and are not definitions.

    python g_class_coverage.py [--todo]

  * the class, its namespace, its vtable, its slot count;
  * whether a hand-written header mentions it;
  * whether a TEST mentions it, which check_recovery requires for anything declared.

A class that is only a row in classes.hpp has an address and nothing else, and this reports how many there are and where they cluster.
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

GENERATED = {"classes.hpp", "virtual_methods.hpp", "parameter_report.hpp", "option_keys.hpp", "miplib_names.hpp"}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--todo", action="store_true")
    args = parser.parse_args(argv)

    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    FOREIGN = ("N8CryptoPP", "N5boost", "N6Json", "N9__gnu_cxx", "NSt7__cxx11", "N10__cxxabiv1", "N6Locale", "NSt6locale",
               "N5Clp", "N4Coin", "N8CoinUtils", "N3Osi", "N3Cbc", "N11CoinPresolve", "N6Ipopt", "N5Ipopt")

    headers = {}
    for path in glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "**", "*.hpp"), recursive=True):
        if os.path.basename(path) in GENERATED:
            continue
        headers[path] = io.open(path, encoding="utf-8", errors="replace").read()
    tests = ""
    for path in glob.glob(os.path.join(ROOT, "lcns", "tests", "*.cpp")):
        tests += io.open(path, encoding="utf-8", errors="replace").read()

    rows = []
    for mangled, entry in data.items():
        if any(mangled.startswith(prefix) for prefix in FOREIGN):
            continue
        qualified = (entry.get("demangled") or "").strip()
        if not qualified:
            continue
        short = qualified.split("::")[-1]
        namespace = qualified.split("::")[0] if "::" in qualified else "(global)"
        # a definition mentions the class as `class X` or `struct X`, in a hand-written header
        defined_in = None
        for path, text in headers.items():
            if re.search(r"\b(?:class|struct)\s+%s\b" % re.escape(short), text):
                defined_in = os.path.basename(path)
                break
        tested = bool(re.search(r"\b%s\b" % re.escape(short), tests))
        rows.append((namespace, short, qualified, entry.get("vtable_rva"),
                     len(entry.get("slots") or []), defined_in, tested))

    total = len(rows)
    defined = [r for r in rows if r[5]]
    tested = [r for r in rows if r[6]]
    print("classes from RTTI: %d" % total)
    print("  mentioned by a hand-written header (class/struct): %d" % len(defined))
    print("  mentioned by a test:                              %d" % len(tested))
    print("")

    by_namespace = {}
    for row in rows:
        namespace = row[0]
        entry = by_namespace.setdefault(namespace, [0, 0])
        entry[0] += 1
        if row[5]:
            entry[1] += 1
    print("%-16s %-7s %-9s" % ("namespace", "classes", "defined"))
    for namespace, (count, done) in sorted(by_namespace.items(), key=lambda kv: -kv[1][0]):
        print("%-16s %-7d %-9d" % (namespace[:16], count, done))
    print("")

    if args.todo:
        print("the classes with NO definition, by slot count:")
        for namespace, short, qualified, vtable, slots, defined_in, was_tested in sorted(rows, key=lambda r: (-r[4], r[2])):
            if defined_in:
                continue
            print("   %-44s vtable 0x%-8X %2d slots" % (qualified[:44], vtable or 0, slots))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
