# -*- coding: utf-8 -*-
"""Rewrite the class test for the standard-layout form, where the field offsets are relative to the block that starts at 0x18."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

START = "    // ---------------------------------------------------------------- Multi::NestingNester as a CLASS (RE 0x342E0)"
END = '    return check::finish("test_recovered");'

BLOCK = '''    // ---------------------------------------------------------------- Multi::NestingNester as a CLASS (RE 0x342E0)
    //
    // The human's point: a table of offsets is metadata ABOUT a class, not a class. This one has members with types, and the instructions
    // place them. **The finding that forced the rewrite**: +0x9F8 is not a field among seven, it is the TWIST INDEX of a 624 word Mersenne
    // Twister whose state lives at +0x38.
    {
        using lcns::Multi::Mt19937;
        using lcns::Multi::SeedPair;
        using lcns::Multi::NestingNesterFields;

        // the algorithm's constants are the module's, and together they identify the generator
        CHECK(Mt19937::kStateSize == 624u);                     // RE 0x3435C: cmp rdx, 0x270
        CHECK(Mt19937::kSeedMultiplier == 1812433253u);         // RE 0x3434B: imul eax, eax, 0x6c078965
        CHECK(Mt19937::kSeedMultiplier == 0x6C078965u);

        // THE LAYOUT IS THE TYPE'S OWN, which is what a real declaration buys. These are exact because the struct is STANDARD-LAYOUT:
        // a polymorphic class answers offsetof with -Winvalid-offsetof, and the compiler said so on the first attempt.
        CHECK(offsetof(SeedPair, first) == 0x00u);              // RE 0x3430B: mov rax, [rdi]
        CHECK(offsetof(SeedPair, second) == 0x08u);             // RE 0x34301: mov rdx, [rdi + 8]

        CHECK(offsetof(NestingNesterFields, seedP) == 0x00u);   // RE 0x34312: the module's +0x18
        CHECK(offsetof(NestingNesterFields, seedQ) == 0x08u);   // RE 0x3430E: the module's +0x20
        CHECK(offsetof(NestingNesterFields, seed) == 0x10u);    // RE 0x34341: the module's +0x28
        CHECK(offsetof(NestingNesterFields, ratio) == 0x18u);   // RE 0x343E3: the module's +0x30
        CHECK(offsetof(NestingNesterFields, twister) == 0x20u); // RE 0x34354: the module's +0x38
        CHECK(offsetof(NestingNesterFields, tail) == 0x9E8u);   // RE 0x34388: the module's +0xa00

        // AND THE TWO ARITHMETIC IDENTITIES THAT CONNECT THE STRUCT TO THE MODULE'S OFFSETS, which is the whole point of stating the
        // block's start as a constant: the struct begins where the module's first data member does.
        CHECK(lcns::Multi::kNestingNesterFieldsStart == 0x18u);
        CHECK(lcns::Multi::kNestingNesterFieldsStart + offsetof(NestingNesterFields, twister) == 0x38u);
        CHECK(lcns::Multi::kNestingNesterFieldsStart + offsetof(NestingNesterFields, ratio) == 0x30u);
        CHECK(lcns::Multi::kNestingNesterFieldsStart + offsetof(NestingNesterFields, tail) == 0xA00u);

        // **THE FINDING, AS ARITHMETIC**: the field block plus the whole 624 word state lands exactly on 0x9F8, which a table of distinct
        // offsets recorded as one more field. It is the array's END, and 0x9F8 holds the twist index that follows it.
        CHECK(lcns::Multi::kNestingNesterFieldsStart + 624u * 4u == 0x9F8u);
        CHECK(offsetof(Mt19937, index) == 624u * 4u);
        CHECK(offsetof(Mt19937, state) == 0u);
        CHECK(sizeof(Mt19937::state) == 2496u);

        // AN INSTANCE CAN BE BUILT AND ITS FIELDS SET, which a table of offsets cannot do
        NestingNesterFields fields{};
        fields.seed = 0x12345678u;
        fields.ratio = 0.5;
        CHECK(fields.seed == 0x12345678u);
        CHECK(fields.ratio == 0.5);
        // the index equals the state size at construction, which is what "untwisted" means, and the constructor writes exactly that
        CHECK(fields.twister.index == Mt19937::kStateSize);
        CHECK(fields.twister.index == 0x270u);
        CHECK(fields.twister.state.size() == 0x270u);

        // the pair, and the two members it fills -- the correspondence the type records
        SeedPair seeds;
        seeds.first = reinterpret_cast<void*>(0x1111);
        seeds.second = reinterpret_cast<void*>(0x2222);
        NestingNesterFields seeded{};
        seeded.seedP = seeds.first;         // the module's +0x18, from [rdi]
        seeded.seedQ = seeds.second;        // the module's +0x20, from [rdi + 8]
        CHECK(seeded.seedP == seeds.first);
        CHECK(seeded.seedQ == seeds.second);

        // and the constructor's address and its base call, which the class records rather than its layout
        CHECK(lcns::Multi::kNestingNesterCtorAddress == 0x342E0u);
        CHECK(lcns::Multi::kNestingNesterBaseCtor == 0xB4470u);   // RE 0x342F5
        CHECK(lcns::Multi::kNestingNesterObjectBytes == 0xA40u);
    }

'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find(START)
    end = text.find(END, start)
    if start < 0 or end < 0:
        print("bounds not found: start=%d end=%d" % (start, end))
        return 1
    text = text[:start] + BLOCK + text[end:]
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote the class test for the standard-layout form")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
