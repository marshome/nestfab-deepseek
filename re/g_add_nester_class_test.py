# -*- coding: utf-8 -*-
"""Include the real NestingNester header and add a test that exercises the CLASS rather than a table."""
import io
import os

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
ANCHOR = '    return check::finish("test_recovered");'

BLOCK = '''
    // ---------------------------------------------------------------- Multi::NestingNester as a CLASS (RE 0x342E0)
    //
    // The human's point: a table of offsets is metadata ABOUT a class, not a class. This one has members with types, and its constructors
    // builders are the instructions. **The finding that forced the rewrite**: +0x9F8 is not a field among seven, it is the TWIST INDEX of a
    // 624 word Mersenne Twister whose state lives at +0x38.
    {
        // the algorithm's constants are the module's, and they identify the generator
        CHECK(lcns::Multi::Mt19937::kStateSize == 624u);                       // RE 0x3435C: cmp rdx, 0x270
        CHECK(lcns::Multi::Mt19937::kSeedMultiplier == 1812433253u);           // RE 0x3434B: imul eax, eax, 0x6c078965
        CHECK(lcns::Multi::Mt19937::kSeedMultiplier == 0x6C078965u);

        // THE LAYOUT IS THE CLASS'S OWN, which is what a real declaration buys: offsetof against the instructions that placed them
        using lcns::Multi::NestingNester;
        CHECK(offsetof(NestingNester, seedP) == 0x18u);
        CHECK(offsetof(NestingNester, seedQ) == 0x20u);
        CHECK(offsetof(NestingNester, seed) == 0x28u);
        CHECK(offsetof(NestingNester, ratio) == 0x30u);
        CHECK(offsetof(NestingNester, twister) == 0x38u);
        CHECK(offsetof(NestingNester, tail) == 0xA00u);

        // and the twister's own members: the index sits after all 624 words, which is what 0x9F8 - 0x38 = 624*4 says
        CHECK(offsetof(lcns::Multi::Mt19937, state) == 0u);
        CHECK(offsetof(lcns::Multi::Mt19937, index) == 624u * 4u);
        CHECK(sizeof(lcns::Multi::Mt19937::state) == 624u * 4u);

        // AN INSTANCE CAN BE BUILT AND ITS FIELDS SET, which a table of offsets cannot do
        NestingNester nester{};
        nester.seedP = nullptr;
        nester.seedQ = nullptr;
        nester.seed = 0x12345678u;
        nester.ratio = 0.5;
        CHECK(nester.seed == 0x12345678u);
        CHECK(nester.ratio == 0.5);
        // the state size and the index are the SAME NUMBER at construction, which is what "untwisted" means
        CHECK(nester.twister.index == lcns::Multi::Mt19937::kStateSize);

        // and the same value the constructor writes at 0x3436D, so the class agrees with the instruction
        CHECK(nester.twister.index == 0x270u);
        CHECK(nester.twister.state.size() == 0x270u);
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "Mt19937" in text:
        print("already present")
        return 0
    include = '#include "lcns/nesting_nester.hpp"\n'
    if include not in text:
        anchor = '#include "lcns/class_constructors.hpp"\n'
        assert anchor in text, "the class_constructors include is gone"
        text = text.replace(anchor, anchor + include, 1)
        print("include added")
    text = text.replace(ANCHOR, BLOCK + "\n" + ANCHOR, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("the class test added; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
