# -*- coding: utf-8 -*-
"""Record the width fix for shear and shearCorner, and the probe that could not be used."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "shear-and-shearCorner-are-thirty-two-bits",
        "grade": "CONSTRUCTOR",
        "kind": "offset",
        "predicate": ("Order's `shear` at +0x44 and `shearCorner` at +0x48 are std::uint32_t, not bool, because the setters store four-byte values there"),
        "witness": ("setShearMode at 0xDDC0 is 33 bytes and RE 0xDDD7 is `mov dword ptr [rsi + 0x44], ebx`; setPartialShearMode at 0xDDF0 is 36 bytes and RE 0xDE07 "
                    "is `mov dword ptr [rsi + 0x48], ebx` and RE 0xDE0A is the same at +0x44. The struct previously declared both as bool with padding05 and "
                    "padding06 beside them, so a four-byte store would have written the padding; the padding is now shrunk to match and the layout still reports "
                    "58 fields, 0 disagreements and sizeof 864"),
        "round": 744,
    },
    {
        "subject": "the-json-reader-truncated-a-value-and-not-a-flag",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("lcns/src/io.cpp read `shear` and `shearCorner` with asBool, which keeps only zero or one from a field whose store preserves the whole value"),
        "witness": ("setShearMode writes the argument unchanged (RE 0xDDD7 `mov dword [rsi + 0x44], ebx`), so `setShearMode(order, 7)` writes 7 while asBool returned 1; "
                    "the reader is now asNumber with a cast, and Value(order.shear) being ambiguous between overloads is the compiler reporting the width change"),
        "round": 744,
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
