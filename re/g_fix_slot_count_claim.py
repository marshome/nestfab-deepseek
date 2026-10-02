# -*- coding: utf-8 -*-
"""Replace the WRONG ledger claim about MultiOrientedPartPattern's slot count with the correction.

THE CLAIM I ADDED LAST ROUND WAS FALSE: "re/vtables.json records 5 slots for Tiling::MultiOrientedPartPattern and the live vtable at 0xA3D370 has
8". **The JSON records 8.** I had read the wrong address -- 0xA3D310, which is some other class -- and written down a discrepancy that did not
exist.

**A WRONG CLAIM IS WORSE THAN A MISSING ONE**, which is this project's own rule, so the claim is REPLACED rather than deleted or left standing:
the replacement records the mistake, the reading that settles it, and what the true count is.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")
OLD_SUBJECT = "slot-counts-disagree-in-one-place"

REPLACEMENT = {
    "grade": "INSTRUCTION",
    "kind": "offset",
    "predicate": ("re/vtables.json records EIGHT slots for Tiling::MultiOrientedPartPattern and the live vtable at 0xA3D370 has eight; "
                  "an earlier claim of five was MY misreading of a different address"),
    "round": 692,
    "subject": "MultiOrientedPartPattern.slot-count-is-eight",
    "witness": ("dumping 0xA3D370 gives a NULL at +0, the typeinfo at +8 and slots at +0x10 through +0x48; the JSON's vtable_rva is 0xA3D370 "
                "with slots 0x76F9D0, 0x76F9C0, 0x7EBB90, 0x7EB5E0, 0x7EBC30, 0x7EB990, 0x7EBDB0 and 0x7EBD90, which match the dump one for "
                "one. The false claim came from reading 0xA3D310"),
}


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    claims = data["claims"] if isinstance(data, dict) and "claims" in data else data
    before = len(claims)
    kept = [c for c in claims if c.get("subject") != OLD_SUBJECT]
    if len(kept) == before:
        print("the false claim is not present, so there is nothing to replace")
    else:
        print("removed the false claim %s" % OLD_SUBJECT)
    kept.append(REPLACEMENT)
    if isinstance(data, dict) and "claims" in data:
        data["claims"] = kept
        out = data
    else:
        out = kept
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print("added %s in its place; %d claims" % (REPLACEMENT["subject"], len(kept)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
