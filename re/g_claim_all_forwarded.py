# -*- coding: utf-8 -*-
"""Record that every forwarded ordinal now dispatches, and why four refusals were wrong."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "all-forty-seven-forwarded-ordinals-dispatch",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("all 47 kForwarding ordinals have a wrapper that calls the named implementation, and 121 of the 168 wrappers still report their ordinal"),
        "witness": ("re/g_forwarding_gap.py reports 47 dispatching and 0 not; re/g_export_status.py counts 47 calls of the shape exports::impl::<name>( and 121 "
                    "notReversed stubs, which sum to 168"),
        "round": 739,
    },
    {
        "subject": "four-arity-refusals-were-the-probes-error",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("four of the arity refusals were the probe's error, each for a different reason: a destination counted as an argument, `test` writing no "
                      "register, doubles in xmm that the integer rule cannot see, and a logger's copy of the object counted as a second parameter"),
        "witness": ("GetNumberOfNestedParts: 0xB1A4 mov rcx, qword [rbx + 8] is a destination. sub_0AFF0: 0xAFF0 test edx, edx reads both operands and writes none. "
                    "SetMarkMode: 0x188F0 movapd xmm7, xmm2 and 0x188F4 movapd xmm6, xmm3 are arguments 3 and 4. NoFitGetNumberOfExternalPolygons: 0x89D8 mov "
                    "rdx, rcx is a copy for the logger called at 0x89E2, and the body starts at 0x89E7"),
        "round": 739,
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
