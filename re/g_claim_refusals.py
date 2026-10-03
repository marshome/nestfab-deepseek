# -*- coding: utf-8 -*-
"""Record this round: two refusals were the probe's error, the list was right, and 42 dispatch."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "two-refusals-were-the-probes-error",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("the arity probe counted a register as an argument whenever it appeared as a SOURCE, so GetNumberOfNestedParts looked like two arguments "
                      "(the second is `mov rcx, [rbx + 8]`, a destination) and sub_0AFF0 looked like none (`test edx, edx` reads edx and writes nothing)"),
        "witness": ("0xB195 mov rbx, rcx then 0xB1A4 mov rcx, qword [rbx + 8]; and 0xAFF0's body is test edx, edx / setne byte [rcx + 0xf8] / ret. Both are wired "
                    "now and the implementations' signatures -- getNumberOfNestedParts(void*) and setByteAtF8(void*, int) -- match the instructions"),
        "round": 737,
    },
    {
        "subject": "the-forwarding-list-was-right-about-286-and-288",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("kForwarding's ordinals 286 and 288 are NOT swapped: 286 is sub_0B000 at rva 0xB000 and setDoubleAndFlag, and 288 is sub_0AFF0 at rva "
                      "0xAFF0 and setByteAtF8"),
        "witness": ("0xAFF0, 10 bytes, is test edx, edx / setne byte [rcx + 0xf8] / ret -- a byte at +0xF8, which is setByteAtF8; 0xB000, 18 bytes, is test edx, "
                    "edx / movsd qword [rcx + 0x100], xmm2 / setne byte [rcx + 0xf9] / ret -- a double at +0x100 and a flag at +0xF9, which is setDoubleAndFlag. "
                    "**An earlier claim that the list had them swapped was wrong and is withdrawn** -- it would have sent a later round to fix a correct file"),
        "round": 737,
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
