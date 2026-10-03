# -*- coding: utf-8 -*-
"""Record the three named flags and the two ways the layout guard caught the same mistake."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "three-order-flags-were-padding",
        "grade": "CONSTRUCTOR",
        "kind": "offset",
        "predicate": ("Order has a bool at +0x20, another at +0x21 and another at +0x40, named floatingMode, originPackingMode and fillLastNestingStrategy after the "
                      "exports that write them, where it previously carried padding01b and padding03"),
        "witness": ("RE 0xDD49 `setne byte [rsi + 0x20]` in CNS_SetFloatingMode, RE 0xDD79 `setne byte [rsi + 0x21]` in CNS_SetOriginPackingMode, and RE 0xDDA9 "
                    "`setne byte [rsi + 0x40]` in SetFillLastNestingStrategy; each was a carrier flag (flag20, flag21, flag40) whose offset fell inside an Order "
                    "padding member, and the layout test now reports 58 fields with 0 disagreements"),
        "round": 743,
    },
    {
        "subject": "offset-0x1C-has-two-views",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("offset +0x1C of Order is written as a DWORD by RE 0xD357 and as its LOW BYTE by RE 0xDE69, so field1C and OptionFlagCarrier::flag1C are two "
                      "views of the same four bytes rather than two fields"),
        "witness": ("0xD357 is `mov dword ptr [rsi + 0x1c], ebx` and 0xDE69 is `setne byte ptr [rsi + 0x1c]`; a byte member at that offset would alias the dword, "
                    "which is why the dword is declared and the byte is documented on it"),
        "round": 743,
    },
    {
        "subject": "naming-a-byte-inside-padding-grows-the-struct",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("replacing a padding member with named fields of the same total width keeps every later offset, and failing to do so moves them all and is "
                      "caught by the byte-level assertions rather than by a compile error"),
        "witness": ("removing padding01b[0x2] and padding03[0x1] and adding four one-byte members grew sizeof(Order) by four; `test_exports.cpp`'s memcpy at +0x1FC "
                    "and `test_recovered.cpp`'s per-field checks both failed, and shrinking padding02 from 4 bytes to 2 restored the size"),
        "round": 743,
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
