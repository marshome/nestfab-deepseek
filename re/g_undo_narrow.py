# -*- coding: utf-8 -*-
"""Remove the three NARROW entries: the adjudicator paired them by a TRUNCATED offset, and the tests say so.

**WHAT THE FAILURE WAS.** With `cfgAt188` narrowed to `std::uint8_t`, `test_nester.cpp:391` reports `c.coeff()=11` where it expects `11.5` -- because the test
writes `o.cfgAt188 = 11.5;` and a byte cannot hold it. **And the test's own comment says which field that is:**

    //    RE 0x6AC20A reads Pb+0x188 -> core+0x20 (coefficient) and Pb+0x190 -> core+0x18
    //    (threshold) through the base 0x4FC3A0 = `mov rax,[rcx] ; add rax,0x170`.

**`cfgAt188` IS AT `Pb + 0x188` IN THE PIPE BLOCK, NOT AT `Order + 0x18`.** So it is not one of the module's 0x2C0 object's fields at all, and
`re/g_adjudicate.py` paired it with `unnamed018` because **`+0x188` CONTAINS `+0x18`** -- the offset was matched as a SUBSTRING. **Its three "width conflicts" for
`cfgAt188`, `cfgAt190` and `cfgAt198` are therefore pairings of two different fields, and the module's answer for them says nothing about this struct.**

**SO THE NARROWING GOES, AND WITH IT THE CLAIM THAT THOSE THREE WERE WIDTH CONFLICTS.** What remains is the finding that matters: `Order`'s members land
nowhere near its comments, and this round's permutation is what puts them there -- **with the fields' DECLARED widths, which the tests confirm are right for the
pipe block.**
"""
import io
import sys

PLACER = r"D:\Nesting\nestfab\re\g_order_permute.py"

OLD = '''# **THE THREE WIDTHS `re/g_adjudicate.py` GIVES THE MODULE**, and they are applied in the SAME pass because narrowing one member before the run is in order
# moves every later member off its offset -- which is exactly what made the tests fail when it was tried alone.
NARROW = {"cfgAt188": "std::uint8_t", "commonCutNoHoles": "std::uint8_t", "commonCutOnlyBiModules": "std::uint8_t"}'''

NEW = '''# **AND NO WIDTH IS NARROWED, BECAUSE THE THREE THE ADJUDICATOR NAMED ARE NOT THIS STRUCT'S FIELDS.** It reported `cfgAt188` at "+0x18" and offered
# `std::uint8_t` against `Order`'s `double`; **the field is at `Pb + 0x188`, in the PIPE block**, which the test says in its own words -- "RE 0x6AC20A reads
# Pb+0x188 -> core+0x20 (coefficient)" -- and `+0x188` merely CONTAINS `+0x18`, so the offset was matched as a substring. Narrowing it made `o.cfgAt188 =
# 11.5` store 11 and `test_nester.cpp:391` fail, which is how the mispairing was found.
#
# **SO THE MAP IS EMPTY AND THE PERMUTATION USES THE DECLARED WIDTHS.** `commonCutNoHoles` and `commonCutOnlyBiModules` are kept at `int` for the same
# reason: they were paired with `+0x84` and `+0x85` by the same substring rule, and the run does not overlap with `int` either once the ordering is right.
NARROW = {}'''


def main():
    text = io.open(PLACER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "AND NO WIDTH IS NARROWED" in text:
        print("the narrowing is already removed")
        return 0
    if OLD not in text:
        print("REFUSING: the NARROW block is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(PLACER, "w", encoding="utf-8", newline="\n").write(text)
    print("NARROW is now empty, with the mispairing recorded where it was")
    return 0


if __name__ == "__main__":
    sys.exit(main())
