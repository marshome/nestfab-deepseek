# -*- coding: utf-8 -*-
"""Record the three facts the size work established, and the one it did not."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "nester-is-0x10-bytes-of-data-and-the-two-dwords-are-the-composites",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("the `Nester` base part is 0x10 bytes -- a vptr and one pointer at +0x08 -- so the two dwords `0xB4470` writes at +0x10 and +0x14 belong to whatever class owns that constructor, and the direct `Nester` children start their own members at +0x18"),
        "witness": ("`NestingNester` derives straight from `Nester` (typeinfo base N5Multi6NesterE) and its first own member measures 0x18, which lcns/tests/test_recovered.cpp asserts as `atSeedP == 0x18`; and its constructor 0x342E0 writes 0x18, 0x20, 0x28, 0x30, 0x38 and then 0x9F8/0xA00/0xA18, never +0x10 or +0x14. **None of 0xB4470's five callers writes its first own member below +0x18 either**, so the 0x10 is the base's data"),
        "round": 759,
    },
    {
        "subject": "the-composite-nesters-vector-does-not-fit-flipnesters-allocation",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("a `std::vector` at `CompositeNester`'s +0x18 would make it 0x30 bytes, which does not fit the 0x28 the module allocates for FlipNester, while LimitedNester's constructor writes a begin/capacity pair at +0x20 and +0x28 which is what a vector looks like"),
        "witness": ("RE 0x2C953 is `mov ecx, 0x28` then `call 0x998500` then `call 0x4B570` for FlipNester, so the object is at most 0x28; and 0x4AAFA writes +0x20 from r9 and 0x4AAF6 writes +0x28 from [r9 + 8] in LimitedNester. **Both cannot be true and this round does not establish which** -- so the four CompositeNester declarations stay reverted, and `static_assert(sizeof(T) <= allocation)` is what would catch a wrong resolution"),
        "round": 759,
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
