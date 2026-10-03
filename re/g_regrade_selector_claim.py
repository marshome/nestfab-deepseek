# -*- coding: utf-8 -*-
"""Re-grade the selector-name claim: what a RETURNED string's BYTES are is an instruction-level fact, not a type claim.

**THE LEDGER REFUSED IT AGAIN AND FOR THE SAME REASON AS THE NODE CLAIM**: "a type claim needs CONSTRUCTOR but has INSTRUCTION". What was read is two slot
bodies -- `movabs rcx, 0x74656568536c6c41` and `mov qword [rax + 8], 9` -- so what is established is **the bytes a method returns and the length it stores at
+0x08**, which is an instruction-level fact about a function. **The class-level facts are the two vtables and their slots, and that claim already carries
CONSTRUCTOR's witness.**

**AND THE DISTINCTION IS THE RULE'S WHOLE POINT**: a TYPE claim says what a thing IS and needs a constructor; an INSTRUCTION claim says what a body DOES and
needs the body. **Grading a fact about a body as a fact about a type is how a plausible answer gets a grade it has not earned.**
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")
SUBJECT = "the-selector-names-are-in-slot-3"

REPLACEMENT = {
    "subject": "slot-3-returns-the-selector-name",
    "grade": "INSTRUCTION",
    "kind": "call",
    "predicate": ("Multi::SheetSelector slot 3 returns a std::string: its body writes the small-string pointer at +0, the LENGTH at +8 and the bytes at +0x10, "
                  "with 9 and \"AllSheet\"+'s' for AllSheetSelector and 0xc and \"Largest\"+\"heet\" for LargestSheetSelector"),
    "witness": ("0x7D25E0: lea rdx,[rcx+0x10] / mov [rcx],rdx / movabs rcx,0x74656568536c6c41 / mov [rax+0x10],rcx / mov byte [rax+0x18],0x73 / mov qword "
                "[rax+8],9; 0x7D3CE0 the same shape with movabs rcx,0x537473656772614c, mov dword [rax+0x18],0x74656568 and mov qword [rax+8],0xc"),
    "round": 720,
}


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    claims = data["claims"]
    kept = [c for c in claims if c.get("subject") != SUBJECT]
    if len(kept) == len(claims):
        print("REFUSING: the claim is not found by that subject")
        return 2
    kept.append(REPLACEMENT)
    data["claims"] = kept
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("re-graded as %s/%s: a slot body establishes what the body DOES" % (REPLACEMENT["grade"], REPLACEMENT["kind"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
