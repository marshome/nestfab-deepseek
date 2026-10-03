# -*- coding: utf-8 -*-
"""Re-grade the two node claims: the slot observation is INSTRUCTION-level, and the class claim is what the typeinfo chains support.

**THE LEDGER REFUSED THE FIRST VERSION AND ITS REASON IS THE RULE**: "a type claim needs CONSTRUCTOR but has INSTRUCTION". I had graded

    a-kind-tag-is-not-two-classes    kind=type    grade=INSTRUCTION

**and the two witnesses are not the same KIND of evidence.** What I read is four slot bodies -- `movsd xmm0, [rcx + N] / ret` -- and **that establishes the
offsets each slot reads**, which is an instruction-level fact. The class-level fact is the two typeinfo chains, and `the-node-family-is-three-classes` already
carries it at CONSTRUCTOR grade.

**SO THE SLOT OBSERVATION IS RESTATED AS WHAT IT IS** -- the offsets two vtable slot bodies read -- **rather than as a claim that a tag cannot express
something**, which is a statement about the port's old shape and not about the module.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")
SUBJECT = "a-kind-tag-is-not-two-classes"

REPLACEMENT = {
    "subject": "the-two-node-tables-read-the-same-offset-in-different-slots",
    "grade": "INSTRUCTION",
    "kind": "offset",
    "predicate": ("TerminalNode's vtable slot 2 reads +0x48 and its slot 3 reads +0x50, while SplitNode's slot 2 reads +0x50 and its slot 3 reads +0x58, so the "
                  "offset +0x50 is read from DIFFERENT SLOTS in the two tables"),
    "witness": ("TerminalNode 0xA3B570 slots 2 and 3 are movsd xmm0,[rcx+0x48]/ret at 0x974F0 and movsd xmm0,[rcx+0x50]/ret at 0x97500; SplitNode 0xA3BB70 "
                "slots 2 and 3 are movsd xmm0,[rcx+0x50]/ret at 0x97510 and movsd xmm0,[rcx+0x58]/ret at 0x97520"),
    "round": 718,
}


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    claims = data["claims"]
    before = len(claims)
    kept = [c for c in claims if c.get("subject") != SUBJECT]
    if before == len(kept):
        print("REFUSING: the claim is not found by that subject")
        return 2
    kept.append(REPLACEMENT)
    data["claims"] = kept
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("re-graded as %s/%s: the four slot bodies are instruction evidence and the typeinfo chains are the class evidence" % (REPLACEMENT["grade"], REPLACEMENT["kind"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
