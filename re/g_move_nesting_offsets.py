# -*- coding: utf-8 -*-
"""Move the NestingNester offset assertions to the module's real offsets, now that the base is known.

**THE TEST WAS WRITTEN FROM A WRONG PREMISE AND WAS RIGHT TO BE**: it measured `atSeedP == 0x08` and recorded `kNestingNesterBaseDataGap = 0x10` with the note "the
base constructor 0xB4470 has not been read". **That gap WAS the base's three fields.** 0xB4470 is 29 bytes, stores a vtable pointer, a pointer at +0x8, 99999 at
+0x10 and -1 at +0x14, and **all five of its callers write their first own member at +0x18** -- so the base part is 0x18 and the module's `seedP` at 0x18 is exactly
`NestingNester`'s first own member.

**SO THE MODEL WAS 0x10 BYTES SHORT AND THE `+ gap` ARITHMETIC WAS COMPENSATING FOR IT.** With the fields declared the gap is zero and the assertions can say what
the module says.
"""
import io
import os
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
HEADER = r"D:\Nesting\nestfab\lcns\include\lcns\nester.hpp"

BLOCK_OLD = """        CHECK(atSeedP == 0x08);      // MEASURED
        CHECK(atSeedQ == 0x10);      // MEASURED
        CHECK(atSeed == 0x18);       // MEASURED
        CHECK(atRatio == 0x20);      // MEASURED
        CHECK(atTwister == 0x28);    // MEASURED
"""

BLOCK_NEW = """        // **THE REAL OFFSETS, NOW THAT THE BASE HAS ITS THREE FIELDS.** These used to read 0x08..0x28 with a `+ gap` correction, because the model's `Nester`
        // held no data and the module's base part is 0x18 bytes. `lcns/nester.hpp` declares them now, so the offsets ARE the module's and there is no gap to add.
        CHECK(atSeedP == 0x18);      // RE 0x34312: mov [rbx + 0x18], rax
        CHECK(atSeedQ == 0x20);      // RE 0x3430E: mov [rbx + 0x20], rdx
        CHECK(atSeed == 0x28);       // RE 0x34341: mov [rbx + 0x28], eax
        CHECK(atRatio == 0x30);      // MEASURED
        CHECK(atTwister == 0x38);    // MEASURED
"""


def main(apply):
    test = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if BLOCK_NEW.split("\n")[1] in test:
        print("the test is already moved")
        return 0
    if BLOCK_OLD not in test:
        print("REFUSING: the assertion block is not where it is expected")
        return 2
    test = test.replace(BLOCK_OLD, BLOCK_NEW, 1)

    # and the two gap assertions that follow, which now say zero
    for old, new in (
        ("CHECK(lcns::kNestingNesterBaseDataGap == 0x10u);",
         "// **THE GAP IS ZERO NOW, AND THAT IS THE WHOLE POINT OF THE ROUND**: the 0x10 it recorded WAS the base's three fields, and they are declared.\n"
         "        CHECK(lcns::kNestingNesterBaseDataGap == 0x00u);"),
    ):
        if old in test:
            test = test.replace(old, new, 1)
            print("   the gap assertion now says zero")

    # the `+ gap` lines become plain, because the offsets already are the module's
    for member, offset in (("atSeedP", "0x18"), ("atSeedQ", "0x20"), ("atSeed", "0x28")):
        old = "CHECK(%s + lcns::kNestingNesterBaseDataGap == %s);" % (member, offset)
        if old in test:
            test = test.replace(old, "CHECK(%s == %s);   // the base fields are declared, so no correction is needed" % (member, offset), 1)

    header = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    header = header.replace("constexpr std::size_t kNestingNesterBaseDataGap = 0x10;",
                            "constexpr std::size_t kNestingNesterBaseDataGap = 0x00;", 1)

    if apply:
        io.open(TEST, "w", encoding="utf-8", newline="\n").write(test)
        io.open(HEADER, "w", encoding="utf-8", newline="\n").write(header)
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
