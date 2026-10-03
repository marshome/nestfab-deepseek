# -*- coding: utf-8 -*-
"""Record the four-way contradiction about the nester base layout, so the next round starts from it.

**FOUR ROUNDS HAVE TRIED TO PLACE `Nester`'s base part and NONE HAS SETTLED IT.** The evidence pulled in three directions and this file states them together, because
each one alone looked decisive:

  * **`0xB4470` writes a vptr at +0x00, a pointer at +0x08, and two dwords at +0x10 and +0x14** -- five callers, and the ports of every nester.
  * **`lcns/include/lcns/base_chain.hpp` ALREADY SAYS `Multi::Nester` declares no data members** and that the fields belong to `CompositeNester`, whose typeinfo is
    `N5Multi15CompositeNesterE` -- **which would make `Nester` 0x08 bytes and put `0xB4470`'s +0x08 store... on `Nester` the class this file says is empty.**
  * **the direct `Nester` children put their first own member at +0x18** (`NestingNester`, asserted as `atSeedP == 0x18`), which fits a 0x10 base part and not a 0x08 one.
  * **and the module allocates 0x28 for `FlipNester`**, while `Nester` at 0x18 plus a `std::vector` at `CompositeNester`'s +0x18 is 0x30.

**SO EVERY READING CONTRADICTS ANOTHER, AND THIS ROUND IS NOT GOING TO PICK ONE.** What it can do is stop the contradiction from being carried in a declaration that
looks settled: the field's own comment now says the base is UNKNOWN and names the four pieces of evidence.
"""
import io
import os
import re
import sys

HEADER = r"D:\Nesting\nestfab\lcns\include\lcns\nester.hpp"

OLD = "    // **AND IT HAS THREE DATA MEMBERS, WHICH THIS DECLARATION DID NOT HAVE.** RE 0xB4470 is the base constructor; it has FIVE callers and its whole body is 29 bytes:"

NEW = """    // **THE BASE LAYOUT IS UNRESOLVED AFTER FOUR ROUNDS, AND THE FOUR PIECES OF EVIDENCE CONTRADICT EACH OTHER.** They are listed together here because each one
    // alone looked decisive, and a reader who sees only one of them will re-derive a different answer:
    //
    //   1. **`0xB4470` writes a vptr at +0x00, a POINTER at +0x08, and TWO DWORDS at +0x10 and +0x14.** Five callers, one per nester family.
    //   2. **`lcns/include/lcns/base_chain.hpp` ALREADY SAYS `Multi::Nester` declares no data members**, and that the fields belong to `CompositeNester`
    //      (`N5Multi15CompositeNesterE`, verified by walking `NoFillNester`'s typeinfo chain). **That makes `Nester` 0x08 -- and then `0xB4470`'s store at +0x08 is a
    //      store to the class base_chain.hpp says is empty.**
    //   3. **The direct `Nester` children put their first own member at +0x18**: `NestingNester` derives straight from `Nester` and the suite asserts
    //      `atSeedP == 0x18`. **That fits a 0x10 base part and not a 0x08 one.**
    //   4. **The module allocates 0x28 for `FlipNester`** (RE 0x2C953 `mov ecx, 0x28`), while `Nester` at 0x18 plus an 0x18 `std::vector` at `CompositeNester`'s +0x18
    //      is 0x30.
    //
    // **WHAT WOULD SETTLE IT IS A CLASS THAT DERIVES STRAIGHT FROM `Nester` AND READS +0x08, +0x10 OR +0x14 THROUGH ITS OWN OBJECT** -- that single instruction decides
    // which of the four readings survives. **`re/g_members_without_instructions.py` is where to look for it**, because it lists each class's constructor writes beside the
    // members declared for them.
    //
    // **AND THE FIELDS BELOW ARE THE DECLARATION AS IT STANDS, NOT A RESOLUTION**: they are what `0xB4470` writes, they make the model fit inside every module
    // allocation (`static_assert` in the suite), and **they are NOT established to be `Nester`'s rather than `CompositeNester`'s.**
    //
    // RE 0xB4470 is the constructor the whole family uses; it has FIVE callers and its body is 29 bytes:"""


def main(apply):
    text = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "THE BASE LAYOUT IS UNRESOLVED AFTER FOUR ROUNDS" in text:
        print("the note is already there")
        return 0
    if OLD not in text:
        print("REFUSING: the anchor is not where it is expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    if apply:
        io.open(HEADER, "w", encoding="utf-8", newline="\n").write(text)
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
