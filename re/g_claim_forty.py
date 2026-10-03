# -*- coding: utf-8 -*-
"""Record this round's claim: 31 more exports wired, and the counts that agree."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIM = {
    "subject": "forty-exports-dispatch",
    "grade": "CONSTRUCTION",
    "kind": "call",
    "predicate": ("40 of the 168 export wrappers call a recovered implementation and 128 still report their ordinal, and the 40 are 40 of the 47 kForwarding "
                  "ordinals with 7 refused on an arity mismatch"),
    "witness": ("re/g_forwarding_gap.py joins kForwarding to api_exports.cpp's wrappers and reports 40 dispatching and 7 not, and re/g_export_status.py counts the "
                "call shape `exports::impl::<name>(` and the `notReversed(` stubs, which sum to 168. All 31 rewrites this round used the argument registers read "
                "by re/g_forwarding_signatures.py, and the build passes with 0 warnings after the return types and parameter types were taken from the "
                "implementations' declarations rather than from the inferred table"),
    "round": 736,
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
