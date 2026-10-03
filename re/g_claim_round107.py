# -*- coding: utf-8 -*-
"""Record the eight typed setters and the tail-call trap in a size-ranked queue."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "eight-setters-left-the-option-carrier",
        "grade": "CONSTRUCTOR",
        "kind": "offset",
        "predicate": ("the eight option setters take Order* and write named fields -- fillLastNestingStrategy +0x40, floatingMode +0x20, originPackingMode +0x21, "
                      "evaluateIntermediateNestingsAsLast +0x41, reorganizeBiggestPartNearOrigin +0x22, reorganizeLongestPartNearOrigin +0x23, shearCorner +0x48, "
                      "shear +0x44, and the low byte of field1C at +0x1C -- instead of casting OptionFlagCarrier*"),
        "witness": ("the RE addresses are on each statement: 0xDDA9, 0xDD49, 0xDD79, 0x1045F, 0x1048F, 0x104BF, 0xDE07, 0xDE0A and 0xDE69, each a `setne byte` except "
                    "0xDE07 and 0xDE0A which are `mov dword`; the wrappers convert the ABI handle once with reinterpret_cast<lcns::Order*>, and the tests read the "
                    "Order fields rather than the carrier's"),
        "round": 745,
    },
    {
        "subject": "a-size-ranked-queue-is-misled-by-tail-calls",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("ranking the unreversed exports by body size puts GetLength and GetHeight in the easy group although their entry points tail-call into 757- and "
                      "759-byte functions"),
        "witness": ("GetLength at 0xB130 is 36 bytes and ends `jmp 0x526160`, which is 757 bytes; GetHeight at 0xB160 is 36 bytes and ends `jmp 0x5266a0`, which is 759. "
                    "re/g_easy_queue.py lists 14 unreversed exports of 64 bytes or less, and these two plus GetBuildVersion, GetBuildDate and GetMajorVersion -- "
                    "which read GLOBALS through `mov rax, [rip + ...]` -- are the five that are not single-field accessors"),
        "round": 745,
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
