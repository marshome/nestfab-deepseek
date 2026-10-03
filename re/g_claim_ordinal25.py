# -*- coding: utf-8 -*-
"""Add the ordinal-25 restoration claim, with the quoting done here rather than in a shell."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIM = {
    "subject": "ordinal-25-was-restored",
    "grade": "INSTRUCTION",
    "kind": "call",
    "predicate": ("GetNumberOfNestings, ordinal 25 at rva 0x0B0C0, dispatches again: its wrapper takes `Solution*` and returns `std::size_t`, calling "
                  "`impl::getNumberOfNestings`, after a table regeneration had replaced it with a `notReversed` stub"),
    "witness": ("kForwarding names `impl::getNumberOfNestings` at ordinal 25 and lcns/tests/test_exports.cpp has a runtime test for it with four 312-byte elements; "
                "the wrapper was `extern \"C\" int GetNumberOfNestings(Solution)` BY VALUE, reporting the ordinal and returning 0; 0xB0C5 is `mov rbx, rcx` and "
                "0xB0D4 is `mov rax, [rbx + 0x58]`, so rcx holds the address; the arithmetic is `0x6f96f96f96f96f97 * 3 = 0xAAAAAAAAAAAAAAAB`, which the "
                "implementation calls `modularInverse(3)`, and 312/8 = 39 which is the stride the instruction encodes"),
    "round": 735,
}


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    if any(existing.get("subject") == CLAIM["subject"] for existing in data["claims"]):
        print("the claim is already there")
        return 0
    data["claims"].append(CLAIM)
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("added %s; %d claims" % (CLAIM["subject"], len(data["claims"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
