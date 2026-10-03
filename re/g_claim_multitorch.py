# -*- coding: utf-8 -*-
"""Record this round: the third argument, and the test that had the same bug as the implementation."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "multitorch-positive-flag-is-the-third-argument",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("setMultiTorchCuttingPreference_0F130 takes THREE arguments: it stores `edx` at +0x9C, sets the byte at +0x98 unconditionally, and takes "
                      "the byte at +0xA0 from `r8d > 0` rather than from the value"),
        "witness": ("0xF13D mov r12d, edx and 0xF140 mov ebp, r8d; 0xF223 test ebp, ebp; 0xF225 mov byte [rsi + 0x98], 1; 0xF22C setg byte [rsi + 0xa0]; 0xF233 "
                    "mov dword [rsi + 0x9c], r12d. `ebp` is never stored, so the third argument is read, tested and discarded. The implementation had two "
                    "parameters and computed the flag from `value > 0`, and its test passed because both calls used the value AS the flag"),
        "round": 738,
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
