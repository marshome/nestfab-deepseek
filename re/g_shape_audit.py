# -*- coding: utf-8 -*-
"""Audit every open SHAPE claim for the defect the last round named: a count over rows that do not agree.

The rule is "a count over a set is worthless unless the set is the one the claim is about", and the mechanical test is whether the ROWS
AGREE. Three claims have already failed it. This asks the question of ALL of them at once, which is cheap, and reports which need
re-measuring rather than promoting.

    python g_shape_audit.py

It cannot fetch the rows itself -- the rows live in the tools that produced them, and that is the honest limitation stated by
re/g_set_consistency.py. What it CAN do is classify each open SHAPE claim by what its own witness says, because a witness that reports
a COUNT OF FUNCTIONS is a claim about a set, and a set needs a consistency argument that most of these do not have.

So the audit's output is a TRIAGE: which claims rest on a count, which rest on an observation, and which already name their own gap.
That is what a round needs in order to choose, and it is derived from the ledger rather than from a reading of the image.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

COUNTISH = re.compile(r"\b\d+\s+(?:functions|callers|copies|sites|of them|rows)\b|\b\d+ functions\b", re.IGNORECASE)
OWNS_GAP = re.compile(r"no constructor|not read|never used|neither read nor|unchecked|not recovered|no label|no assertion", re.IGNORECASE)
SHAPE_OF = re.compile(r"begins|a sub-object with fields|fields \+|offsets", re.IGNORECASE)


def main():
    data = json.loads(io.open(LEDGER, encoding="utf-8").read())
    open_shape = [c for c in data["claims"] if c["grade"] == "SHAPE" and not c.get("superseded_by")]

    print("open SHAPE claims: %d" % len(open_shape))
    print("")
    counted = []
    observed = []
    gaps = []
    for claim in open_shape:
        text = claim["predicate"] + " " + claim["witness"]
        row = (claim["subject"], claim["round"], claim["predicate"])
        if OWNS_GAP.search(claim["witness"]) or OWNS_GAP.search(claim["predicate"]):
            gaps.append(row)
        elif COUNTISH.search(claim["witness"]):
            counted.append(row)
        else:
            observed.append(row)

    def show(title, rows, note):
        print("=== %s (%d)" % (title, len(rows)))
        print("    %s" % note)
        for subject, round_number, predicate in rows:
            print("    %-34s r%-4s %s" % (subject, round_number, predicate[:70]))
        print("")

    show("RESTS ON A COUNT and therefore needs a consistency argument", counted,
         "the rule from the last round applies to these: the rows behind the count must agree, and none of them names that check")
    show("RESTS ON AN OBSERVATION", observed,
         "these may not need a count at all, so the consistency rule does not reach them")
    show("ALREADY NAMES ITS OWN GAP", gaps,
         "these are honest about what is missing; the question is whether the gap can now be closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
