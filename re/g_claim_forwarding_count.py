# -*- coding: utf-8 -*-
"""Add this round's two claims: ordinal 84 is wired, and the forwarding COUNT is of a list rather than of the code."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "the-forwarding-count-is-of-the-list",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("kForwarding lists 47 ordinals and only 8 of their wrappers call the named implementation, and one of the 39 that do not is ordinal 25, "
                      "GetNumberOfNestings, which an earlier round implemented and forwarded and whose wrapper is now a notReversed stub"),
        "witness": ("re/g_forwarding_gap.py joins every kForwarding ordinal to its wrapper: 8 call impl:: and 39 do not. Commit 6cdca57 'the first four exports "
                    "implemented from their assembly (GetNumberOfNestings 0xB0C0, ...)' says ordinal 25 was forwarded, and lcns/src/api_exports.cpp's wrapper for "
                    "GetNumberOfNestings is now `lcns::dll::exports::notReversed(12u); return 0;` while kForwarding still names impl::getNumberOfNestings at 25. "
                    "The counts in this project's history -- 40, 43, 45, 47 -- are counts of the hand-written list, and kForwarding's own header warns that "
                    "regenerating the table must never erase a recovered behaviour"),
        "round": 734,
    },
    {
        "subject": "ordinal-84-dispatches",
        "grade": "CONSTRUCTION",
        "kind": "call",
        "predicate": ("SetLocalMaximumIterations, ordinal 84 at rva 0x0D400, has a wrapper that calls impl::setLocalMaximumIterations, which stores a 32-bit value "
                      "at +0x1FC with no clamp, and the table row says Forwarded"),
        "witness": ("lcns/src/api_exports.cpp's wrapper is `extern \"C\" void SetLocalMaximumIterations(Order* order, int iterations)` and calls "
                    "impl::setLocalMaximumIterations; the implementation stores through LocalEngineCarrier::maxIterations at +0x1FC, from 0x0D417 `mov dword "
                    "[rsi + 0x1fc], ebx`; re/exports_table.md counts 2 register arguments; test_exports.cpp asserts the store is 32-bit and not widened"),
        "round": 734,
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
