#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""A rule with a check: the tree describes each module OBJECT once, and two structs over the same OFFSETS are the duplication it forbids.

**THE FIRST VERSION OF THIS CHECK WATCHED THE WRONG THING AND MISSED THE CASE IT WAS WRITTEN FOR.** It grouped structs by
(field count, field names) and caught `SimplexLinearProgram` in `lp.hpp` against `ClpLinearProgram` in `lp_clp.hpp` -- **which is NOT a duplication**: they
are two back-ends for the same linear program and having both is the point. Meanwhile `model.hpp`'s `Order` (49 offset-commented fields) and
`launching_order.hpp`'s `LaunchingOrderLayout` (127) went unnoticed, **because their field NAMES differ and a name-based signature cannot see that they
describe one object.**

**SO THE SIGNATURE IS THE OFFSET SET.** Each offset-commented field carries its offset in the comment, and two structs whose offset sets overlap
substantially describe the same module object whatever their fields are called. `re/g_adjudicate.py` is what then settles WHICH of them is right, by
comparing each against the store the module actually performs.

    python -u g_one_definition.py
    python -u g_one_definition.py --list
"""
import argparse
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

STRUCT = re.compile(r"^(?:struct|class)\s+(\w+)\s*(?::[^\{]*)?\{(?P<body>.*?)^\};", re.M | re.S)
# a field line carrying `+0xNNN` in its comment, which is how this project records an offset it derived
# **AND THE PADDING IS NOT A FIELD.** The permutation inserts `std::byte paddingNN[...]` members to force the next field onto its offset, and those
# declarations carry a `+0xNNN` comment -- so a field regex matches them and counts the tool's own scaffolding as the module's structure. **Thirteen of
# the "15 offsets only Order has" were padding**, and the same omission made `re/g_one_definition.py` report 68 shared offsets where this tool reports
# 67. A member whose type is `std::byte`, whose name begins with `padding` and whose width is zero is not a field.
NOT_A_FIELD = re.compile(r"^padding\d*$")
# **AND THE COMMENT MUST BE ON THE SAME LINE, WHICH IS THE FIX FOR A BUG THAT WAS ALREADY FIXED ELSEWHERE.** The pattern this replaces let its `//...` part span a
# NEWLINE, so `incompatibleSheets` -- which has no comment of its own -- matched the SECTION HEADER below it, "// --- pipe mode / late common-cut block
# (+0x170, +0x1A0..+0x1C0) ---", and was recorded as claiming +0x170. **A regex that can cross a newline will find the next line's data**, and the reason it
# was caught here is that `re/g_order_union.py` read the same file with the same-line rule and reported one field fewer -- **two tools disagreeing is what makes
# a bug like this visible.**
FIELD = re.compile(r"^\s+[\w:<>\s\*&\[\]]+?\b(\w+)\s*(?:\[[^\]]*\])?\s*(?:=[^;]*)?;[^\n]*?//[^\n]*?\+0x([0-9A-Fa-f]+)", re.M)

# PAIRS THAT ARE NOT A DUPLICATION, each with the reason. **`SimplexLinearProgram` and `ClpLinearProgram` share offsets because a linear program's
# fields are a linear program's fields, and the module has TWO back-ends for it** -- that is two implementations of one interface and both belong.
NOT_DUPLICATES = {
    frozenset({("lp.hpp", "SimplexLinearProgram"), ("lp_clp.hpp", "ClpLinearProgram")}):
        "two back-ends for one linear program: the offsets are the same because the DATA is, and the module has both",
}

# A PAIR THAT IS a duplication, with what settles it. **AND THE ADJUDICATION IS NOT SIMPLY "THE LAYOUT WINS"**: re/g_adjudicate.py compares WIDTHS and
# reports the layout 20 to 0, correct as far as it goes -- but the layout's names are OFFSET-DERIVED and `Order`'s come from the EXPORTS, so the two agree
# on only 2 names in 45 while describing the same 45 fields. **A reconciliation has to take `Order`'s names and the layout's widths**, which is what makes
# this a task with two lists rather than a choice between two structs.
KNOWN_DUPLICATES = {
    frozenset({("model.hpp", "Order"), ("launching_order.hpp", "LaunchingOrderLayout")}):
        "ONE object described twice. **THE NUMBERS, WITH THE PADDING THE PERMUTATION INSERTS EXCLUDED** (this tool counted it only because a padding member "
        "carries a `+0xNNN` comment, and it is excluded at NOT_A_FIELD): 54 shared offsets, 73 that only the layout has -- **62 of them carrying an unnamedXXX "
        "name**, which is the offset-derived shape this objective removes -- and 2 that only Order has. **So NEITHER is the module's object alone, and the merge "
        "direction is a real decision rather than a preference**: taking Order and adding the 73 puts 62 unnamedXXX members into the file being cleaned, and "
        "taking the layout deletes 234 call sites' names and the export-derived witnesses with them",
}

# **HOW TO TELL TWO STRUCTS OVER THE SAME OFFSETS APART FROM TWO STRUCTS THAT MERELY ALIGN, MEASURED RATHER THAN GUESSED.**
#
# The first version divided the shared count by the SMALLER offset set and reported 22 pairs, including `LaunchingOrderLayout` against
# `SimplexLinearProgram` -- **8 shared of 8, a 100% match, because the denominator measured the smaller struct rather than the relationship.** With an
# absolute floor the list came down to three, and reading the two that remained settled the real test:
#
#     OwnedChainNode (12 offsets)  vs LaunchingOrderLayout (127):  +0x00 unnamed000/unknown00, +0x10 multiplicityPreference/chain, ...
#     ScoreNode      (17 offsets)  vs LaunchingOrderLayout (127):  +0x20 unnamed020/minX, +0x28 unnamed028/minY, +0x30 unnamed030/maxX, ...
#
# **BOTH ARE STRUCTS WHOSE FIELDS FALL ON 8 BYTE BOUNDARIES AND THEREFORE SHARE WORD POSITIONS BY ARITHMETIC, AND NOT ONE SHARED OFFSET CARRIES THE SAME
# FIELD NAME.** The real duplication is different:
#
#     Order (49 offsets)           vs LaunchingOrderLayout (127):  45 shared, AND the shared ones are the SAME FIELDS with the same understanding
#
# **SO THE TEST IS SHARED OFFSETS COVERING MOST OF THE SMALLER STRUCT, AND *NOT* THE FIELD NAMES.** An earlier version also required a quarter of the
# shared offsets to carry the same name -- and that EXCLUDED `Order` against `LaunchingOrderLayout`, which agree on only TWO names, because one names a field by
# the export that sets it and the other by its offset. **A rule that excludes the case it was written for is the wrong rule**, and the coverage test separates
# the same two pairs without it: `ScoreNode` covers 17 of its 17 against the layout and IS arithmetic alone, while `Order` covers most of its own.
MIN_SHARED = 20
SMALLER_COVERED = 0.6


def structs():
    for path in sorted(glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "*.hpp"))):
        name = os.path.basename(path)
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in STRUCT.finditer(text):
            found = FIELD.findall(match.group("body"))
            if len(found) < 8:
                continue
            offsets = {}
            for field, offset in found:
                if NOT_A_FIELD.match(field):
                    continue      # **PADDING IS NOT A FIELD**, see the note at NOT_A_FIELD
                offsets[int(offset, 16)] = field
            yield name, match.group(1), offsets


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    rows = list(structs())
    if args.list:
        for name, struct, offsets in sorted(rows, key=lambda r: -len(r[2])):
            print("   %-22s %-34s %3d offsets, +0x%X .. +0x%X"
                  % (name, struct, len(offsets), min(offsets), max(offsets)))
        return 0

    overlaps = []
    for index, (name_a, struct_a, offsets_a) in enumerate(rows):
        for name_b, struct_b, offsets_b in rows[index + 1:]:
            shared = set(offsets_a) & set(offsets_b)
            if len(shared) < MIN_SHARED:
                continue
            # **AND THE SHARED OFFSETS MUST BE MOST OF THE SMALLER STRUCT.** Two structs whose fields land on 8 byte boundaries share word positions by
            # arithmetic alone -- `ScoreNode` shares 17 offsets with `LaunchingOrderLayout` and NONE of them is the same field. **AND THE NAMES CANNOT BE
            # THE TEST**: `Order` and `LaunchingOrderLayout` share 45 offsets and agree on only TWO names, because one names a field by the export that
            # sets it and the other by its offset -- so a name-based rule would EXCLUDE the very duplication this check exists for, which is what an
            # earlier version of it did.
            if len(shared) / min(len(offsets_a), len(offsets_b)) < SMALLER_COVERED:
                continue
            agreeing = sum(1 for offset in shared if offsets_a[offset] == offsets_b[offset])
            overlaps.append((frozenset({(name_a, struct_a), (name_b, struct_b)}),
                             agreeing / len(shared), len(shared), agreeing))

    print("structs with 8 or more offset-commented fields: %d" % len(rows))
    print("pairs sharing %d or more offsets and covering %.0f%% of the smaller struct: %d"
          % (MIN_SHARED, SMALLER_COVERED * 100, len(overlaps)))
    print("")
    unrecorded = []
    for pair, ratio, shared, agreeing in overlaps:
        members = sorted(pair)
        detail = "(%d shared offsets, %d of them the same field)" % (shared, agreeing)
        if pair in NOT_DUPLICATES:
            print("   NOT A DUPLICATE  %s  ==  %s   %s" % (members[0][1], members[1][1], detail))
            print("      %s" % NOT_DUPLICATES[pair])
        elif pair in KNOWN_DUPLICATES:
            print("   KNOWN DUPLICATE  %s  ==  %s   %s" % (members[0][1], members[1][1], detail))
            print("      %s" % KNOWN_DUPLICATES[pair])
        else:
            unrecorded.append((members, detail))
    print("")
    print("recorded as NOT a duplication: %d" % len(NOT_DUPLICATES))
    print("recorded as known debt:        %d" % len(KNOWN_DUPLICATES))
    print("")
    if unrecorded:
        print("FAILING: %d pair(s) describe the same offsets and are NOT recorded. **Two descriptions of one module object is what this project's")
        print("objective forbids**, and a new one is not to be added quietly: either reconcile it, or add it to NOT_DUPLICATES with the reason it is two")
        print("things, or to KNOWN_DUPLICATES with the adjudication that names the right one.")
        for members, shared in unrecorded:
            print("   UNRECORDED: %s == %s, %d shared offsets" % (members[0][1], members[1][1], shared))
        return 1
    print("PASS: every pair of structs over the same offsets is RECORDED as either two things or a known duplication with its adjudication.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
