# -*- coding: utf-8 -*-
"""Make the evaluator base's note consistent: FOUR slots, TWO virtuals beyond the destructors, and NEITHER slot named.

The note said "A BASE WITH THREE VIRTUALS" and then listed FOUR slots, and it named slot 2 `name()` -- which is not established either. **The point of
this round is that a name guessed from a shape is the placeholder this project removes**, so the note stops naming both slots and says what the
sharing does and does not settle.
"""
import io
import re
import sys

TILING = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"

NEW = '''/** **RE the eight tables below, and EVERY ONE HAS FOUR SLOTS** -- which is TWO VIRTUALS beyond the destructor pair:
 *
 *      0x76E380..0x76FA00   the deleting destructor, 1 or 5 bytes, one per class
 *      0x76E390..0x76FA10   the destructor, one per class
 *      slot 2, POSITIVE IN EVERY CLASS, and which method it is has NOT been established
 *      slot 3, 0x4E7E50 in SIX of the eight       **SHARED, AND ITS NAME IS NOT ESTABLISHED EITHER**
 *
 *  `ObliqueEvaluator` uses 0x7E8970 at slot 3 and `QuantityEvaluator` 0x7E8DA0, so the address differs in two of the eight.
 *
 *  **AND THE SHARING DOES NOT SETTLE WHICH SLOT IS WHICH.** In six of the eight, slot 3 is a routine that copies 0x60 bytes from its argument and
 *  then DEEP COPIES a container of 0x90 byte elements, calling the allocator and a per-element copy -- **a copy constructor or a clone, and not a
 *  scoring function**. So neither slot is named here: `name()` and `evaluate()` are this project's own words for them, arrived at before these
 *  tables were measured, and an earlier note presented them as if the table had said so. **A name guessed from a shape is the placeholder this
 *  project removes.** */
'''


def main():
    text = io.open(TILING, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find("/** **RE the eight tables below")
    if start < 0:
        print("REFUSING: the note is not found")
        return 2
    end = text.find("*/", start)
    if end < 0:
        print("REFUSING: the note has no end")
        return 2
    text = text[:start] + NEW.rstrip("\n") + text[end + 2:]
    io.open(TILING, "w", encoding="utf-8", newline="\n").write(text)
    print("the evaluator base's note now says FOUR slots and names neither")
    return 0


if __name__ == "__main__":
    sys.exit(main())
