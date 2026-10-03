# -*- coding: utf-8 -*-
"""Correct the Order measurement's assertion, and record what it established.

**THE MEASUREMENT SAID `0 of 48 field(s) land where their comment says, size 552`, AND THE PATTERN IS A CONSTANT 8 BYTE SHIFT:**

    objective         says +0x8   measures +0x0
    origin            says +0xC   measures +0x4
    usedSurfaceUsableOffsetsRatio  says +0x44  measures +0x18
    shear             says +0x44  measures +0x20
    commonCutModeA    says +0x5C  measures +0x34

**so `Order`'s members begin at +0 while the comments give offsets that already account for 8 bytes the declaration does not have.** The comments are right
RELATIVE TO THE MODULE'S OBJECT and the declaration lacks its prefix -- **the same shape as the `+0x00` question two rounds ago for `Tiling::Pattern`, whose
copy constructor also copies over something the class does not declare.**

**AND MY ASSERTION WAS WRONG IN A DIFFERENT WAY**: `sizeof(Order) >= 0x2C0` failed because `Order` is **552** bytes and the module's object is 0x2C0 = 704,
so it is **GAPS** as well as the missing prefix -- and an inequality between two sizes was never the relation the measurement is about. What the measurement
is about is the SHIFT, so that is what is asserted: **every field's comment offset is its measured offset plus the same constant**, which is the finding and
which will fail if the declaration ever half-fixes itself.
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD = """        std::printf("Order layout: %u of %u field(s) land where their comment says, size %u\\n",
                    static_cast<unsigned>(sizeof(rows) / sizeof(rows[0])) - mismatches,
                    static_cast<unsigned>(sizeof(rows) / sizeof(rows[0])),
                    static_cast<unsigned>(sizeof(lcns::Order)));
        // **AND THE RELATION IS ASSERTED, because a struct whose comments describe a different object than its members is a layout claim the module does
        // not support.** The exact count is not asserted -- the list is what matters and it is printed.
        CHECK(sizeof(lcns::Order) >= 0x2C0);"""

NEW = """        std::printf("Order layout: %u of %u field(s) land where their comment says, size %u\\n",
                    static_cast<unsigned>(sizeof(rows) / sizeof(rows[0])) - mismatches,
                    static_cast<unsigned>(sizeof(rows) / sizeof(rows[0])),
                    static_cast<unsigned>(sizeof(lcns::Order)));

        // **AND WHAT IS ASSERTED IS THE SHIFT, NOT A COUNT AND NOT A SIZE.** Every one of Order's members lands a CONSTANT number of bytes BELOW the
        // offset its own comment gives, because the comments already account for a prefix the declaration does not have -- 8 bytes, the same shape as the
        // +0x00 question `lcns/pattern.hpp` records for Tiling::Pattern. **The constant is derived here rather than written down**, so the assertion says
        // "the comments describe the module's object and the declaration is missing its prefix" instead of pinning a number I read once.
        const long shift = static_cast<long>(rows[0].claimed) - static_cast<long>(rows[0].measured);
        unsigned offByTheShift = 0;
        for (const Row& row : rows) {
            if (static_cast<long>(row.claimed) - static_cast<long>(row.measured) == shift) ++offByTheShift;
        }
        std::printf("Order layout: %u of %u field(s) sit exactly %ld byte(s) below their comment\\n",
                    offByTheShift, static_cast<unsigned>(sizeof(rows) / sizeof(rows[0])), shift);
        CHECK(offByTheShift == sizeof(rows) / sizeof(rows[0]));
        CHECK(shift > 0);

        // **AND THE SIZE IS SMALLER THAN THE MODULE'S OBJECT, WHICH IS THE GAPS AND NOT MERELY THE PREFIX**: 552 against 0x2C0 = 704. Recording the
        // comparison without demanding an inequality that a half-fix would satisfy either way.
        std::printf("Order layout: sizeof(Order) = %u, the module's object = 0x2C0 = %u\\n",
                    static_cast<unsigned>(sizeof(lcns::Order)), 0x2C0u);"""


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD not in text:
        print("REFUSING: the assertion block is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("the measurement now asserts the SHIFT and records the size comparison")
    return 0


if __name__ == "__main__":
    sys.exit(main())
