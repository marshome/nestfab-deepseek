# -*- coding: utf-8 -*-
"""Resolve the eight bytes: `mov dword [rbx + 0x18], 1` is `mt[0]` AND THE SEED, not an index -- and the loop starts at rdx = 1.

**THE CONTRADICTION IS GONE AND THE ARITHMETIC THAT REMOVES IT IS ONE INSTRUCTION I MISREAD:**

    0B007A  mov ecx, 1
    0B007F  mov edx, 1                      ; **THE LOOP STARTS AT 1, not 0**
    0B0084  mov dword [rbx + 0x18], 1       ; and +0x18 already holds 1 -- **this is mt[0], the SEED**
    0B0090  ... the MT seeding step ...
    0B00A0  mov dword [rbx + rdx*4 + 0x18], ecx    ; writes mt[rdx]
    0B00A8  cmp rdx, 0x270                   ; until 624, so rdx runs 1 .. 623
    0B00B7  mov qword [rbx + 0x9d8], 0x270

**SO THE LOOP WRITES `mt[1]` THROUGH `mt[623]`**: the first at +0x18 + 1*4 = **+0x1C** and the last at +0x18 + 623*4 = **+0x9D7**. **`mt` is 624 words
from +0x18 to +0x9D7, `mti` is at +0x9D8, and 0x9D8 + 8 = 0x9e0 -- exactly `mov ecx, 0x9e0`.** Nothing overlaps and nothing is missing.

**AND MY ERROR WAS TO READ `+0x18` AS THE INDEX.** It is `mt[0]`: the standard seeding sets the state's FIRST word to the seed and then fills the rest from it,
and `mov dword [rbx + 0x18], 1` at 0x0B0084 is that first word. **The index is the eight bytes at +0x9D8 that 0x0B00B7 writes** -- eight and not four, which
the instruction says outright and which no member can straddle. **Three measurements disagreed because a FOURTH instruction, `mov edx, 1`, is what makes them
agree.**
"""
import io
import sys

TARGET = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"
TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD = '''    /** +0x18, RE 0x0B0084: `mov dword [rbx + 0x18], 1` -- **the MT19937 index, set to 1 after seeding**, which is what the standard seed does. */
    std::uint32_t mtIndex_ = 0;
    /** +0x1C, RE 0x0B00A0: `mov dword [rbx + rdx*4 + 0x18], ecx` for `rdx` from 1 to 0x26F -- **624 words, spanning +0x1C through +0x9DB**. */
    std::uint32_t mt_[624] = {};                      // +0x1C..+0x9DB'''

NEW = '''    /** +0x18, RE 0x0B0084: `mov dword [rbx + 0x18], 1` -- **`mt[0]`, WHICH THE SEEDING SETS TO THE SEED ITSELF.** The standard seed puts the seed in the state's
     *  FIRST word and derives the rest from it, and 0x0B00A0's loop then writes `mt[1]` .. `mt[623]` because **`mov edx, 1` at 0x0B007F starts it at ONE**:
     *  first write +0x18 + 1*4 = +0x1C, last +0x18 + 623*4 = **+0x9D7**. **So the 624 words span +0x18..+0x9D7 and `mti` at +0x9D8 does not overlap them.** */
    std::uint32_t mt_[624] = {};                      // +0x18..+0x9D7'''

OLD_IDX = '''    /** **+0x9E0 AS DECLARED, AND RE 0x0B00B7 WRITES +0x9D8.** The generator's own layout says `mti` is `kMtToMti` = 0x9C0 bytes after `mt`, and `mt` is at +0x1C,
     *  so the instruction's +0x9D8 is 0x9D8 - 0x1C = 0x9BC -- **four bytes short of 0x9C0** -- while a member can only begin at +0x9E0, which is 0x9C4 after.
     *  **Neither fits, the allocation 0x9e0 and the declaration 0x9E8 differ by those eight bytes, and the disagreement is left standing.** */
    std::uint64_t mtIndex8_ = 0;'''

NEW_IDX = '''    /** +0x9D8, RE 0x0B00B7: `mov qword [rbx + 0x9d8], 0x270` -- **EIGHT bytes, and +0x9D8 + 8 = 0x9e0 is exactly what 0x0B004B asks the allocator for.**
     *  The instruction's width is what settles it: a four byte member here would leave the last four bytes of the object unaccounted for. */
    std::uint64_t mtIndex_ = 0;                       // +0x9D8..+0x9DF, and the object ends at 0x9e0'''

TEST_OLD = '''        CHECK(reinterpret_cast<const unsigned char*>(&probe.mt_) - at == 0x1C);          // RE 0x0B00A0: [rbx + rdx*4 + 0x18] with rdx from 1
        CHECK(sizeof(probe.mt_) / sizeof(probe.mt_[0]) == 624);                          // RE 0x0B00A8: cmp rdx, 0x270
        // **THE INDEX AT +0x9D8 IS EIGHT BYTES AND IT OVERLAPS THE LAST WORD OF THE 624.** RE 0x0B00B7 writes `qword [rbx + 0x9d8]` while 0x0B00A0's loop
        // reaches +0x9DB, and `mov ecx, 0x9e0` at 0x0B004B allocates only 0x9e0 -- **so the declaration measures 0x9E8 and the allocation is 0x9e0, a
        // disagreement that is recorded and NOT smoothed over by moving a field.**
        CHECK(reinterpret_cast<const unsigned char*>(&probe.mtIndex8_) - at == 0x9E0);   // while RE 0x0B00B7 writes qword [rbx + 0x9d8]
        CHECK(sizeof(probe.mtIndex8_) == 8);                                             // EIGHT bytes, as that instruction says
        CHECK(sizeof(lcns::RandomSheetSelector) == 0x9E8);                               // while RE 0x0B004B asks for 0x9e0: see the note in tiling.hpp'''

