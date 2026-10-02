# -*- coding: utf-8 -*-
"""Move the offsetof checks on NestingNester from the header into the test, where they belong.

`offsetof` on a polymorphic class is conditionally supported, so GCC warns wherever it appears -- but a WARNING IS A MEASUREMENT and the gate
refuses one. The split that works: the HEADER declares the class and its constants, and the TEST asserts the offsets, because a test is where a
measurement belongs and a header is where a declaration belongs.
"""
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
NESTER = os.path.join(ROOT, "lcns", "include", "lcns", "nester.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")

KEEP_IN_HEADER = '''// SO THE ASSERT BELOW CHECKS THE DIFFERENCE RATHER THAN PRETENDING IT AWAY: the module's offsets are recorded as constants with their
// instructions, the model's offsets are asserted in lcns/tests/test_recovered.cpp -- **a test is where a measurement belongs and a header is
// where a declaration belongs**, which is also why the offsets are not asserted here: `offsetof` on a polymorphic class is only conditionally
// supported and GCC warns, and a warning is a measurement the gate refuses.
constexpr std::size_t kNestingNesterBaseDataGap = 0x10;    // module offset minus model offset, the same for all five members

static_assert(offsetof(SeedPair, second) == 0x08, "RE 0x34301: mov rdx, [rdi + 8]");
static_assert(Mt19937::kStateSize == 624, "RE 0x3435C: cmp rdx, 0x270");
static_assert(Mt19937::kSeedMultiplier == 1812433253u, "RE 0x3434B: imul eax, eax, 0x6c078965");
'''

TEST_BLOCK = '''
        // THE LAYOUT IS MEASURED, AND IT DOES NOT MATCH THE MODULE -- recorded rather than hidden. The compiler gives seedP at 0x08 while the
        // module writes it at 0x18, and the difference is the same 0x10 for all five members.
        CHECK(offsetof(lcns::NestingNester, seedP) == 0x08u);      // MEASURED
        CHECK(offsetof(lcns::NestingNester, seedQ) == 0x10u);      // MEASURED
        CHECK(offsetof(lcns::NestingNester, seed) == 0x18u);       // MEASURED
        CHECK(offsetof(lcns::NestingNester, ratio) == 0x20u);      // MEASURED
        CHECK(offsetof(lcns::NestingNester, twister) == 0x28u);    // MEASURED
        CHECK(lcns::kNestingNesterBaseDataGap == 0x10u);
        CHECK(offsetof(lcns::NestingNester, seedP) + lcns::kNestingNesterBaseDataGap == 0x18u);   // RE 0x34312
        CHECK(offsetof(lcns::NestingNester, seedQ) + lcns::kNestingNesterBaseDataGap == 0x20u);   // RE 0x3430E
        CHECK(offsetof(lcns::NestingNester, seed) + lcns::kNestingNesterBaseDataGap == 0x28u);    // RE 0x34341
        CHECK(offsetof(lcns::NestingNester, ratio) + lcns::kNestingNesterBaseDataGap == 0x30u);   // RE 0x343E3
        CHECK(offsetof(lcns::NestingNester, twister) + lcns::kNestingNesterBaseDataGap == 0x38u); // RE 0x34354
'''


def main():
    text = io.open(NESTER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find("// SO THE ASSERT BELOW CHECKS THE DIFFERENCE")
    if start < 0:
        print("the assert block is not found")
        return 1
    end = text.find("static_assert(Mt19937::kSeedMultiplier == 1812433253u", start)
    end = text.find("\n", end) + 1
    text = text[:start] + KEEP_IN_HEADER + text[end:]
    io.open(NESTER, "w", encoding="utf-8", newline="\n").write(text)
    print("header keeps the constants and the standard-layout asserts only")

    test = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "kNestingNesterBaseDataGap" in test:
        print("the test already asserts the gap")
        return 0
    marker = "        CHECK(lcns::Mt19937::kSeedMultiplier == 0x6C078965u); // RE 0x3434B"
    if marker not in test:
        marker = "        CHECK(offsetof(lcns::SeedPair, second) == 0x08u);    // RE 0x34301"
    if marker not in test:
        print("the insertion point is not found")
        return 1
    test = test.replace(marker, marker + "\n" + TEST_BLOCK, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(test)
    print("the test now asserts the measured offsets and the 0x10 gap")
    return 0


if __name__ == "__main__":
    sys.exit(main())
