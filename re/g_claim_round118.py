# -*- coding: utf-8 -*-
"""Record the four-way contradiction as a ledger entry, so it outlives this round's context."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIM = {
    "subject": "the-nester-base-layout-is-unresolved",
    "grade": "INSTRUCTION",
    "kind": "offset",
    "predicate": ("the placement of Nester's base data is UNRESOLVED: four pieces of evidence disagree and no round has settled which survives"),
    "witness": ("(1) 0xB4470 writes a vptr at +0x00, a pointer at +0x08 and two dwords at +0x10 and +0x14, with five callers. (2) lcns/include/lcns/base_chain.hpp "
                "already says `Multi::Nester` declares no data members and that the fields belong to N5Multi15CompositeNesterE, which would make Nester 0x08 and make "
                "0xB4470's +0x08 store a store into the class that file calls empty. (3) the direct Nester children put their first own member at +0x18 -- "
                "NestingNester derives straight from Nester and the suite asserts atSeedP == 0x18 -- which fits 0x10 and not 0x08. (4) the module allocates 0x28 for "
                "FlipNester (RE 0x2C953 mov ecx, 0x28), while Nester at 0x18 plus an 0x18 vector at CompositeNester's +0x18 is 0x30. **The declaration as it stands "
                "fits every allocation and is NOT established to be right**; what would settle it is a class deriving straight from Nester that reads +0x08, +0x10 or "
                "+0x14 through its own object"),
    "round": 761,
}


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    if any(existing.get("subject") == CLAIM["subject"] for existing in data["claims"]):
        print("the claim is already there")
        return 0
    data["claims"].append(CLAIM)
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("added; %d total" % len(data["claims"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
