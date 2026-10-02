# -*- coding: utf-8 -*-
"""Correct the compare-path expectations: with a zero-initialised box, an element only LOWERS a low if it is below zero.

The previous version of this test asserted that folding (5, 7, 9, 4) into an empty box gives lows of 5 and 4. It does not, and the
instructions say why: 0x5C8C73 is `ucomisd xmm1, xmm0` -- the BOX against the ELEMENT -- with `jbe` skipping the store, so the store
happens only when the element is BELOW the box's current low, which for a fresh box is zero.

**THAT IS EXACTLY WHY 0x5C8D10's BUILD PATH EXISTS**: a fresh box has no useful lows, so the first element is installed rather than
compared, and only afterwards are elements compared. The test now exercises that order, which is what the module does.
"""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD = '''        // the compare path: all four values meet the box
        lcns::StatBox box;
        box.fold(true, 5.0, 7.0, 9.0, 4.0);
        CHECK(box.valid == 0);                             // untouched: the compare path never sets it
        CHECK(box.low0 == 5.0 && box.high0 == 9.0);        // a=5 lowered nothing, c=9 raised the high
        CHECK(box.low1 == 4.0 && box.high1 == 7.0);        // b=7 set the high, d=4 lowered the low
'''

NEW = '''        // the compare path against a ZERO box, which only lowers a low when the element is BELOW ZERO -- 0x5C8C73 is `ucomisd` of
        // the box against the element with `jbe` skipping the store. **This is why the build path exists**: a fresh box has no useful
        // lows, so the first element is installed rather than compared.
        lcns::StatBox zeroed;
        zeroed.fold(true, 5.0, 7.0, 9.0, 4.0);
        CHECK(zeroed.valid == 0);                          // the compare path never touches the flag
        CHECK(zeroed.low0 == 0.0);                         // 5 and 9 are both above zero, so the low stays
        CHECK(zeroed.high0 == 9.0);                        // and c=9 raised the high
        CHECK(zeroed.low1 == 0.0);                         // same for the second axis
        CHECK(zeroed.high1 == 7.0);                        // b=7

        // and a NEGATIVE element does lower the low, which is the comparison the jbe skips over
        lcns::StatBox negative;
        negative.fold(true, -5.0, -7.0, 1.0, -2.0);
        CHECK(negative.low0 == -5.0);                      // a=-5 is below zero, so it lands
        CHECK(negative.low1 == -7.0);                      // b=-7 likewise
        CHECK(negative.high0 == 1.0);                      // c=1 raised the high
        CHECK(negative.high1 == 0.0);                      // d=-2 is below zero, so the high stays 0
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD not in text:
        print("anchor not found")
        return 1
    text = text.replace(OLD, NEW, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("corrected the compare-path expectations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
