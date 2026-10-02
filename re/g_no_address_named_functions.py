#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""A rule with a check: a function whose name carries its own OFFSET is a calling convention, not a program.

FOUR WRONG VERSIONS OF THIS CHECK, and each is recorded because the last one is what makes the rule right:

  1. "any name ending in a hex address" flagged `setAutomaticStop_0E010` and `setCommonCutSafetyPreference_0E940` -- **names that DO say what
     they do and keep the RVA as evidence.** A check that flags correct code gets switched off.
  2. exempting `sub_*` by prefix did not cover a probe file, and exempting by the word `get`/`set` **let the actual defect through**, because
     `getDword00_52F920` starts with `get`.
  3. "any line matching the pattern" flagged three COMMENTS in test_exports.cpp that name an anonymous export by its address, which is citing
     evidence.

**THE TELL IS THE OFFSET IN THE NAME, WITH A WIDTH OR TYPE WORD BEFORE IT**: `getDword00_52F920` is `<verb><type><two-hex-digits>_<rva>`, and
the two hex digits are the field's OFFSET. `setAutomaticStop_0E010` has no offset in it -- `AutomaticStop` is a domain term -- so it passes.

    python -u g_no_address_named_functions.py [--list]
"""
import argparse
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# <word>_<rva> as a DECLARED function, which is the shape to judge
ADDRESS_NAMED = re.compile(r"\b(\w+?)_([0-9A-F]{4,6})\s*\(")
# AND THE TELL: a type word followed by TWO HEX DIGITS, which is the field's OFFSET written into the name
OFFSET_IN_NAME = re.compile(r"^(?:get|set|addr|copy|move|iset)?(?:Dword|Byte|Word|Qword|Ptr|Double|Bool|Int|Float|Short|Long|A0|00)"
                            r"([0-9A-F]{2})$")
# the embedded shims and the module's own byte registry, whose ONLY identifier is an address -- verified by reading gen_blobs.cpp: each entry is
# a comment with the address, the size, a status and a sha256, because the packer stripped the export names
SHIM = re.compile(r"^(?:sub|lcns_orig|orig)_")
EXEMPT_FILES = {"exports_impl.hpp", "exports_impl.cpp", "api_exports.cpp", "exports_forwarding.inc", "recovery.hpp",
                "gen_blobs.cpp", "gen_table.cpp", "gen_orig.S", "embedded.hpp", "embedded_shims.cpp"}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    rows = []
    for pattern in ("**/*.hpp", "**/*.cpp"):
        for base in (os.path.join(ROOT, "lcns", "include", "lcns"), os.path.join(ROOT, "lcns", "src"),
                     os.path.join(ROOT, "lcns", "tests"), os.path.join(ROOT, "lcns", "apps")):
            for path in glob.glob(os.path.join(base, pattern), recursive=True):
                name = os.path.basename(path)
                if name in EXEMPT_FILES:
                    continue
                hits = []
                for line in io.open(path, encoding="utf-8", errors="replace").read().split("\n"):
                    stripped = line.strip()
                    if stripped.startswith(("//", "*", "/*")):
                        continue          # a COMMENT naming an address is citing evidence
                    for word, _address in ADDRESS_NAMED.findall(line):
                        if SHIM.match(word) or not OFFSET_IN_NAME.match(word):
                            continue
                        hits.append(word)
                if hits:
                    rows.append((name, len(hits), sorted(set(hits))[:5]))

    rows.sort(key=lambda r: -r[1])
    if args.list:
        for name, count, sample in rows:
            print("   %-28s %3d  %s" % (name, count, ", ".join(sample)))
        return 0

    print("files declaring functions with an OFFSET IN THE NAME: %d" % len(rows))
    print("such functions: %d" % sum(r[1] for r in rows))
    for name, count, sample in rows[:12]:
        print("   %-28s %3d  %s" % (name, count, ", ".join(sample)))
    print("")
    if rows:
        print("FAILING: a function named `getDword00_52F920` carries its own OFFSET and the address it was found at, and a caller has to know")
        print("both. **This is `at_0020` one level up** -- a member named after its offset, a function named after its offset AND its address.")
        print("A name that says what the function does is what is required; the RVA may stay as the evidence beside it.")
        return 1
    print("PASS: no function carries its own offset in its name.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
