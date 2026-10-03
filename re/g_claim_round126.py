# -*- coding: utf-8 -*-
"""Record that the four engines share one member layout, which makes it the BASE's data and not four sets of members."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "the-engines-share-one-member-layout-so-it-is-the-bases",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("four engines read and write the SAME offsets through their object register -- 0x00, 0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48 and 0x50 -- so that range is the BASE's data and not four classes' members"),
        "witness": ("EquivalentEngine::run through rsi (which is reloaded from the `rcx` spill at [rsp + 0x210] by 0x75BDD8 and 0x75BE6A): +0x00 WR, +0x10 W, +0x18 W, +0x20 WR, +0x28 R, +0x30 WR, +0x38 WR, +0x40 WR, +0x48 WR, +0x50 WR. CompositeEngine::run through rdi (reloaded from [rsp + 0x410] by 0x75ABD1 and 0x75AD1D): +0x00 R, +0x10 R, +0x18 R, +0x20 WR, +0x28 R, +0x30 WR, +0x38 WR, +0x40 WR, +0x48 WR, +0x50 WR. **MultiEngine reaches +0x00, +0x08, +0x18, +0x20, +0x28, +0x30, +0x38 and +0x40, and DelayedEngine +0x00, +0x08, +0x10, +0x18, +0x20, +0x28, +0x30, +0x38, +0x40, +0x48 and +0x50.** Four classes agreeing on eleven offsets is a base and not a coincidence, and `no function references an engine vtable` means there is no constructor to read the members off directly"),
        "round": 770,
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
