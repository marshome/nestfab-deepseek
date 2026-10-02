# -*- coding: utf-8 -*-
"""Update the variant test for the corrected scale: one constant, not two.

The test previously passed two different factors and asserted that each arm used its own. Both arms load the SAME double at
0x9AD9C8, so the new assertions take one scale and check that the arms differ only in WHICH extent is multiplied.
"""
import io
import re

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD = '''        // an invalid box returns zero, which is the routine jumping past its own scaling
        CHECK(lcns::variantScale(false, 10.0, 1.0, 2.0, 3.0) == 0.0);
        // the first extent larger: extentA * longer
        CHECK(lcns::variantScale(true, 10.0, 1.0, 2.0, 3.0) == 20.0);
        // the second larger: extentB * shorter
        CHECK(lcns::variantScale(true, 1.0, 10.0, 2.0, 3.0) == 30.0);
        // equal extents take the not-greater branch, because the instruction is ucomisd then JBE
        CHECK(lcns::variantScale(true, 5.0, 5.0, 2.0, 3.0) == 15.0);
        // and zero extents give zero either way, which is the degenerate case
        CHECK(lcns::variantScale(true, 0.0, 0.0, 2.0, 3.0) == 0.0);
        // the offsets, against the instructions that show them
        CHECK(lcns::kVariantSource == 0x50);
        CHECK(lcns::kVariantTargetA == 0x68);
        CHECK(lcns::kVariantTargetB == 0x208);
        CHECK(lcns::kVariantTargetB < 0x2C0);              // inside the object the constructor allocates
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, commonCutSafetyPreferenceGiven) == lcns::kVariantTargetA);
        CHECK(lcns::kVariantScaleLong != lcns::kVariantScaleShort);'''

NEW = '''        // an invalid box returns zero, which is the routine jumping past BOTH multiplies
        CHECK(lcns::variantScale(false, 10.0, 1.0, 0.5) == 0.0);
        // the first extent larger: extentA * scale
        CHECK(lcns::variantScale(true, 10.0, 1.0, 0.5) == 5.0);
        // the second larger: extentB * scale
        CHECK(lcns::variantScale(true, 1.0, 10.0, 0.5) == 5.0);
        // equal extents take the not-greater branch, because the instruction is ucomisd then JBE
        CHECK(lcns::variantScale(true, 5.0, 5.0, 0.5) == 2.5);
        // and zero extents give zero either way, which is the degenerate case
        CHECK(lcns::variantScale(true, 0.0, 0.0, 0.5) == 0.0);
        // CORRECTION: both arms load the SAME constant. The two mulsd instructions have different DISPLACEMENTS
        // (0x99a679 at 0x13347 and 0x99a63e at 0x13382) that resolve to the SAME address 0x9AD9C8, where the double is
        // 0.0001. So the comparison selects which extent is multiplied and not the factor, and the earlier test -- which
        // passed two factors and asserted each arm used its own -- was asserting something the instructions do not do.
        CHECK(lcns::kVariantScale == 0.0001);
        CHECK(lcns::variantScale(true, 10000.0, 1.0, lcns::kVariantScale) == 1.0);
        CHECK(lcns::variantScale(true, 1.0, 10000.0, lcns::kVariantScale) == 1.0);
        CHECK(lcns::variantScale(true, 20000.0, 1.0, lcns::kVariantScale) == 2.0);
        // the offsets, against the instructions that show them
        CHECK(lcns::kVariantSource == 0x50);
        CHECK(lcns::kVariantTargetA == 0x68);
        CHECK(lcns::kVariantTargetB == 0x208);
        CHECK(lcns::kVariantTargetB < 0x2C0);              // inside the object the constructor allocates
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, commonCutSafetyPreferenceGiven) == lcns::kVariantTargetA);'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD not in text:
        print("the old block is not present verbatim; nothing changed")
        return 1
    text = text.replace(OLD, NEW, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("updated the variant test for the single scale constant")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
