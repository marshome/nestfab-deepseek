# -*- coding: utf-8 -*-
"""Record what RE 0x5C8C50 actually does, and that StatBox::fold in the tree is WRONG.

Three attempts at this routine failed, each time because a reading was taken from a fragment rather than from the whole body. The body is
125 instructions and this reads it in two halves, which is the lesson: the first half looked like a two-axis min/max clamp and is not one.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")
import json  # noqa: E402

CLAIMS = [
    {
        "grade": "INSTRUCTION",
        "kind": "offset",
        "subject": "fold.5C8C50.structure",
        "predicate": ("RE 0x5C8C50 reads FOUR doubles from the element and folds them in PAIRS: element +8 and +0x10 against the "
                      "accumulator's low0/high0 and low1/high1, then element +0x18 and +0x20 against the same four"),
        "witness": ("0x5C8C69 movsd xmm0,[rdx+8] vs 0x5C8C6E [rcx+8] and 0x5C8C88 [rdx+8] vs [rcx+0x18]; 0x5C8C94 [rdx+0x10] vs "
                    "[rcx+0x10] and 0x5C8CB2 vs [rcx+0x20]; THEN 0x5C8CC6 [rdx+0x18] vs [rcx+8] and 0x5C8CDB vs [rcx+0x18]; 0x5C8CE7 "
                    "[rdx+0x20] vs [rcx+0x10] and 0x5C8CFC vs [rcx+0x20] -- so four element doubles reach the accumulator's two pairs in "
                    "two passes"),
        "round": 647,
    },
    {
        "grade": "INSTRUCTION",
        "kind": "offset",
        "subject": "fold.5C8C50.flag-is-inverted",
        "predicate": ("the accumulator's flag at +0x00 sends the routine DOWN the compare-and-keep path when it is ZERO and to the "
                      "0x5C8D10 path when it is NON-ZERO, which is the opposite of what lcns/stat.hpp's StatBox::fold assumes"),
        "witness": ("0x5C8C60 cmp byte ptr [rcx],0 / 0x5C8C63 jne 0x5C8D10, so zero falls through to 0x5C8C69's comparisons; and the "
                    "0x5C8D10 path ends at 0x5C8D00 jbe 0x5C8C55, which is the routine's `ret`, so that path can return without doing "
                    "what the other path does"),
        "round": 647,
    },
    {
        "grade": "INSTRUCTION",
        "kind": "offset",
        "subject": "fold.5C8C50.is-wrong-in-the-tree",
        "predicate": "lcns/stat.hpp's StatBox::fold does not implement RE 0x5C8C50 and must be rewritten or the claim removed",
        "witness": ("the committed fold treats a single value per axis, sets its flag on the first fold rather than clearing it, and has "
                    "no second pass; three attempts to reconcile it with the instructions failed, and the instructions above are what "
                    "the rewrite must follow"),
        "round": 647,
    },
]


def main():
    data = json.loads(io.open(LEDGER, encoding="utf-8").read())
    existing = {c["subject"] for c in data["claims"]}
    added = 0
    for claim in CLAIMS:
        if claim["subject"] in existing:
            continue
        data["claims"].append(claim)
        added += 1
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=1, sort_keys=True))
    print("added %d claim(s); the ledger now holds %d" % (added, len(data["claims"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
