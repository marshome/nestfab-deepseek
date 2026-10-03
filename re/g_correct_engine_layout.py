# -*- coding: utf-8 -*-
"""CORRECT the "four engines agree on eleven offsets" claim down to what the named registers actually show.

**WHAT LAST ROUND CLAIMED**: four engines read and write the same eleven offsets -- 0x00, 0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48 and 0x50 -- so the range
is the base's.

**WHAT THE NAMED OBJECT REGISTERS SHOW**: the four registers were read one at a time, and the intersection is much smaller.

    MultiEngine        through r13   1 offset:  +0x00
    DelayedEngine      through rdi  10 offsets: +0x00 +0x10 +0x18 +0x20 +0x28 +0x30 +0x38 +0x40 +0x48 +0x50
    NestingEngine      through r15   1 offset:  +0x00
    EquivalentEngine   through rsi  13 offsets: +0x00 +0x10 +0x18 +0x20 +0x28 +0x30 +0x38 +0x40 +0x48 +0x50 +0x54 +0x58 +0x60

**so the intersection of ALL FOUR is `+0x00` alone, and the intersection of the two that touch much at all is the ten offsets 0x00 to 0x50.** **The extra offsets that
`MultiEngine` was credited with came from counting EVERY register that ever received `rcx`, including `r15` after it took over from `r13`** -- **so the earlier finding
mixes registers and cannot support an eleven-offset claim.**

**AND `+0x54`, `+0x58` AND `+0x60` ARE `EquivalentEngine`'s ALONE** in this measurement, **so they are NOT shown to be the base's** and are not given to it.

**THE CORRECTION KEEPS WHAT THE TWO NAMED REGISTERS AGREE ON** -- the ten offsets from `DelayedEngine`'s rdi and `EquivalentEngine`'s rsi, in the same order with the
same widths -- **and says plainly that the other engines' contributions are unmeasured rather than agreeing.**
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

SUBJECT = "the-engines-share-one-member-layout-so-it-is-the-bases"

CORRECTED = {
    "predicate": ("TWO engines' named object registers read and write the same ten offsets -- 0x00, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48 and 0x50 -- "
                  "through registers that received `rcx`, which is evidence that the range is the BASE's data"),
    "witness": ("`DelayedEngine::run` through `rdi` (`756EEA mov rdi, rcx`) touches +0x00 +0x10 +0x18 +0x20 +0x28 +0x30 +0x38 +0x40 +0x48 +0x50; "
                "`EquivalentEngine::run` through `rsi` (reloaded from the `rcx` spill at [rsp + 0x210] by 0x75BDD8) touches the SAME ten and then +0x54 +0x58 +0x60. "
                "**`+0x54`, `+0x58` and `+0x60` are NOT shown to be the base's** -- only `EquivalentEngine` touches them here. **AND THE EARLIER VERSION OF THIS CLAIM SAID "
                "FOUR ENGINES AGREE ON ELEVEN OFFSETS, WHICH IS TOO STRONG**: `MultiEngine`'s extra offsets came from counting EVERY register that ever received `rcx`, "
                "including `r15` after it took over from `r13`, so they mix registers. **Measured through the one register each prologue establishes, `MultiEngine` "
                "(r13) and `NestingEngine` (r15) each show `+0x00` alone** -- which is agreement and not contradiction, but it is much less than was claimed"),
    "round": 771,
}


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    for claim in data["claims"]:
        if claim.get("subject") == SUBJECT:
            claim.update(CORRECTED)
            print("corrected %s in place" % SUBJECT)
            break
    else:
        print("REFUSING: the claim is not in the ledger")
        return 2
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
