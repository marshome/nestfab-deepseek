# -*- coding: utf-8 -*-
"""Record each corrected class's VTABLE ADDRESS and SLOT COUNT beside it, and derive the evaluators from their real base.

**WHY THE ADDRESS BELONGS BESIDE THE CLASS.** I once read 0xA3D310 -- which is `Tiling::MultitorchEvaluator` -- and reported a slot-count discrepancy
about `Tiling::MultiOrientedPartPattern` at 0xA3D370. **Adjacent tables in one RTTI region are different classes**, and the address is the only thing
that tells them apart.

THE MEASURED TABLES, from re/g_class_tables.py:

    Tiling::DensityEvaluator            0xA3D210   4 slots   0x76E390 0x76E380 0x7E8910 0x4E7E50
    Tiling::ObliqueEvaluator            0xA3D240   4 slots   0x76E3D0 0x76E3A0 0x7E8B30 0x7E8970
    Tiling::QuantityEvaluator           0xA3D270   4 slots   0x76E410 0x76E400 0x7E8DD0 0x7E8DA0
    Tiling::ReusableEvaluator           0xA3D2A0   4 slots   0x76E430 0x76E420 0x7E8F60 0x4E7E50
    Tiling::MultitorchEvaluator         0xA3D310   4 slots   0x76F260 0x76F250 0x7E9240 0x4E7E50
    Tiling::OldMultitorchEvaluator      0xA3D340   4 slots   0x76F9B0 0x76F9A0 0x7EB320 0x4E7E50
    Tiling::UnlimitedDensityEvaluator   0xA3D3C0   4 slots   0x76F9F0 0x76F9E0 0x7EBFC0 0x4E7E50
    Tiling::UnlimitedXDensityEvaluator  0xA3D3F0   4 slots   0x76FA10 0x76FA00 0x7EC210 0x4E7E50

**AND SLOT 3 IS THE BASE'S OWN IMPLEMENTATION IN SIX OF THE EIGHT** -- the same address 0x4E7E50, 539 bytes. `ObliqueEvaluator` overrides it with
0x7E8970 and `QuantityEvaluator` with 0x7E8DA0, and **a slot that differs is the derived class's override while a slot that is shared is the base's**.

    Engine::CloudEngine       0xA3CED0   3 slots      Engine::MultiEngine      0xA3CF00   3 slots
    Engine::DelayedEngine     0xA3CF70   3 slots      Engine::NestingEngine    0xA3CFA0   3 slots
    Engine::InfiniteEngine    0xA3CFD0   3 slots      Engine::CompositeEngine  0xA3D000   3 slots
    Engine::EquivalentEngine  0xA3D030   3 slots
"""
import io
import re
import sys

TILING = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"

# the evaluator classes and their measured tables, as their declarations are found
TABLE = {
    "DensityEvaluator": ("0xA3D210", "0x76E390", "0x7E8910", "0x4E7E50"),
    "ObliqueEvaluator": ("0xA3D240", "0x76E3D0", "0x7E8B30", "0x7E8970"),
    "QuantityEvaluator": ("0xA3D270", "0x76E410", "0x7E8DD0", "0x7E8DA0"),
    "ReusableEvaluator": ("0xA3D2A0", "0x76E430", "0x7E8F60", "0x4E7E50"),
    "MultitorchEvaluator": ("0xA3D310", "0x76F260", "0x7E9240", "0x4E7E50"),
    "OldMultitorchEvaluator": ("0xA3D340", "0x76F9B0", "0x7EB320", "0x4E7E50"),
    "UnlimitedDensityEvaluator": ("0xA3D3C0", "0x76F9F0", "0x7EBFC0", "0x4E7E50"),
    "UnlimitedXDensityEvaluator": ("0xA3D3F0", "0x76FA10", "0x7EC210", "0x4E7E50"),
}

EVALUATOR = '''/** **RE the eight tables below, and IT IS A BASE WITH THREE VIRTUALS.** Every instantiated derived class has FOUR slots:
 *
 *      0x76E380..0x76FA00   the deleting destructor, 1 or 5 bytes, one per class
 *      0x76E390..0x76FA10   the destructor, one per class
 *      slot 2, varying       `name()`
 *      slot 3, 0x4E7E50 in SIX of the eight    `evaluate()` -- **THE BASE'S OWN IMPLEMENTATION**, 539 bytes
 *
 *  `ObliqueEvaluator` overrides slot 3 with 0x7E8970 and `QuantityEvaluator` with 0x7E8DA0, so **a slot address shared by several derived tables is
 *  the base's and one that differs is the override.** */
class Evaluator {
public:
    virtual ~Evaluator() = default;
    virtual const char* name() const = 0;
    virtual double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const = 0;
};
'''


def main():
    text = io.open(TILING, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    changed = 0
    for name, (vtable, destructor, slot2, slot3) in TABLE.items():
        # put the measured table in the class's OWN comment, without disturbing anything else
        pattern = re.compile(r"(class %s\b[^\n]*\n(?:public:\n)?)" % re.escape(name))
        match = pattern.search(text)
        if not match:
            print("   %-30s not found in the header" % name)
            continue
        if ("vtable 0x" + vtable[2:]) in text[max(0, match.start() - 500):match.start()]:
            continue
        note = ("    /** RE vtable 0x%s, FOUR slots: 0x%s and the destructor pair, slot 2 is `name()` at 0x%s, slot 3 is `evaluate()` at 0x%s%s. */\n"
                % (vtable, destructor, slot2, slot3,
                   " -- the BASE's own implementation" if slot3 == "0x4E7E50" else " -- an OVERRIDE"))
        text = text[:match.start()] + note + text[match.start():]
        changed += 1

    if "RE the eight tables below" in text:
        print("the Evaluator comment is already present")
    else:
        old = """class Evaluator {
public:
    virtual ~Evaluator() = default;
    virtual const char* name() const = 0;
    virtual double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const = 0;
};
"""
        if old not in text:
            print("REFUSING: the Evaluator declaration is not as expected")
            return 2
        text = text.replace(old, EVALUATOR, 1)
        changed += 1

    io.open(TILING, "w", encoding="utf-8", newline="\n").write(text)
    print("annotated %d evaluator class(es) with their measured tables" % changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
