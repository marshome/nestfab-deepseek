#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Every constant address and every magic offset in the C++ -- classified by whether it is EVIDENCE or FAKE REVERSE ENGINEERING.

WHAT THE HUMAN OBJECTED TO, stated as precisely as it can be: "C++ code is full of address offsets everywhere, and do not do this kind of
fake reverse engineering again". The objection is not to addresses as such -- **an address is this project's unit of proof**, and the ledger
grades depend on them. The objection is to addresses and offsets used where the code should have a TYPE:

    GOOD, and required:   constexpr std::uintptr_t kRun = 0x759A80;   // RE 0x759AB0: the vtable slot
    GOOD, and required:   box.fold(...)   // the call the instruction at 0x5CD61D performs
    FAKE:                 a register of kFoo = 0x18, kFoo2 = 0x20, kFoo3 = 0x28 ... with the instruction in a comment
    FAKE:                 a struct whose members are absent and replaced by offsets into it

So this measures the BALANCE: how many address constants have a witness, how many magic offsets appear, and -- the number that matters --
**how much of the header tree is a table of offsets rather than declarations of types.** A file that is mostly constants and tables with
few class/struct declarations is a file that describes code instead of being code.

    python g_fake_reverse.py [--files] [--worst 15]
"""
import argparse
import collections
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INCLUDE = os.path.join(ROOT, "lcns", "include", "lcns")
SOURCE = os.path.join(ROOT, "lcns", "src")

# a hexadecimal constant that is an ADDRESS: six digits or more, or a named kFoo = 0x... in the address ranges this module uses
ADDRESS = re.compile(r"0x[0-9A-Fa-f]{5,}")
# a WITNESS: an instruction address and what it does, which is what makes a constant evidence rather than a claim
WITNESS = re.compile(r"RE\s+0x[0-9A-Fa-f]{4,}")
DECLARATION = re.compile(r"^\s*(?:class|struct)\s+\w+", re.M)
MEMBER = re.compile(r"^\s{4,}(?:[\w:<>,\s\*&]+)\s+\w+\s*(?:=|;|\{)", re.M)
TABLE_ROW = re.compile(r"^\s*\{\s*\"?[\w:\.\+]+\"?\s*,", re.M)


def files():
    out = []
    for pattern in ("**/*.hpp", "**/*.cpp"):
        out.extend(glob.glob(os.path.join(INCLUDE, pattern), recursive=True))
    out.extend(glob.glob(os.path.join(SOURCE, "*.cpp")))
    return sorted(set(out))


def classify(path):
    text = io.open(path, encoding="utf-8", errors="replace").read()
    addresses = ADDRESS.findall(text)
    witnessed = len(WITNESS.findall(text))
    declarations = len(DECLARATION.findall(text))
    members = len(MEMBER.findall(text))
    rows = len(TABLE_ROW.findall(text))
    return {
        "path": path,
        "name": os.path.relpath(path, ROOT),
        "addresses": len(addresses),
        "witnesses": witnessed,
        "declarations": declarations,
        "members": members,
        "rows": rows,
        "lines": text.count("\n") + 1,
    }


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", action="store_true")
    parser.add_argument("--worst", type=int, default=15)
    args = parser.parse_args(argv)

    rows = [classify(path) for path in files()]
    total_addresses = sum(r["addresses"] for r in rows)
    total_witnesses = sum(r["witnesses"] for r in rows)
    total_declarations = sum(r["declarations"] for r in rows)
    total_members = sum(r["members"] for r in rows)
    total_rows = sum(r["rows"] for r in rows)

    print("files scanned: %d" % len(rows))
    print("")
    print("  hex constants (5+ digits):      %d" % total_addresses)
    print("  RE witnesses:                   %d" % total_witnesses)
    print("  class/struct declarations:      %d" % total_declarations)
    print("  member declarations:            %d" % total_members)
    print("  table rows of the {name, 0x..., ...} shape: %d" % total_rows)
    print("")
    print("A WITNESS PER ADDRESS is the standard this project's ledger sets. Ratio: %.2f witnesses per address."
          % (total_witnesses / max(1, total_addresses)))
    print("")

    # A FILE IS "A TABLE, NOT CODE" WHEN IT HAS MANY CONSTANTS AND FEW OR NO DECLARATIONS OR MEMBERS
    tables = [r for r in rows if r["addresses"] >= 8 and r["members"] == 0]
    print("FILES THAT ARE TABLES RATHER THAN CODE (8+ address constants and NO member declarations): %d" % len(tables))
    for row in sorted(tables, key=lambda r: -r["addresses"])[:args.worst]:
        print("   %-44s %4d consts  %3d witnesses  %3d decls  %4d lines"
              % (row["name"][-44:], row["addresses"], row["witnesses"], row["declarations"], row["lines"]))
    print("")

    unwitnessed = [r for r in rows if r["addresses"] > r["witnesses"] * 3 and r["addresses"] >= 10]
    print("FILES WITH FAR MORE CONSTANTS THAN WITNESSES (3x or worse): %d" % len(unwitnessed))
    for row in sorted(unwitnessed, key=lambda r: -(r["addresses"] - 3 * r["witnesses"]))[:args.worst]:
        print("   %-44s %4d consts  %3d witnesses" % (row["name"][-44:], row["addresses"], row["witnesses"]))
    print("")

    if args.files:
        print("%-52s %6s %6s %6s %6s" % ("file", "consts", "witnes", "decls", "members"))
        for row in sorted(rows, key=lambda r: -r["addresses"]):
            print("%-52s %6d %6d %6d %6d" % (row["name"][-52:], row["addresses"], row["witnesses"],
                                             row["declarations"], row["members"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
