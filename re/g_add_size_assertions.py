# -*- coding: utf-8 -*-
"""Add the size assertions the suite was missing, then report what they say.

**THE TEST COMPARED A CONSTANT TO ITSELF.** `CHECK(kFlipNesterBytes == 0x28)` where `kFlipNesterBytes` is `inline constexpr int = 0x28` -- **so a class that is LARGER
than the module allocates passes**, which is how `FlipNester` at 0x30 sailed past a suite that lists 0x28.

**AND THE ASSERTION THAT CAN FAIL IS A COMPILE-TIME ONE**: `sizeof(T) <= the module's allocation`. **It is a MEASUREMENT of the model against the module**, it costs
nothing at run time, and **it is where the contradiction belongs** -- because a contradiction that only a human notices is a contradiction that gets shipped.

**AND IT IS AN UPPER BOUND AND NOT AN EQUALITY, WHICH IS A DELIBERATE CHOICE**: the module allocates a block and constructs in it, so the object may be SMALLER than the
block -- `NestingNester` is 0xA40 allocated and the block is what the allocation site passes. **An equality would flag correct code, and a check that flags correct code
gets switched off.**
"""
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "engine.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")

# the class and the constant that holds the module's allocation for it
PAIRS = [
    ("FlipNester", "kFlipNesterBytes"),
    ("MultiTorchNester", "kMultiTorchNesterBytes"),
    ("LimitedNester", "kLimitedNesterBytes"),
    ("FilterNester", "kFilterNesterBytes"),
    ("NoFillNester", "kNoFillNesterBytes"),
    ("CompactNester", "kCompactNesterBytes"),
    ("NestingNester", "kNestingNesterBytes"),
    ("RectangleNester", "kRectangleNesterBytes"),
    # **`RowNester` IS NAMED AND EXCLUDED, NOT SILENTLY DROPPED.** The module inlines a 208-byte `RowNestCore` at +0x18; this port holds a `std::unique_ptr` to it
    # instead, **because `makeStrategy()` has no `Order` at construction time and the comment on the class says so**. So the port's object is SMALLER and its size is
    # not comparable to the module's -- **and a check that flags a documented deviation gets switched off, while one that names the exception keeps working for the
    # other eight.** `re/g_add_size_assertions.py` carries the same note.
]

ANCHOR = "        CHECK(kNestingNesterBytes == 0xA40);"


def main(apply):
    test = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    header = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")

    block = ["        // **AND THE MODEL MUST FIT IN WHAT THE MODULE ALLOCATES -- A COMPILE-TIME MEASUREMENT THE SUITE DID NOT HAVE.**",
             "        // Every assertion above compares a constant to the SAME constant (`kFlipNesterBytes == 0x28`, and kFlipNesterBytes IS 0x28), so a class larger",
             "        // than its allocation passed. `sizeof` against the allocation is the check that can fail, and a contradiction that only a human notices is one",
             "        // that gets shipped. **It is an UPPER BOUND and not an equality**, because the module allocates a block and constructs in it, so the object may",
             "        // be smaller than the block -- `NestingNester` is 0xA40 and the block is what the allocation site passes.",
             "        //",
             "        // **AND A CLASS WHOSE LAYOUT DELIBERATELY DEVIATES IS EXCLUDED AND NAMED, NOT SILENTLY DROPPED.** The module inlines a 208-byte `RowNestCore`",
             "        // inside `RowNester` at +0x18 and this port holds a `std::unique_ptr` to it instead, because `makeStrategy()` has no `Order` at construction",
             "        // time -- so the port's object is SMALLER than the module's and its size is not comparable. **A check that flags a documented deviation gets",
             "        // switched off; one that names the exception keeps working for everything else.**",
             "        //",
             "        // sizes as the model sees them (a failure here prints the real number):"]
    for klass, constant in PAIRS:
        block.append("        static_assert(sizeof(lcns::%s) <= static_cast<std::size_t>(lcns::%s), "
                     "\"the model's %s is larger than the module's allocation\");" % (klass, constant, klass))
    # **AND THE RUNTIME PRINT, SO ONE BUILD REPORTS EVERY SIZE AT ONCE** instead of one failing assert at a time
    block.append("        std::printf(\"model sizes: Flip %zu/%d  MultiTorch %zu/%d  Limited %zu/%d  Filter %zu/%d  NoFill %zu/%d  Compact %zu/%d  Nesting %zu/%d  Rectangle %zu/%d  Row %zu/%d\\n\",")
    block.append("            sizeof(lcns::FlipNester), lcns::kFlipNesterBytes, sizeof(lcns::MultiTorchNester), lcns::kMultiTorchNesterBytes,")
    block.append("            sizeof(lcns::LimitedNester), lcns::kLimitedNesterBytes, sizeof(lcns::FilterNester), lcns::kFilterNesterBytes,")
    block.append("            sizeof(lcns::NoFillNester), lcns::kNoFillNesterBytes, sizeof(lcns::CompactNester), lcns::kCompactNesterBytes,")
    block.append("            sizeof(lcns::NestingNester), lcns::kNestingNesterBytes, sizeof(lcns::RectangleNester), lcns::kRectangleNesterBytes,")
    block.append("            sizeof(lcns::RowNester), lcns::kRowNesterBytes);   // **the documented deviation: the port holds a pointer where the module inlines 208 bytes**")
    block = "\n".join(block) + "\n"

    if "the model's FlipNester is larger than the module's allocation" in test:
        print("the size assertions are already there")
    else:
        if ANCHOR not in test:
            print("REFUSING: the anchor is not where it is expected")
            return 2
        test = test.replace(ANCHOR, block + ANCHOR, 1)
        print("   added %d static_assert(s)" % len(PAIRS))

    # and the runtime CHECKs stay, but the comment says what they are
    test = test.replace("        CHECK(kFlipNesterBytes == 0x28);",
                        "        CHECK(kFlipNesterBytes == 0x28);   // the CONSTANT, not the model -- the static_asserts below are the measurement", 1)

    if apply:
        io.open(TEST, "w", encoding="utf-8", newline="\n").write(test)
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
