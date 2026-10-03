# -*- coding: utf-8 -*-
"""Point the three nesters at `CompositeNester`, which the typeinfo says is their base.

**THE TYPEINFO IS THE ORACLE AND IT DISAGREES WITH THREE DECLARATIONS:**

    FlipNester        typeinfo base N5Multi15CompositeNesterE   declared : public Nester
    FilterNester      typeinfo base N5Multi15CompositeNesterE   declared : public Nester
    MultiTorchNester  typeinfo base N5Multi15CompositeNesterE   declared : public Nester

**AND EACH ONE'S CONSTRUCTOR CALLS `0xB4DA0`, WHICH IS `CompositeNester`'S** -- it is the function that writes the `std::vector`'s storage pointer at +0x18. **So the
declarations put every field of these three 0x10 too low, exactly as `LimitedNester` was.**

**AND THE OFFSETS THEY WRITE CONFIRM WHICH MEMBERS ARE THE BASE'S**: `FlipNester` writes a BYTE at +0x20 and another at +0x21 (`0x4B59B`, `0x4B5AE`); +0x20 is the
vector's end pointer, **so a byte write there is the class touching its own base's vector slot and not a member of its own** -- which is why the members move and the
comments say so rather than silently changing.
"""
import io
import os
import sys

HEADER = r"D:\Nesting\nestfab\lcns\include\lcns\nester.hpp"

EDITS = [
    ("class FlipNester : public Nester {",
     "// **IT DERIVES FROM `CompositeNester`, NOT FROM `Nester`**: its typeinfo (vtable 0xA3B4A0) names `N5Multi10FlipNesterE` and its base is `N5Multi15CompositeNesterE`,\n"
     "// and its constructor 0x4B570 calls 0xB4DA0 -- `CompositeNester`'s -- which is the function that writes the vector's storage pointer at +0x18. **So the two bytes it\n"
     "// writes at +0x20 and +0x21 (`0x4B59B`, `0x4B5AE`) land in the base's vector slot region and NOT in members of its own.**\n"
     "class FlipNester : public CompositeNester {"),
    ("class FilterNester : public Nester {",
     "// **IT DERIVES FROM `CompositeNester`, NOT FROM `Nester`**: vtable 0xA3B500, typeinfo `N5Multi12FilterNesterE`, base `N5Multi15CompositeNesterE`, and its\n"
     "// constructor 0xB3A70 calls 0xB4DA0. **AND THAT CORRECTS TWO COMMENTS THAT WERE WRONG ABOUT WHOSE FIELDS THEY ARE**: `inner_` was described as \"the object at\n"
     "// +0x18\", and +0x18 is `CompositeNester::children_`'s begin pointer -- an interior object and a vector are not the same claim; and `seed_` was placed at +0x10,\n"
     "// **which is `Nester::at10`, written by 0xB447E to 0x1869F and not by a seed store.**\n"
     "class FilterNester : public CompositeNester {"),
    ("class MultiTorchNester : public Nester {",
     "// **IT DERIVES FROM `CompositeNester`, NOT FROM `Nester`**: vtable 0xA3B8B0, typeinfo `N5Multi16MultiTorchNesterE`, base `N5Multi15CompositeNesterE`, and its\n"
     "// constructor 0x780E0 calls 0xB4DA0 and then writes at +0x20 -- the base's vector end slot -- before its own members.\n"
     "class MultiTorchNester : public CompositeNester {"),
]


def main(apply):
    text = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    done = 0
    for old, new in EDITS:
        if new in text:
            print("   already corrected: %s" % old[:44])
            continue
        if old not in text:
            print("   REFUSING: anchor not found: %s" % old[:60])
            return 2
        text = text.replace(old, new, 1)
        print("   corrected: %s" % old[:60])
        done += 1
    if apply and done:
        io.open(HEADER, "w", encoding="utf-8", newline="\n").write(text)
        print("%d declaration(s) written" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
