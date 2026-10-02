# -*- coding: utf-8 -*-
"""Wire Tiling::Pattern as the base of BiModulePattern and MultiOrientedPartPattern, which the module's RTTI establishes.

**THE DERIVATION IS IN THE MODULE AND WAS ABSENT FROM THE TREE.** The typeinfo chains are

    N6Tiling15BiModulePatternE          -> N6Tiling7PatternE
    N6Tiling21MultiOrientedPartPatternE -> N6Tiling7PatternE

read from the +0x10 pointer of each class's own typeinfo, so both derive from `Tiling::Pattern` -- **and neither declaration said so**, because
`Tiling::Pattern` did not exist here until two rounds ago.

**AND THE MEASUREMENT I MADE THAT DID NOT FIT IS EXPLAINED BY THE ORDER OF THE BASES.** `pattern.hpp` records that a derived instance's own first member
lands at +8 while `Tiling::Pattern` is one word, so **something occupies +0x00**. For `BiModulePattern` the constructors show a `std::shared_ptr` being
written to the caller's 2 word object, and `MultiOrientedPartPattern` does the same -- **so a pattern is held BY `shared_ptr` and the module's classes are
used through it**, which is the same relationship every other handle in this tree has and which the copy constructor at 0x4E7E50 copies over.

**I AM NOT DECLARING THAT SUBOBJECT HERE.** The evidence for the base CLASS is the typeinfo chain and it is used; the evidence for what precedes `Pattern`
in the LAYOUT is a one-word measurement and a constructor that writes a `shared_ptr` into a CALLER's slot, and those two do not yet agree on which object
holds what. **The class is wired and the layout question stays open**, which is the distinction this project draws.
"""
import io
import sys

TILING = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"

INCLUDE_OLD = '#include "lcns/geom.hpp"\n#include "lcns/model.hpp"'
INCLUDE_NEW = '#include "lcns/geom.hpp"\n#include "lcns/model.hpp"\n#include "lcns/pattern.hpp"'

BASE_NOTE = '''
// ---------------------------------------------------------------------------
// the two pattern classes -- **BOTH DERIVE FROM `Tiling::Pattern`**, by the typeinfo chains
// N6Tiling15BiModulePatternE -> N6Tiling7PatternE and N6Tiling21MultiOrientedPartPatternE -> N6Tiling7PatternE.
//
// **AND THAT DERIVATION WAS ABSENT FROM THIS TREE UNTIL `lcns/pattern.hpp` EXISTED**, because the base is abstract and therefore not a key in
// `re/vtables.json` -- so nothing here had noticed it. `Tiling::Pattern`'s own measured facts, including the copy constructor at 0x4E7E50 that SIX OF THE
// EIGHT EVALUATORS carry at vtable slot 3, are in that header.
//
// **WHAT IS STILL OPEN**: `sizeof(Tiling::Pattern)` measured ONE WORD while a derived instance's own first member landed at +8, so SOMETHING OCCUPIES
// +0x00 that the base does not have. The constructors write a `std::shared_ptr` into a CALLER-owned 2 word object, which is a fact about the CALL rather
// than about the layout, and the two do not yet agree on which object holds what. **Recorded, not resolved.**
// ---------------------------------------------------------------------------
'''


def main():
    text = io.open(TILING, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "lcns/pattern.hpp" in text:
        print("tiling.hpp already includes pattern.hpp")
    else:
        if INCLUDE_OLD not in text:
            print("REFUSING: the include block is not as expected")
            return 2
        text = text.replace(INCLUDE_OLD, INCLUDE_NEW, 1)
        print("tiling.hpp includes pattern.hpp")

    for short, full in (("BiModulePattern", "N6Tiling15BiModulePatternE"),
                        ("MultiOrientedPartPattern", "N6Tiling21MultiOrientedPartPatternE")):
        old = "class %s {" % short
        new = "class %s : public Pattern {" % short
        if new in text:
            print("   %s already derives" % short)
            continue
        index = text.find(old)
        if index < 0:
            print("   %s not found" % short)
            continue
        # put the base note above the first of the two, once
        if BASE_NOTE.strip() not in text:
            text = text[:index] + BASE_NOTE + text[index:]
            index = text.find(old)
        text = text[:index] + new + text[index + len(old):]
        print("   %s now derives from Pattern" % short)

    io.open(TILING, "w", encoding="utf-8", newline="\n").write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
