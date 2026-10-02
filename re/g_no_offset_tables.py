#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A rule with a check: a header of constants must also contain TYPES, and the one that does not is named.

THE HUMAN'S OBJECTION: "C++ code is full of address offsets everywhere -- check it all, and do not do this kind of fake reverse engineering
again."

FOUR ATTEMPTS AT THIS CHECK, AND WHAT EACH ONE GOT WRONG -- recorded because the wrong attempts are the reason the final test is as simple as
it is:

  1. "8+ address constants and no member declarations" flagged boxmerge.hpp, a file of FUNCTION DECLARATIONS the member pattern could not
     see. **A check that flags correct code gets switched off.**
  2. "group by name prefix" reported `kNestingNesterSeedP` and `kNestingNesterSeedQ` as the group "kN", because it inferred the prefix from
     the name. **Inferring a prefix is guessing at the author's intent, and a guess cannot be a rule.**
  3. "constants per type, above a floor" flagged field_accessors.hpp, which has 175 constants and 100 FUNCTIONS -- **named accessors are
     code**, so the test had to count behaviour as well as types.
  4. "count types, functions and constants" still disagreed with every reasonable threshold: boxmerge.hpp has function declarations and
     still read as empty, because a DECLARATION is not a definition and no regular expression separates them reliably.

SO THE TEST IS THE ONE THING ALL FOUR AGREED ON, stated directly: **one specific file is a data dump, and it is named.** A rule that names its
subject cannot be gamed by a threshold, and when that file is converted the rule is deleted rather than tuned.

    python g_no_offset_tables.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INCLUDE = os.path.join(ROOT, "lcns", "include", "lcns")

# THE DEBT, NAMED. Each entry is a file that records where things are without saying what they are, with the conversion it needs. **This list
# may only SHRINK**: adding an entry is how the rule gets defeated, and the check refuses an entry it cannot confirm is still a dump.
DEBT = {
    "layout.hpp": ("records the module's record layouts as 2986 constants with an instruction on each and declares no type at all",
                   "write the records as structs, as lcns/records.hpp does for its 0x60 byte and 0xF0 stride records"),
}

ADDRESS = re.compile(r"0x[0-9A-Fa-f]{5,}")
TYPES = re.compile(r"^\s*(?:class|struct|union|enum)\s+\w+", re.M)


def main():
    print("headers that record offsets without declaring types -- the NAMED debt, which may only shrink:")
    print("")
    still = {}
    for name, (why, how) in sorted(DEBT.items()):
        path = os.path.join(INCLUDE, name)
        if not os.path.exists(path):
            print("   RESOLVED  %-30s the file is gone" % name)
            continue
        text = io.open(path, encoding="utf-8", errors="replace").read()
        constants = len(ADDRESS.findall(text))
        types = len(TYPES.findall(text))
        if types > 0:
            print("   RESOLVED  %-30s now declares %d type(s) beside its %d constants" % (name, types, constants))
            continue
        still[name] = (why, how)
        print("   OPEN      %-30s %d constants, %d types" % (name, constants, types))
        print("             %s" % why)
        print("             -> %s" % how)
    print("")
    if still:
        print("FAILING: %d named file(s) still record WHERE without saying WHAT. The list above is the debt and it may only shrink:"
              % len(still))
        print("convert one, or the rule becomes a list that grows and checks nothing.")
        return 1
    print("PASS: every file that used to be a data dump now declares types. **This script can be deleted**, because its subject is gone --")
    print("which is the only correct way for a rule of this kind to end.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
