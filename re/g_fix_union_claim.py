# -*- coding: utf-8 -*-
"""Correct the union claim's numbers, which the padding fix changed, and record WHY they moved.

**THE NUMBERS WERE INFLATED BY THE TOOL'S OWN SCAFFOLDING.** The claim said 68 shared offsets, 60 only in the layout and 15 only in `Order`; with the padding
excluded the measurement says

    54 shared offsets
    73 that only the layout has, and 62 of those carry an unnamedXXX name
    2 that only Order has

**and the 13 that vanished from "only Order" were `std::byte paddingNN` members the permutation inserts**, whose `+0xNNN` comments the field regex matched -- so
the tool was reporting its own padding as the module's structure. **The layout side moved UP because padding on `Order`'s side had been occupying offsets the
layout also describes**, which made those offsets look shared when one side was scaffolding.

**A WRONG NUMBER IS WORSE THAN A MISSING ONE**, so the claim is replaced rather than left standing with a note.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")
SUBJECT = "the-Order-duplication-division"

REPLACEMENT = {
    "grade": "MEASURED",
    "kind": "offset",
    "predicate": ("of the two placed layouts of the module's object, 54 offsets are shared, 73 exist only in LaunchingOrderLayout and 62 of those carry an "
                  "unnamedXXX name, and 2 exist only in Order"),
    "round": 715,
    "subject": "the-Order-duplication-division",
    "witness": ("re/g_order_union.py and re/g_one_definition.py now agree field for field after both were given the same two rules: the offset comment must be "
                "on the same line, and a `paddingNN` member is not a field. The padding rule was the correction -- 13 of the earlier \"15 offsets only Order "
                "has\" were std::byte padding the permutation inserts, whose +0xNNN comments the regex matched"),
}


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    claims = data["claims"]
    before = len(claims)
    kept = [c for c in claims if c.get("subject") != SUBJECT]
    print("removed %d claim(s) with the inflated numbers" % (before - len(kept)))
    kept.append(REPLACEMENT)
    data["claims"] = kept
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("replaced with the corrected division; %d claims" % len(kept))
    return 0


if __name__ == "__main__":
    sys.exit(main())
