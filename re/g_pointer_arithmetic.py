# -*- coding: utf-8 -*-
"""Replace the offsetof checks on the polymorphic class with POINTER ARITHMETIC on a real object.

`offsetof` is only conditionally supported on a non-standard-layout type, so GCC warns wherever it appears and the gate refuses a warning. **A
pointer difference against a constructed object is the same measurement with no such condition** -- and it is stronger, because it is taken on a
REAL instance rather than from the type alone, which is something only a class with a constructor can offer.
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD = '''        // THE LAYOUT IS MEASURED, AND IT DOES NOT MATCH THE MODULE -- recorded rather than hidden. The compiler gives seedP at 0x08 while the
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

NEW = '''        // THE LAYOUT IS MEASURED, AND IT DOES NOT MATCH THE MODULE -- recorded rather than hidden. The compiler places seedP at 0x08 while
        // the module writes it at 0x18, and the difference is the same 0x10 for all five members.
        //
        // THE MEASUREMENT IS A POINTER DIFFERENCE against a real object rather than `offsetof`, because `offsetof` is only conditionally
        // supported on a polymorphic type and GCC warns -- and **a pointer difference is stronger anyway: it is taken on a constructed
        // instance**, which is something only a class with a constructor can offer.
        lcns::SeedPair probeSeeds;
        lcns::NestingNester probe(probeSeeds);
        const char* base = reinterpret_cast<const char*>(&probe);
        const std::ptrdiff_t atSeedP = reinterpret_cast<const char*>(&probe.seedP) - base;
        const std::ptrdiff_t atSeedQ = reinterpret_cast<const char*>(&probe.seedQ) - base;
        const std::ptrdiff_t atSeed = reinterpret_cast<const char*>(&probe.seed) - base;
        const std::ptrdiff_t atRatio = reinterpret_cast<const char*>(&probe.ratio) - base;
        const std::ptrdiff_t atTwister = reinterpret_cast<const char*>(&probe.twister) - base;

        CHECK(atSeedP == 0x08);      // MEASURED
        CHECK(atSeedQ == 0x10);      // MEASURED
        CHECK(atSeed == 0x18);       // MEASURED
        CHECK(atRatio == 0x20);      // MEASURED
        CHECK(atTwister == 0x28);    // MEASURED

        // **AND THE GAP IS THE FINDING**: the module's offsets are 0x10 further along, so its base occupies two quadwords this C++ `Nester`
        // does not have. What they are is NOT established -- 0xB4470 has not been read -- and that is recorded rather than filled in.
        CHECK(lcns::kNestingNesterBaseDataGap == 0x10u);
        CHECK(atSeedP + lcns::kNestingNesterBaseDataGap == 0x18);    // RE 0x34312: mov [rbx + 0x18], rax
        CHECK(atSeedQ + lcns::kNestingNesterBaseDataGap == 0x20);    // RE 0x3430E: mov [rbx + 0x20], rdx
        CHECK(atSeed + lcns::kNestingNesterBaseDataGap == 0x28);     // RE 0x34341: mov [rbx + 0x28], eax
        CHECK(atRatio + lcns::kNestingNesterBaseDataGap == 0x30);    // RE 0x343E3: movsd [rbx + 0x30], xmm6
        CHECK(atTwister + lcns::kNestingNesterBaseDataGap == 0x38);  // RE 0x34354: [rbx + rdx*4 + 0x38]
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD not in text:
        print("the anchor is not present verbatim")
        return 1
    text = text.replace(OLD, NEW, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("replaced offsetof with pointer arithmetic on a real object")
    return 0


if __name__ == "__main__":
    sys.exit(main())
