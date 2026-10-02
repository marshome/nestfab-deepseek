# -*- coding: utf-8 -*-
"""Correct three things this round found, and none of them is a new class.

**1. THE LEDGER CLAIM ABOUT 0x1380D0 WAS RIGHT AND ITS WORDING WAS TOO NARROW.** The predicate called it "the routine a tree miss calls", and it is
MORE than that: `0x1380D0` is `squeezeCost`, the routine `re/row.hpp` already records as fully recovered (2375 bytes), and `0x13A3CC` calling it on a
tree miss is one of its callers rather than its identity. The claim's substance -- that it tests the enabled flag the constructor wrote -- is
verified at its own entry: `0x13810C cmp byte ptr [rdx + 8], 0`.

**2. `Tiling::Evaluator`'S SLOT 3 IS NOT `evaluate`.** Last round I recorded that slot 3 at 0x4E7E50 is "the base's implementation" of the evaluators'
evaluate. **READING IT SETTLES THAT IT IS SOMETHING ELSE**: 0x4E7E50 copies 0x60 bytes from its fourth argument and then DEEP COPIES A CONTAINER whose
elements are 0x90 bytes apart (`add rbx, 0x90` at 0x4E7F49), calling `0x63F2F8` per element and the allocator at 0x4E7F01. **That is a copy
constructor or a clone and not a scoring function**, and the element stride 0x90 matches the container `Tiling::Pattern` is recorded with.

**3. AND THE RELATION EVERY READING OF A VTABLE DEPENDS ON IS NOW CHECKED.** `slots[n]` is the word at `vtable_rva + 0x10 + n*8` -- the base holds a
NULL at +0 and the typeinfo at +8 -- and I twice read a SLOT'S VALUE as though it were a table's base, once reporting a slot-count discrepancy about
`MultiOrientedPartPattern` from `0xA3D310` (which is `MultitorchEvaluator`'s base) and once reading `BasicDistancer`'s entries from `0xA3B1E0` (which
is `Squeezer`'s own slot 2). `re/g_check_vtable_slots.py` verifies the relation for all 443 entries.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

# the claim to re-word, and the two to replace
REWORD = "Squeezer.enabled-gates-the-cost-path"
WRONG = "Evaluator.slot3-is-the-base-implementation"

REPLACEMENTS = [
    {
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("0x1380D0 -- the cost routine this project records as fully recovered -- tests the enabled flag the Squeezer constructor wrote, "
                      "at its own entry"),
        "round": 700,
        "subject": "Squeezer.cost-routine-tests-the-enabled-flag",
        "witness": ("0x13810C cmp byte ptr [rdx + 8], 0 is the routine's fourteenth instruction, and 0x138A6B writes byte 1 at that offset; "
                    "0x13A3CC is one of its callers, on a tree miss"),
    },
    {
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("Tiling::Evaluator's slot 3 is the same address 0x4E7E50 in SIX of its eight derived classes, and THAT ROUTINE IS NOT A SCORING "
                      "FUNCTION: it copies 0x60 bytes and deep copies a container of 0x90 byte elements"),
        "round": 700,
        "subject": "Evaluator.slot3-is-not-evaluate",
        "witness": ("0x4E7E5F..0x4E7EE6 copy [r8] through [r8 + 0x58] into [rcx]; 0x4E7F01 calls the allocator 0x998500; 0x4E7F41 calls 0x63F2F8 per "
                    "element; 0x4E7F49 and 0x4E7F50 add 0x90 to both pointers. An earlier claim called this the base's implementation of evaluate"),
    },
]


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    claims = data["claims"]
    # re-word the first
    for claim in claims:
        if claim.get("subject") == REWORD:
            claim["predicate"] = REPLACEMENTS[0]["predicate"]
            claim["witness"] = REPLACEMENTS[0]["witness"]
            claim["subject"] = REPLACEMENTS[0]["subject"]
            claim["round"] = 700
            print("re-worded %s" % REWORD)
    # replace the second
    before = len(claims)
    claims = [c for c in claims if c.get("subject") != WRONG]
    if len(claims) != before:
        print("removed the false claim %s" % WRONG)
    claims.append(REPLACEMENTS[1])
    data["claims"] = claims
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("%d claims" % len(claims))
    return 0


if __name__ == "__main__":
    sys.exit(main())
