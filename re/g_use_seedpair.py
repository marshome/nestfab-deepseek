# -*- coding: utf-8 -*-
"""Use SeedPair in the test, which is what check_recovery wants and what the constructor's signature needs."""
import io

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD = """        // and the same value the constructor writes at 0x3436D, so the class agrees with the instruction
        CHECK(nester.twister.index == 0x270u);
        CHECK(nester.twister.state.size() == 0x270u);
    }
"""

NEW = """        // and the same value the constructor writes at 0x3436D, so the class agrees with the instruction
        CHECK(nester.twister.index == 0x270u);
        CHECK(nester.twister.state.size() == 0x270u);

        // THE CONSTRUCTOR'S THIRD ARGUMENT IS A PAIR, which RE 0x342EF's `mov rdi, r8` then 0x3430B and 0x34301 show by reading
        // [rdi] and [rdi + 8] into the two pointers at +0x18 and +0x20. SeedPair is that pair as a type.
        lcns::Multi::SeedPair seeds;
        seeds.first = reinterpret_cast<void*>(0x1111);
        seeds.second = reinterpret_cast<void*>(0x2222);
        CHECK(seeds.first == reinterpret_cast<void*>(0x1111));
        CHECK(seeds.second == reinterpret_cast<void*>(0x2222));

        // and the two members it fills are the two the constructor writes, which is the correspondence the type records
        NestingNester seeded{};
        seeded.seedP = seeds.first;                    // the +0x18 member, from [rdi]
        seeded.seedQ = seeds.second;                   // the +0x20 member, from [rdi + 8]
        CHECK(seeded.seedP == seeds.first);
        CHECK(seeded.seedQ == seeds.second);
        CHECK(offsetof(lcns::Multi::SeedPair, first) == 0u);
        CHECK(offsetof(lcns::Multi::SeedPair, second) == 8u);
    }
"""


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "SeedPair seeds" in text:
        print("already present")
        return 0
    if OLD not in text:
        print("the anchor is not present verbatim")
        return 1
    text = text.replace(OLD, NEW, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("SeedPair exercised in the test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
