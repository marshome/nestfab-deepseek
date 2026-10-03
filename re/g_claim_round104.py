# -*- coding: utf-8 -*-
"""Record the measured reason the five remaining handles cannot become classes, and the Solution rename."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "a-struct-return-breaks-the-168-walk",
        "grade": "CONSTRUCTION",
        "kind": "call",
        "predicate": ("the export wrappers cannot return a recovered class BY VALUE, because every neutral stub is called with zero arguments through one uniform "
                      "function pointer and a struct return needs the caller to pass a return buffer address in rcx"),
        "witness": ("making Part, Sheet, Nesting and NestedPart return values instead of handles made `return nullptr` into `return Part{}` and test_exports.exe died "
                    "on 0xC0000005; lcns/tests/test_exports.cpp walks all 168 exports with `ex::RawFn fn = ex::addressOf(i); fn();` and no arguments, so rcx holds "
                    "whatever the loop left there and the callee writes the default object through it"),
        "round": 742,
    },
    {
        "subject": "solution-handle-is-renamed",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("`Solution` is no longer an opaque handle: api.hpp declares `struct Solution_t; using SolutionHandle = Solution_t*`, because Solution is used "
                      "only as a PARAMETER in the export wrappers and so the ABI is unchanged"),
        "witness": ("re/g_handle_usage.py finds Solution in wrapper parameter lists and in no return type, unlike Part, Sheet, Nesting, NestedPart and NoFitNesting "
                    "which are all return types. The rename was applied in api.hpp, api_exports.cpp (5 uses) and api_typed.inc (5 uses), and the gate is green"),
        "round": 742,
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