TEST_NEW = '''        // **`mt` IS 624 WORDS FROM +0x18, SETTLED BY THREE INSTRUCTIONS THAT AGREE.** 0x0B0084 writes `dword [rbx + 0x18], 1` -- `mt[0]`, the seed -- and
        // 0x0B007F sets `edx` to 1 before the loop, so 0x0B00A0's `[rbx + rdx*4 + 0x18]` writes `mt[1]` at +0x1C through `mt[623]` at **+0x9D7**.
        CHECK(reinterpret_cast<const unsigned char*>(&probe.mt_) - at == 0x18);          // RE 0x0B0084 writes mt[0] here, and 0x0B00A0 starts at mt[1] = +0x1C
        CHECK(sizeof(probe.mt_) / sizeof(probe.mt_[0]) == 624);                          // RE 0x0B00A8: cmp rdx, 0x270
        // **AND `mti` AT +0x9D8 DOES NOT OVERLAP IT**, because the last word ends at +0x9D7. RE 0x0B00B7 writes EIGHT bytes, and 0x9D8 + 8 = 0x9e0 is exactly
        // `mov ecx, 0x9e0` at 0x0B004B. **The four instructions agree and the earlier reading of +0x18 as an index was the error.**
        CHECK(reinterpret_cast<const unsigned char*>(&probe.mtIndex_) - at == 0x9D8);    // RE 0x0B00B7: mov qword [rbx + 0x9d8], 0x270
        CHECK(sizeof(probe.mtIndex_) == 8);                                              // EIGHT bytes: a four byte member would leave four bytes unexplained
        CHECK(sizeof(lcns::RandomSheetSelector) == 0x9e0);                               // RE 0x0B004B: mov ecx, 0x9e0 -- and it now agrees'''


def main():
    text = io.open(TARGET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "mt[0]` , WHICH THE SEEDING" in text or "WHICH THE SEEDING SETS TO THE SEED ITSELF" in text:
        print("the reading is already corrected")
        return 0
    for old, new, label in ((OLD, NEW, "mt_"), (OLD_IDX, NEW_IDX, "mtIndex_")):
        if old not in text:
            print("REFUSING: the %s declaration is not as expected" % label)
            return 2
    text = text.replace(OLD, NEW, 1).replace(OLD_IDX, NEW_IDX, 1)
    # and the test's own size assertion stops comparing against a disagreement
    text = text.replace('''        // **THE SIZE IS THE MEASURED ONE AND NOT THE ALLOCATED ONE.** RE 0x0B004B asks for 0x9e0; a declaration carrying the offsets the instructions use -- 624
        // words from +0x1C and EIGHT bytes at +0x9D8 -- measures 0x9E8. **The disagreement is asserted rather than smoothed over**: see `mtIndex8_` in
        // tiling.hpp, where the three instructions that cannot all hold of one object are written beside the field.
        static_assert(sizeof(lcns::RandomSheetSelector) == 0x9E8, "measured 0x9E8 against an allocation of 0x9e0 -- see tiling.hpp");''', "", 1)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("tiling.hpp: mt_ is 624 words from +0x18 and mtIndex_ is the eight bytes at +0x9D8")

    body = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "static_assert(sizeof(lcns::RandomSheetSelector) == 0x9E8" in body:
        body = body.replace('''        // **THE SIZE IS THE MEASURED ONE AND NOT THE ALLOCATED ONE.** RE 0x0B004B asks for 0x9e0; a declaration carrying the offsets the instructions use -- 624
        // words from +0x1C and EIGHT bytes at +0x9D8 -- measures 0x9E8. **The disagreement is asserted rather than smoothed over**: see `mtIndex8_` in
        // tiling.hpp, where the three instructions that cannot all hold of one object are written beside the field.
        static_assert(sizeof(lcns::RandomSheetSelector) == 0x9E8, "measured 0x9E8 against an allocation of 0x9e0 -- see tiling.hpp");''',
        '        static_assert(sizeof(lcns::RandomSheetSelector) == 0x9e0, "RE 0x0B004B: mov ecx, 0x9e0 -- and with mt[0] at +0x18 the declaration now measures it");', 1)
    if TEST_OLD not in body:
        print("REFUSING: the test's generator assertions are not as expected")
        return 2
    body = body.replace(TEST_OLD, TEST_NEW, 1)
    body = body.replace("probe.mtIndex8_", "probe.mtIndex_")
    body = body.replace("mtAt + lcns::kMtToMti == 0x9DC", "mtAt + lcns::kMtToMti == 0x9D8")
    body = body.replace("CHECK(indexAt == 0x9E0);", "CHECK(indexAt == 0x9D8);")
    body = body.replace("CHECK(sizeof(lcns::RandomSheetSelector) == 0x9E8);        // against the allocation `mov ecx, 0x9e0` at 0x0B004B",
                        "CHECK(sizeof(lcns::RandomSheetSelector) == 0x9e0);        // and it agrees with `mov ecx, 0x9e0` at 0x0B004B")
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(body)
    print("test_recovered.cpp: the assertions follow the corrected reading")
    return 0


if __name__ == "__main__":
    sys.exit(main())
