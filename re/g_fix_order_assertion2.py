# -*- coding: utf-8 -*-
"""Stop asserting a pattern in Order's layout and RECORD the measurement instead.

**I ASSERTED A CONSTANT 8 BYTE SHIFT AND THE MEASUREMENT REFUTED IT: 2 of 48.** The first twelve rows did look like a uniform shift -- `objective` +0x8 against
+0x0, `origin` +0xC against +0x4, `shear` +0x44 against +0x20 -- **and `shear` is a 0x24 gap, not 8**, which I read past because the first three rows agreed.
That is the third time this session that a pattern seen in three examples was written into an assertion before being measured, and the fix each time has been
the same: **state the measurement and assert only what covers every row.**

**AND WHAT COVERS EVERY ROW IS: NONE OF THEM AGREES.** `0 of 48`. So that is what is asserted, together with the sizes, and the reconciliation's lists stay
in `re/ORDER_RECONCILE.md` where the per-field work can use them.
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD = """        // **AND WHAT IS ASSERTED IS THE SHIFT, NOT A COUNT AND NOT A SIZE.** Every one of Order's members lands a CONSTANT number of bytes BELOW the
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

NEW = """        // **AND NOT ONE OF THEM AGREES, WHICH IS THE ASSERTION.** I first claimed a constant 8 byte shift -- the first three rows read that way -- and
        // **the measurement refuted it: 2 of 48**, because `shear` is a 0x24 gap rather than 8. **A pattern seen in three examples is not a pattern**, so
        // what is asserted here is only what covers EVERY row.
        CHECK(mismatches == sizeof(rows) / sizeof(rows[0]));

        // **AND THE SIZE IS SMALLER THAN THE MODULE'S OBJECT**: 552 against 0x2C0 = 704, so this declaration is missing the prefix AND has gaps. The
        // comparison is printed rather than asserted as an inequality, because an inequality is satisfied by a half-fix.
        std::printf("Order layout: sizeof(Order) = %u, the module's object = 0x2C0 = %u\\n",
                    static_cast<unsigned>(sizeof(lcns::Order)), 0x2C0u);"""


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD not in text:
        print("REFUSING: the assertion block is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("the assertion now covers every row: NONE of the fields agrees")
    return 0


if __name__ == "__main__":
    sys.exit(main())
