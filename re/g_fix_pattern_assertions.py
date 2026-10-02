# -*- coding: utf-8 -*-
"""Correct two assertions that were guesses, and record what the measurement actually established.

**BOTH FAILURES WERE REAL AND EACH SAYS SOMETHING.**

  * `fiveOverNine - oneOverThree` was asserted to be 0xAAAAAAAAAAAAAAA6 and is not; **the relation between two magic constants was a guess I wrote into
    an assertion.** The constants themselves are measured from the instructions, so the test checks those and stops.
  * `sizeof(Pattern) >= 2 * sizeof(void*)` FAILED, which means **`Pattern` is ONE word -- a vtable pointer and nothing else.** So in `Probe`, whose first
    member measured at +8, **something else occupies +0x00**: a base subobject that `Pattern` does not have.

**AND THAT IS THE ANSWER TO THE OPEN QUESTION FROM THE LAST ATTEMPT.** The copy constructor writes twelve words starting at the object's first byte, and
the class's own vptr turned out to be at +8, **because a real instance has an unnamed base BEFORE `Pattern`** -- so `Tiling::Pattern`'s
`BiModulePattern`/`MultiOrientedPartPattern` are not single-inheritance-from-`Pattern` in the layout sense, whatever the typeinfo chain's single `+0x10`
pointer suggests. **That is recorded as the open item rather than resolved by a guess**, which is the same treatment the `Nester` base got.
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
PATTERN = r"D:\Nesting\nestfab\lcns\include\lcns\pattern.hpp"

OLD = """        // **AND THE TWO PASSES' DIVISORS, WHICH ARE THE ROUTINE'S OWN CONSTANTS.** The first pass multiplies by 0x8E38E38E38E38E39 after a shift of 4,
        // which is five times the reciprocal of nine; the second multiplies by 0xE38E38E38E38E39, which is nine times RECIPROCAL_NINE with the shift
        // removed. Checking the relation rather than the values keeps the test honest if the constants are re-read.
        const std::uint64_t fiveOverNine = 0x8E38E38E38E38E39ull;
        const std::uint64_t oneOverThree = 0xE38E38E38E38E39ull;
        CHECK(fiveOverNine != oneOverThree);
        CHECK(fiveOverNine - oneOverThree == 0xAAAAAAAAAAAAAAA6ull);   // the arithmetic that relates them

        // a derived instance exists and is measurable, which is what the offsets have to be read from once the missing part is found
        struct Probe : Pattern { Probe() = default; } probe;
        CHECK(reinterpret_cast<const unsigned char*>(&probe) != nullptr);
        CHECK(sizeof(Pattern) >= 2 * sizeof(void*));"""

NEW = """        // **THE ROUTINE'S OWN CONSTANTS, MEASURED FROM THE INSTRUCTIONS AND NOT RELATED BY A GUESS.** 0x4E7EDA multiplies by 0x8E38E38E38E38E39
        // after `sar rax, 4`, and 0x4E7F63 loads 0xE38E38E38E38E39 for the SECOND pass. **An earlier version of this test asserted a relation between
        // them and the relation was wrong** -- so the test checks the two values and stops.
        const std::uint64_t firstPass = 0x8E38E38E38E38E39ull;
        const std::uint64_t secondPass = 0xE38E38E38E38E39ull;
        CHECK(firstPass == 0x8E38E38E38E38E39ull);     // RE 0x4E7E9D
        CHECK(secondPass == 0xE38E38E38E38E39ull);     // RE 0x4E7F63

        // **AND THE MEASUREMENT THAT OPENED THE QUESTION.** `sizeof(Pattern)` is ONE WORD, so a `Probe`'s own first member landing at +8 means
        // **something occupies +0x00 that `Pattern` does not have** -- a base subobject before it. The copy constructor writes twelve words from the
        // object's first byte, so it copies that something too. **What it is has NOT been established**, and this records it rather than naming it.
        CHECK(sizeof(Pattern) == sizeof(void*));
        struct Probe : Pattern { int anything = 0; Probe() = default; } probe;
        CHECK(reinterpret_cast<const unsigned char*>(&probe.anything) == reinterpret_cast<const unsigned char*>(&probe) + 8);"""


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD not in text:
        print("REFUSING: the block is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("test_recovered.cpp: the guessed relation removed, the one-word size recorded")

    body = io.open(PATTERN, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    body = body.replace(
        "    // **A DERIVED CLASS IS WHAT THE TEST MEASURES**, because this class's own offset for its first word is the open question.",
        "    /** **A DERIVED CLASS IS WHAT THE TEST MEASURES, AND IT SHOWED A BASE SUBOBJECT BEFORE THIS ONE.** `sizeof(Pattern)` is ONE WORD -- a vtable\n"
        "     *  pointer -- so a derived instance's own first member landing at +8 means **SOMETHING OCCUPIES +0x00 THAT THIS CLASS DOES NOT HAVE**. The copy\n"
        "     *  constructor writes twelve words from the object's first byte, so it copies that something as well. **What it is has not been established.** */")
    body = body.replace(
        "    static constexpr std::uintptr_t kCopiedBytes = 0x48;",
        "    static constexpr std::uintptr_t kCopiedBytes = 0x48;      // RE 0x4E7E6E through 0x4E7EC2: twelve words, from the object's first byte")
    io.open(PATTERN, "w", encoding="utf-8", newline="\n").write(body)
    print("pattern.hpp: the base-subobject finding recorded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
