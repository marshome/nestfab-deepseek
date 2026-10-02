# -*- coding: utf-8 -*-
"""Correct the evaluator annotations: slot 3 is NOT `evaluate`, and the class-level note said so of six classes.

**THE ANNOTATION I ADDED LAST ROUND SAID "slot 3 is `evaluate()` -- the BASE's own implementation" FOR EACH OF SIX CLASSES, AND THAT IS WRONG.** Reading
0x4E7E50 -- the address all six share -- shows it copies 0x60 bytes and then DEEP COPIES A CONTAINER with 0x90 byte elements, calling an allocator and
a per-element copy routine:

    0x4E7E5F  mov rax, [r8]        ...  0x4E7EE6  through [r8 + 0x58] into [rcx]      ; 0x60 bytes copied
    0x4E7F01  call 0x998500                                                          ; the allocator
    0x4E7F41  call 0x63F2F8                                                          ; one call per element
    0x4E7F49  add rbx, 0x90                                                          ; THE ELEMENT STRIDE

**so it is a copy constructor or a clone, not a scoring function.** The element stride 0x90 matches the container `Tiling::Pattern` is recorded with.

**AND WHAT SLOT 3 ACTUALLY IS BELONGS TO THE MODULE, NOT TO A GUESS**, so the annotations now say what is measured -- the address, its size, and
whether it is shared -- and stop naming the method. **A name that has not been established is the placeholder this whole session has been removing.**
"""
import io
import re
import sys

TILING = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"

# class -> (vtable, destructor, slot2, slot3)
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


def main():
    text = io.open(TILING, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    changed = 0
    for name, (vtable, destructor, slot2, slot3) in TABLE.items():
        # find the single-line annotation this project's earlier tool wrote
        pattern = re.compile(r"/\*\* RE vtable %s, FOUR slots[^\n]*\*/\n" % re.escape(vtable))
        match = pattern.search(text)
        if not match:
            continue
        shared = slot3 == "0x4E7E50"
        note = ("/** RE vtable %s, FOUR slots. Slot 0 is the deleting destructor %s, slot 1 the destructor, slot 2 is at %s (81 to 798 bytes) and\n"
                " *  slot 3 is at %s%s.\n"
                " *  **SLOT 3 IS NOT NAMED HERE ON PURPOSE.** In six of the eight evaluators it is the SAME address, 0x4E7E50, and reading that routine\n"
                " *  shows a 0x60 byte copy followed by a DEEP COPY of a container with 0x90 byte elements -- a copy constructor or a clone, NOT a\n"
                " *  scoring function. An earlier annotation called it `evaluate()`; **what slot 3 is has not been established**, and a name guessed at\n"
                " *  from a shape is the placeholder this project removes. */\n"
                % (vtable, destructor, slot2, slot3,
                   " -- SHARED with five other evaluators" if shared else " -- this class's own"))
        text = text[:match.start()] + note + text[match.end():]
        changed += 1

    # and the class-level note about the base
    text = text.replace(
        " *      slot 3, 0x4E7E50 in SIX of the eight    `evaluate()` -- **THE BASE'S OWN IMPLEMENTATION**, 539 bytes",
        " *      slot 3, 0x4E7E50 in SIX of the eight    **SHARED, AND ITS NAME IS NOT ESTABLISHED** -- see the per-class notes below")
    text = text.replace(
        " *  `ObliqueEvaluator` overrides slot 3 with 0x7E8970 and `QuantityEvaluator` with 0x7E8DA0, so **a slot address shared by several derived tables is\n"
        " *  the base's and one that differs is the override.** */",
        " *  `ObliqueEvaluator` uses 0x7E8970 at slot 3 and `QuantityEvaluator` 0x7E8DA0, so the address is NOT the same in all eight. **A slot address\n"
        " *  shared by several derived tables is one implementation and one that differs is another**, and which of them is `evaluate` is not settled by\n"
        " *  the sharing alone. */")

    io.open(TILING, "w", encoding="utf-8", newline="\n").write(text)
    print("corrected %d evaluator annotation(s) and the class-level note" % changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
