# -*- coding: utf-8 -*-
"""Record that the easy queue is empty and that the ranking has to be by chain."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "no-unreversed-export-is-a-simple-accessor",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("of the 128 unreversed exports, none has a delegation chain whose largest function is 64 bytes or less, so ranking them by entry-point size "
                      "does not find the easy ones"),
        "witness": ("re/g_chain_size.py follows each export's calls and jumps and reports the largest function reached: 0 exports have a chain under 64 bytes and 128 "
                    "delegate to something bigger. GetLength at 0xB130 is 36 bytes and reaches 2620; GetFillRatio at 0xB4B0 is 34 bytes and reaches 2493; "
                    "AddHoleToPartVariant at 0x16D00 is 49 bytes and reaches 3494"),
        "round": 746,
    },
    {
        "subject": "a-rip-relative-jmp-is-an-import-thunk",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("0x63F228 is an import thunk -- `jmp qword ptr [rip + 0x4e9cee]` with nop padding repeating every 8 bytes -- so GetPartUserStringEx's chain "
                      "leaves the module there, while 0x64AEA0 is the module's own 403-byte logging helper and not a thunk"),
        "witness": ("disassembling 0x63F228 gives `jmp qword ptr [rip + 0x4e9cee]`, `nop`, `nop`, then `jmp qword ptr [rip + 0x4e9cde]` eight bytes later; "
                    "0x64AEA0 gives `push rsi` / `push rbx` / `sub rsp, 0x38` and has a measured size of 403 bytes"),
        "round": 746,
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
