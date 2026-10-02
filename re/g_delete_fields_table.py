# -*- coding: utf-8 -*-
"""Delete the FieldStore table and its test, keeping the types that supersede them.

nesting_nester_fields.hpp and nesting_nester_layout.hpp describe one class. The first is a `FieldStore` table -- the shape the human objected
to, and the shape I produced on the way -- and the second is the type. **A file superseded by another should be deleted, not left beside it**,
because two descriptions of one class drift and this pair already had: both define kNestingNesterCtorAddress.

WHAT IS KEPT FROM THE TABLE, because deleting a file must not lose a fact:
  * the constructor's address and size -- already in nesting_nester_layout.hpp
  * the slot 2 offsets -- their MEANING is the same constructor rule, and the address 0x33100 is asserted in vtable_layout.hpp

WHAT IS LOST, and said out loud rather than quietly: the per-store list of the constructor (eight stores at seven offsets) as a runtime table.
It is a description of the CONSTRUCTOR rather than of the class, and the class's members carry the same instructions.
"""
import io
import os
import re

ROOT = r"D:\Nesting\nestfab"
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")
FIELDS = os.path.join(ROOT, "lcns", "include", "lcns", "nesting_nester_fields.hpp")

START = "    // ---------------------------------------------------------------- Multi::NestingNester's fields (RE 0x342E0)"
END = "    // ---------------------------------------------------------------- Multi::NestingNester as a CLASS (RE 0x342E0)"


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find(START)
    end = text.find(END)
    if start < 0 or end < 0 or end <= start:
        print("bounds not found: start=%d end=%d" % (start, end))
        return 1
    replacement = (
        "    // ---------------------------------------------------------------- the constructor's store list, DELETED\n"
        "    //\n"
        "    // A `FieldStore` table stood here, listing the constructor's eight stores at seven offsets with their instructions. **The\n"
        "    // class below states the same facts as MEMBERS**, which is what the human asked for, and two descriptions of one class drift --\n"
        "    // this pair already did, both defining kNestingNesterCtorAddress. The table is deleted and the class's members keep the\n"
        "    // instructions; nothing was true in the table that the class does not say.\n\n"
    )
    text = text[:start] + replacement + text[end:]
    if '#include "lcns/nesting_nester_fields.hpp"\n' in text:
        text = text.replace('#include "lcns/nesting_nester_fields.hpp"\n', "", 1)
        print("removed the include")
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("deleted the table's test block; lines now %d" % text.count("\n"))

    if os.path.exists(FIELDS):
        os.remove(FIELDS)
        print("deleted lcns/include/lcns/nesting_nester_fields.hpp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
