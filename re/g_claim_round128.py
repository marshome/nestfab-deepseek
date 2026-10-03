# -*- coding: utf-8 -*-
"""Record the capstone spelling quirk and the negative result about module-wide offset searches."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "capstone-prints-one-digit-displacements-in-decimal",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": "capstone prints a ONE-DIGIT memory displacement in DECIMAL and a larger one in hex, so `[rax + 8]` and `[rax + 0x10]` are the same notation for two different values",
        "witness": ("counting the spellings over the first few thousand functions gives `8` 38 times and `0x10` 20, `0x20` 14, `0x18` 12, `0x28` 6 -- **so a regex demanding an "
                    "`0x` prefix sees offset 8 NOWHERE.** A checker built that way reported NINE classes as having an untouched member at +0x8 at once, which is what the "
                    "tell looks like: **when the same offset comes out dead in many unrelated classes, the fault is in the reader.** And `[rax]` with no displacement is "
                    "offset 0, which has the same effect on vtable stores"),
        "round": 772,
    },
    {
        "subject": "a-module-wide-offset-search-cannot-support-a-member",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("searching the whole module for an offset cannot show that a declared member is supported, because 36068 distinct displacements occur somewhere and every "
                      "small offset is among them"),
        "witness": ("with the spelling fixed, `re/g_member_offsets_live.py` reports NO class with an untouched member -- **and that is a negative result about the question, "
                    "not a clean bill of health.** The check that CAN answer it is `re/g_members_without_instructions.py`, which pairs each class with a function (its "
                    "destructor) and then asks whether the object or an allocated block is touched **through that function's own object register** -- class attribution is "
                    "what the module-wide search lacks"),
        "round": 772,
    },
]


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    added = 0
    for claim in CLAIMS:
        if any(existing.get("subject") == claim["subject"] for existing in data["claims"]):
            continue
        data["claims"].append(claim)
        added += 1
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("added %d claim(s); %d total" % (added, len(data["claims"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
