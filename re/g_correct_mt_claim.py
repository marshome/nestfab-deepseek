# -*- coding: utf-8 -*-
"""Correct last round's claim, which was WRONG: it said the object IS 0x9e0 bytes, and 0x9e0 is the ALLOCATION.

**WHAT WAS CLAIMED:**

    "Multi::RandomSheetSelector is 0x9e0 bytes as allocated and carries a complete std::mt19937: 624 state words from +0x1C, an index written as EIGHT bytes
     at +0x9D8, ..."

**and the first clause states a size that the offsets themselves contradict**: 624 words from +0x1C reach +0x9DB, the eight bytes at +0x9D8 OVERLAP their last
word, so a member can only begin at +0x9E0 and the declaration measures **0x9E8**. **`0x9e0` is what `mov ecx, 0x9e0` asks the ALLOCATOR for, and a claim that the
object IS that size takes an allocation for a layout.**

**AND A SECOND CONSTRUCTOR SETTLED THE GENERATOR'S OWN ARITHMETIC**, which the claim also did not have: `0x84510` builds the same generator with `mt` at +0x00 and
`mti` at +0x9C0, so **`mti` is 0x9C0 bytes after `mt`** and that does not depend on either object.

**SO THE CLAIM IS REPLACED** rather than left standing with a note: a wrong number is worse than a missing one.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")
SUBJECT = "RandomSheetSelector-embeds-an-mt19937"

REPLACEMENT = {
    "subject": "RandomSheetSelector-embeds-a-generator-of-the-same-shape",
    "grade": "INSTRUCTION",
    "kind": "offset",
    "predicate": ("Multi::RandomSheetSelector's constructor seeds the same generator shape as the one 0x84510 builds: 624 words four bytes apart from +0x1C and an "
                  "eight byte index value written at +0x9D8, so mti sits 0x9C0 bytes after mt"),
    "witness": ("0x0B0084 sets +0x18 to 1; 0x0B0097 imul eax,eax,0x6c078965 and 0x0B00A8 cmp rdx,0x270 are the MT19937 seeding signature this project records in "
                "re/19_mt19937.py, and the loop writes [rbx + rdx*4 + 0x18] for rdx 1..0x26F; 0x84530's loop writes [rax + rcx*4] at base +0x00 and 0x8455E "
                "writes qword [rax + 0x9c0], 0x270 -- so the two mti fields are 0x9C0 after their mt and RandomSheetSelector's eight byte store at 0x0B00B7 "
                "lands at +0x9D8 = +0x18 + 0x9C0"),
    "round": 723,
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
    print("replaced: the size 0x9e0 was the ALLOCATION, and the generator's arithmetic now comes from two constructors instead of one")
    return 0


if __name__ == "__main__":
    sys.exit(main())
