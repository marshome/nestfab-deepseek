# -*- coding: utf-8 -*-
"""Record the two named fields and the destructive regenerator."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "order-names-the-0x18-and-0x1c-fields",
        "grade": "CONSTRUCTOR",
        "kind": "offset",
        "predicate": ("Order has a field at +0x18 and another at +0x1C, both four bytes, where it previously carried padding01[0x12] across +0x10..+0x21"),
        "witness": ("0xD310, 33 bytes, is `mov dword [rsi + 0x18], ebx` at 0xD327; 0xD340, 33 bytes, is `mov dword [rsi + 0x1c], ebx` at 0xD357; and +0x244's "
                    "`mov dword [rsi + 0x244], ebx` at 0xD447 was already `Order::unlockMode`. **The module names no field at +0x18 or +0x1C**, so they are named for "
                    "their offsets -- the same names IntFieldCarrier used, which is the point: one structure instead of two"),
        "round": 740,
    },
    {
        "subject": "the-measurement-regenerator-deleted-tests",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("re/g_measure_order_run.py replaced everything between its BLOCK_START and the finish marker, so every assertion appended after the "
                      "measurement block was inside the span it rewrote; one run deleted 217 lines and check_recovery then reported five classes with no test"),
        "witness": ("the guard now counts CHECK(, static_assert( and distinct lcns:: class names before and after and refuses when any falls; on the tree as it "
                    "stands it reports `REFUSING: the rewrite would remove evidence. checks 3982->3939, static_asserts 39->12, class names 123->113`. The test "
                    "file was restored from git, which is the difference between fixing a deletion and covering for it"),
        "round": 740,
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
