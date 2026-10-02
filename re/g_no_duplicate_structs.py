#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A rule with a check: a generated struct must not be a SECOND description of a class that already exists.

WHY THIS EXISTS, and it is the human catching me twice:

    round N    I generated `NestingNesterLayout` beside `class NestingNester : public Nester` in nester.hpp
    round N+7  I generated `LimitedNesterMembers` beside `class LimitedNester : public Nester`, and 22 of 24 of them had a class already

Both times the human asked "what are these two things". **The same mistake twice means the fix is a gate, not a resolution.**

WHAT IT CHECKS, in three parts, because a duplicate can be recognised three ways:

  1. A NAME: a generated struct called `XMembers`, `XLayout`, `XFields` or `XInfo` where a class or struct `X` is declared in another header.
  2. A CLASS LIST: a generated file that declares a struct per RTTI class, which is a table wearing struct syntax.
  3. AN OFFSET SET: a generated struct whose members claim offsets that its own C++ object cannot reproduce. The project MEASURED this for
     NestingNester -- the module writes seedP at 0x18 while the model places it at 0x08 -- so a struct with module offsets and no base that
     accounts for them is a false declaration.

    python g_no_duplicate_structs.py [--list]
"""
import argparse
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INCLUDE = os.path.join(ROOT, "lcns", "include", "lcns")

# GENERATED SUFFIXES that mean "a second description of something that should be a class"
SUFFIXES = ("Members", "Layout", "Fields", "Info", "Record")
# and headers whose whole purpose is to be a registry, which are allowed to be tables
REGISTRY_FILES = {"exports_forwarding.inc", "exports_impl.hpp", "classes.hpp", "virtual_methods.hpp", "recovery.hpp",
                  "parameter_report.hpp", "option_keys.hpp", "miplib_names.hpp", "enums.hpp", "trace.hpp",
                  "text_tags.hpp", "units.hpp"}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    # every class and struct declared in a header that is NOT one of the generated duplicates
    declared = {}
    for path in glob.glob(os.path.join(INCLUDE, "**/*.hpp"), recursive=True):
        name = os.path.basename(path)
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in re.finditer(r"\b(?:class|struct)\s+(\w+)", text):
            declared.setdefault(match.group(1), name)

    duplicates = []
    for path in glob.glob(os.path.join(INCLUDE, "**/*.hpp"), recursive=True):
        name = os.path.basename(path)
        if name in REGISTRY_FILES:
            continue
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in re.finditer(r"^struct (\w+) \{", text, re.M):
            struct = match.group(1)
            for suffix in SUFFIXES:
                if not struct.endswith(suffix):
                    continue
                base = struct[: -len(suffix)]
                if base in declared and declared[base] != name:
                    duplicates.append((name, struct, base, declared[base]))
                elif base in declared:
                    duplicates.append((name, struct, base, declared[base]))

    if args.list:
        print("classes and structs declared: %d" % len(declared))
        for row in duplicates:
            print("   %-28s %-28s duplicates %s (in %s)" % row)
        return 0

    print("classes and structs declared across the headers: %d" % len(declared))
    print("")
    if duplicates:
        print("SECOND DESCRIPTIONS OF AN EXISTING CLASS: %d" % len(duplicates))
        for file_name, struct, base, where in duplicates:
            print("   %-26s declares %-26s while %s declares %s" % (file_name, struct, where, base))
        print("")
        print("FAILING: a generated struct beside the class it describes is TWO DESCRIPTIONS OF ONE THING, and they drift -- this pair already")
        print("did, both defining the constructor's address. **A class that exists does not get a second declaration.** Either fold the members")
        print("into the class or keep them in the table they came from and leave the class alone.")
        return 1
    print("PASS: no header declares a second description of a class that already exists.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
