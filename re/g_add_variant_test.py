# -*- coding: utf-8 -*-
"""Add the variant scale test, which check_recovery requires because the header declares a name in it.

The project's rule: everything declared in include/lcns must be named in a test. The variant rule has three behaviours and they are
exactly what needs pinning -- an invalid box scales nothing, and the larger extent chooses which constant is used.
"""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- the variant scale rule (RE 0x132E0)
    //
    // The rule two exports share, and the three behaviours its instructions express: an invalid box scales nothing (0x13327 jumps
    // past both multiplies), and the LARGER of the two extents chooses which constant is used (0x13341, 0x13345 and 0x13382).
    {
        // an invalid box returns zero, which is the routine jumping past its own scaling
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
        CHECK(lcns::kVariantScaleLong != lcns::kVariantScaleShort);
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "variantScale" in text:
        print("already present")
        return 0
    if '#include "lcns/variant.hpp"' not in text:
        anchor = '#include "lcns/stat.hpp"\n'
        assert anchor in text, "the stat include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/variant.hpp"\n', 1)
        print("added the include")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the variant test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
