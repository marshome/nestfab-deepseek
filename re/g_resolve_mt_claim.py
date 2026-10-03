# -*- coding: utf-8 -*-
"""Replace the "cannot all hold" claim: it CAN all hold, and what was wrong was MY READING of `mov dword [rbx + 0x18], 1`.

**THE CLAIM SAID:** "RandomSheetSelector's three measurements cannot all hold: the allocation is 0x9e0, the 624 state words reach +0x9DB, and 0x0B00B7 writes EIGHT
bytes at +0x9D8, so the declaration measures 0x9E8."

**AND ALL THREE HOLD.** `0x0B007F mov edx, 1` starts the loop at ONE, and `0x0B0084 mov dword [rbx + 0x18], 1` is **`mt[0]` -- the seed, which the standard
seeding puts in the state's first word.** So:

    0B0084  mt[0] = 1                       at +0x18
    0B00A0  mt[rdx] for rdx = 1 .. 623      at +0x1C .. +0x9D7
    0B00B7  mti, EIGHT bytes                at +0x9D8
    and 0x9D8 + 8 = 0x9e0 = `mov ecx, 0x9e0` at 0x0B004B

**`mt` is 624 words from +0x18 to +0x9D7 and NOTHING OVERLAPS.** The eight bytes I could not place came from treating +0x18 as an index, which made the array start
at +0x1C and run four bytes too far. **The claim is REPLACED, and the reading error is named, because that is what a wrong claim is for.**
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")
SUBJECT = "the-mt-state-overlaps-its-index"

REPLACEMENT = {
    "subject": "the-mt-state-does-not-overlap-its-index",
    "grade": "INSTRUCTION",
    "kind": "offset",
    "predicate": ("RandomSheetSelector's mt is 624 words from +0x18 to +0x9D7 and mti is EIGHT bytes at +0x9D8, so 0x9D8 + 8 = 0x9e0 is exactly the "
                  "allocation and nothing overlaps"),
    "witness": ("0x0B007F mov edx, 1 starts the seeding loop at ONE; 0x0B0084 mov dword [rbx + 0x18], 1 is mt[0], the seed; 0x0B00A0 mov dword [rbx + rdx*4 + "
                "0x18], ecx therefore writes mt[1] at +0x1C through mt[623] at +0x9D7; 0x0B00B7 mov qword [rbx + 0x9d8], 0x270 writes EIGHT bytes at +0x9D8 "
                "(raw bytes b9e0090000 at 0x0B004B are the 0x9e0 allocation, so the immediates are not misread)"),
    "round": 724,
}

# the earlier claim's wording is quoted in the replacement, so a reader sees what was corrected
REPLACEMENT["witness"] += " The earlier claim that these could not all hold came from reading +0x18 as an index, which put the array at +0x1C and four bytes too long"


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
    print("replaced: the three measurements DO hold, and the error was reading +0x18 as an index rather than as mt[0]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
