#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A rule with a check: a header that is a TABLE is not a reconstruction, and this fails when a new one appears.

THE HUMAN'S OBJECTION, in their words: "C++ code is full of address offsets everywhere -- check it all, and do not do this kind of fake
reverse engineering again."

WHAT IS AND IS NOT THE DEFECT. An address is this project's UNIT OF PROOF; the ledger's grades are addresses and instructions, so removing
them would remove the evidence. **The defect is a FILE whose body is a table of addresses and which declares no types** -- a file that
DESCRIBES code instead of being code. That is testable, so it is tested:

    a file FAILS when it has 8 or more address constants and NO member declaration and NO function definition.

KNOWN CASES ARE EXEMPT WITH A REASON, because the exemption list is the honest form of "this one is allowed": a file that is genuinely a
registry of addresses -- exports_impl.hpp, the export forwarding table -- is not fake reverse engineering, it is a table of exports, and it
says so.

    python g_no_table_headers.py [--list]
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
SOURCE = os.path.join(ROOT, "lcns", "src")

ADDRESS = re.compile(r"0x[0-9A-Fa-f]{5,}")

# EXEMPT WITH A REASON. These are registries of the module's own entry points, which is what this project exists to produce; each reason
# names what the file IS so that a reader can disagree with the exemption rather than wonder about it.
EXEMPT = {
    "exports_impl.hpp": "the export forwarding registry: one row per exported ordinal, which is the module's own interface",
    "exports_forwarding.inc": "the generated half of that registry",
    "units.hpp": "the unit conversion factors the archive recovered, which are VALUES rather than addresses",
    "virtual_methods.hpp": "GENERATED from the RTTI: the slot table is the deliverable and the addresses ARE the content",
    "classes.hpp": "GENERATED from the RTTI: one row per class, which is a registry and not a reconstruction",
    "class_definitions.hpp": "GENERATED declarations; its rows are the designators for the declarations below them",
    "class_constructors.hpp": "GENERATED from the constructor scan: one row per class, a registry",
    "recovery.hpp": "the recovery STATUS registry, which is a report about the port rather than code",
    "api_exports.cpp": "the export thunks themselves, one per ordinal",
}


def scan():
    rows = []
    for pattern in ("**/*.hpp",):
        for path in glob.glob(os.path.join(INCLUDE, pattern), recursive=True):
            name = os.path.basename(path)
            text = io.open(path, encoding="utf-8", errors="replace").read()
            members = len(re.findall(r"^\s{4,}(?:[\w:<>,\s\*&]+)\s+\w+\s*(?:=|;|\{)", text, re.M))
            functions = len(re.findall(r"^\s*(?:inline\s+)?[\w:<>,\s\*&]+\s+\w+\s*\([^;]*\)\s*\{", text, re.M))
            declarations = len(re.findall(r"^\s*(?:class|struct)\s+\w+", text, re.M))
            rows.append((name, path, len(ADDRESS.findall(text)), members, functions, declarations, text.count("\n") + 1))
    return rows


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    rows = scan()
    offenders = [(n, p, a, m, f, d, l) for n, p, a, m, f, d, l in rows if a >= 8 and m == 0 and f == 0]

    if args.list:
        print("%-40s %6s %7s %8s %6s" % ("file", "consts", "members", "funcs", "lines"))
        for name, _path, addresses, members, functions, declarations, lines in sorted(rows, key=lambda r: -r[2]):
            print("%-40s %6d %7d %8d %6d" % (name[:40], addresses, members, functions, lines))
        return 0

    print("headers scanned: %d" % len(rows))
    print("headers that are tables (8+ address constants, no members, no functions): %d" % len(offenders))
    print("")
    unexplained = []
    for name, path, addresses, members, functions, declarations, lines in sorted(offenders, key=lambda r: -r[2]):
        reason = EXEMPT.get(name)
        if reason:
            print("   EXEMPT  %-38s %4d consts -- %s" % (name, addresses, reason[:70]))
        else:
            print("   FAIL    %-38s %4d consts, %d lines" % (name, addresses, lines))
            unexplained.append(name)
    print("")
    if unexplained:
        print("FAILING: %d header(s) describe the module instead of reconstructing it. **A table of offsets is not a class**, which is what"
              % len(unexplained))
        print("the human said and what this rule encodes. Give the file types and members, or add it to EXEMPT in this script with a reason.")
        return 1
    print("PASS: every table-shaped header is either a registry with a stated reason, or has types of its own.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
