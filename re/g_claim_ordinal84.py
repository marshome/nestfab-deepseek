# -*- coding: utf-8 -*-
"""Add the ordinal-84 wiring claim, with the quoting done in Python rather than in a shell."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIM = {
    "subject": "ordinal-84-is-wired",
    "grade": "INSTRUCTION",
    "kind": "call",
    "predicate": ("SetLocalMaximumIterations, ordinal 84 at rva 0x0D400, is wired end to end: its wrapper calls impl::setLocalMaximumIterations, which stores a "
                  "32-bit value at +0x1FC with no clamp"),
    "witness": ("the wrapper was `extern \"C\" void SetLocalMaximumIterations(Order, int)`, taking the Order BY VALUE, while 0x0D406 is `mov rsi, rcx` and 0x0D417 "
                "is `mov dword [rsi + 0x1fc], ebx` -- writes THROUGH it; re/exports_table.md counts 2 register arguments; the implementation was named `setInt_1FC` "
                "and kForwarding named it at ordinal 84, so it was renamed to the module's own export name. re/g_forwarding_gap.py no longer lists ordinal 84 among "
                "the forwarded ordinals whose wrapper does not dispatch"),
    "round": 733,
}


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    if any(c.get("subject") == CLAIM["subject"] for c in data["claims"]):
        print("the claim is already there")
        return 0
    data["claims"].append(CLAIM)
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("added %s; %d claims" % (CLAIM["subject"], len(data["claims"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
