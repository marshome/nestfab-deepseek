# -*- coding: utf-8 -*-
"""Put the generator's arithmetic NEXT TO THE FIELD, as a constexpr helper, and mark the unresolved eight bytes as unresolved.

**WHAT IS SETTLED, AND IT IS THE ARITHMETIC RATHER THAN THE OFFSET:** the two constructors place the generator identically.

    0x84510 (0x9f8 byte object, 0x9F8 is `mov ecx, 0x9f8` at 0x084519)   mt at +0x00,  mti written EIGHT bytes at +0x9C0
    0xB0040 (0x9e0 byte object, 0x9E0 is `mov ecx, 0x9e0` at 0x0B004B)  mt at +0x18,  mti written EIGHT bytes at +0x9D8

**and 0x9D8 - 0x18 = 0x9C0**, so the generator's internal layout agrees between the two and its `mti` sits **0x9C0 bytes after `mt`**. **That is a fact about the
generator and it does not depend on either object.**

**AND THE EIGHT BYTES ARE STILL UNRESOLVED.** In `RandomSheetSelector` the loop's last word ends at +0x9DB while the eight bytes start at +0x9D8, so four bytes
overlap and the member can only begin at +0x9E0 -- **0x9E8 in total against an allocation of 0x9e0.** The resolved shape is written as `constexpr` arithmetic on
the two offsets that ARE settled, so the next round can see the disagreement without recomputing it: **a helper that cannot be made to equal the allocation is a
better record of the problem than a comment saying there is one.**
"""
import io
import sys

TARGET = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"

OLD = '''/** RE 0xB0040 (159 bytes). **THE OBJECT IS 0x9e0 BYTES AND MOST OF IT IS A `std::mt19937`**'''

NEW = '''/** **THE GENERATOR'S TWO OFFSETS ARE SETTLED AND THE OBJECT'S EIGHT TRAILING BYTES ARE NOT.** Two constructors place the same generator and a `constexpr`
 *  difference between them is the part that does not depend on either object:
 *
 *      0x84510   0x9f8 byte object (`mov ecx, 0x9f8` at 0x084519)   mt at +0x00, mti written EIGHT bytes at +0x9C0
 *      0xB0040   0x9e0 byte object (`mov ecx, 0x9e0` at 0x0B004B)   mt at +0x18, mti written EIGHT bytes at +0x9D8
 *
 *  **and +0x9D8 - +0x18 = +0x9C0**, so `mti` sits 0x9C0 bytes after `mt` in both. **What is NOT settled is where `RandomSheetSelector`'s object ends**: the
 *  loop's 624 words reach +0x9DB, the eight bytes begin at +0x9D8, and a member can only begin at +0x9E0 -- **0x9E8 against an allocation of 0x9e0.** */
inline constexpr std::size_t kMtToMti = 0x9C0;                       // RE: 0x9D8 - 0x18, and 0x9C0 - 0x00 in the other constructor
inline constexpr std::size_t kMtWords = 0x270;                       // RE 0x0B00A8 `cmp rdx, 0x270`: 624 words
inline constexpr std::size_t kMtIndexBytes = 8;                      // RE 0x0B00B7 `mov qword [rbx + 0x9d8], 0x270`

/** RE 0xB0040 (159 bytes). **THE OBJECT IS 0x9e0 BYTES AND MOST OF IT IS A `std::mt19937`**'''

OLD_FIELD = '''    std::uint64_t mtIndex8_ = 0;                      // **+0x9E0 AS DECLARED, and RE 0x0B00B7 writes +0x9D8 -- see the note above**'''

NEW_FIELD = '''    /** **+0x9E0 AS DECLARED, AND RE 0x0B00B7 WRITES +0x9D8.** The generator's own layout says `mti` is `kMtToMti` = 0x9C0 bytes after `mt`, and `mt` is at +0x1C,
     *  so the instruction's +0x9D8 is 0x9D8 - 0x1C = 0x9BC -- **four bytes short of 0x9C0** -- while a member can only begin at +0x9E0, which is 0x9C4 after.
     *  **Neither fits, the allocation 0x9e0 and the declaration 0x9E8 differ by those eight bytes, and the disagreement is left standing.** */
    std::uint64_t mtIndex8_ = 0;'''


def main():
    text = io.open(TARGET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "kMtToMti" in text:
        print("the arithmetic is already beside the fields")
        return 0
    if OLD not in text or OLD_FIELD not in text:
        print("REFUSING: the anchors are not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    text = text.replace(OLD_FIELD, NEW_FIELD, 1)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("tiling.hpp: the settled arithmetic is constexpr and the unresolved eight bytes are marked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
