# -*- coding: utf-8 -*-
"""Extend the variant test with the extent step, which the header previously left as a comment."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD = '''        // an invalid box returns zero, which is the routine jumping past BOTH multiplies
        CHECK(lcns::variantScale(false, 10.0, 1.0, 0.5) == 0.0);'''

NEW = '''        // THE COMPLETE RULE, which the header previously carried only as the multiplication. RE 0x132E0 fills a box at rsp+0x50 and
        // takes high - low per axis -- [rsp+0x70]-[rsp+0x60] for the second and [rsp+0x68]-[rsp+0x58] for the first -- then scales the
        // larger. The box's offsets are StatBox's, so one representation is shared with the stat accumulator.
        {
            lcns::StatBox box;
            CHECK(box.valid == 0);
            CHECK(lcns::variantScaleOfBox(box) == 0.0);        // RE 0x13327: an invalid box scales nothing

            box.valid = 1;
            box.low0 = 2.0;  box.high0 = 9.0;                   // the first axis: extent 7
            box.low1 = 0.0;  box.high1 = 3.0;                   // the second: extent 3
            CHECK(box.high0 - box.low0 == 7.0);
            CHECK(box.high1 - box.low1 == 3.0);
            // the larger extent is scaled, and the scale is 0.0001 in the module
            CHECK(lcns::variantScaleOfBox(box) == 7.0 * lcns::kVariantScale);
            CHECK(lcns::variantScaleOfBox(box) == 0.0007);

            // swap which axis is larger, and the answer must follow
            box.low0 = 0.0;  box.high0 = 1.0;                   // first: 1
            box.low1 = 0.0;  box.high1 = 40.0;                  // second: 40
            CHECK(lcns::variantScaleOfBox(box) == 40.0 * lcns::kVariantScale);

            // equal extents take the not-greater arm, as the ucomisd and jbe at 0x13341/0x13345 say
            box.low0 = 5.0;  box.high0 = 15.0;
            box.low1 = 0.0;  box.high1 = 10.0;
            CHECK(lcns::variantScaleOfBox(box) == 10.0 * lcns::kVariantScale);

            // and the correspondence the header records: extentA is the SECOND axis
            CHECK(lcns::variantScale(true, 3.0, 7.0, lcns::kVariantScale) == 7.0 * lcns::kVariantScale);
            CHECK(lcns::kVariantAppend == 0x23BF0);
        }

        // an invalid box returns zero, which is the routine jumping past BOTH multiplies
        CHECK(lcns::variantScale(false, 10.0, 1.0, 0.5) == 0.0);'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "variantScaleOfBox" in text:
        print("already present")
        return 0
    if OLD not in text:
        print("the anchor is not present verbatim; nothing changed")
        return 1
    text = text.replace(OLD, NEW, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("extended the variant test with the extent step; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
