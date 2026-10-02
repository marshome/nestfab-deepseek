# -*- coding: utf-8 -*-
"""Assert the two derivations the module's typeinfo establishes, so the wiring cannot be lost again.

**A BASE CLASS THAT ONLY EXISTS IN A DOCUMENT IS THE DRIFT THIS PROJECT CHECKS FOR.** `Tiling::Pattern` was absent from this tree for two rounds'
work while the module had it as the base of both pattern classes, so the relationship is asserted here rather than described.
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

BLOCK = '''
    // ---------------------------------------------------------------- the pattern family's base (RE the typeinfo chains)
    //
    // **BOTH RELATIONSHIPS ARE THE MODULE'S OWN, READ FROM THE +0x10 POINTER OF EACH CLASS'S TYPEINFO**:
    //
    //     N6Tiling15BiModulePatternE          -> N6Tiling7PatternE
    //     N6Tiling21MultiOrientedPartPatternE -> N6Tiling7PatternE
    //
    // and neither was declared here until Tiling::Pattern existed, because an abstract base is not a key in `re/vtables.json`.
    {
        static_assert(std::is_base_of<lcns::tiling::Pattern, lcns::tiling::BiModulePattern>::value,
                      "the typeinfo chain N6Tiling15BiModulePatternE -> N6Tiling7PatternE says so");
        static_assert(std::is_base_of<lcns::tiling::Pattern, lcns::tiling::MultiOrientedPartPattern>::value,
                      "the typeinfo chain N6Tiling21MultiOrientedPartPatternE -> N6Tiling7PatternE says so");

        // **AND `Tiling::Pattern`'S MEASURED FACTS ARE REACHABLE THROUGH BOTH**, which is what the base exists for
        CHECK(lcns::tiling::Pattern::kElementStride == 0x90);       // RE 0x4E7F49 and 0x4E7F50
        CHECK(lcns::tiling::Pattern::kCopiedBytes == 0x48);         // RE 0x4E7E6E through 0x4E7EC2
        CHECK(lcns::tiling::Pattern::kContainerOffset == 0x48);     // RE 0x4E7EBA

        // the base is one word, and a derived instance carries MORE -- which is the open question recorded in pattern.hpp and not asserted here
        static_assert(sizeof(lcns::tiling::Pattern) == sizeof(void*),
                      "sizeof(Pattern) is ONE WORD, which is why a derived first member landing at +8 is unexplained");
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "the pattern family's base" in text:
        print("the test already asserts the derivations")
        return 0
    anchor = '    return check::finish("test_recovered");'
    if anchor not in text:
        print("REFUSING: the finish marker is not found")
        return 2
    text = text.replace(anchor, BLOCK + "\n" + anchor, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("added the pattern-family derivation assertions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
