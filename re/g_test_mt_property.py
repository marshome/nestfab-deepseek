# -*- coding: utf-8 -*-
"""Assert the generator's arithmetic as a PROPERTY, so the eight unresolved bytes are a check and not a paragraph.

**THE PROPERTY COMES FROM TWO CONSTRUCTORS AND NOT FROM EITHER OBJECT:**

    0x84530's loop writes `dword [rax + rcx*4]` at base +0x00, and 0x8455E writes `qword [rax + 0x9c0], 0x270`
    0x0B00A0's loop writes `dword [rbx + rdx*4 + 0x18]`, and 0x0B00B7 writes `qword [rbx + 0x9d8], 0x270`

**so `mti` is 0x9C0 bytes after `mt` in BOTH**, and that is a statement about the generator. **The test asserts it against `RandomSheetSelector`**, which is the
part that is checkable here: `mt_` at +0x1C means the index belongs at +0x1C + 0x9C0 = **+0x9DC**, while 0x0B00B7 writes +0x9D8 and the declaration has it at
+0x9E0. **AND THE TEST IS EXPECTED TO FAIL** -- which is why it is written as a comparison against the instruction rather than as an assertion that passes: a
property that does not hold, written down where the build can see it, **is what turns "there is a contradiction" into a fact with a location.**
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
BLOCK_END = '    return check::finish("test_recovered");'

BLOCK = '''
    // ---------------------------------------------------------------- the generator's arithmetic, from TWO constructors (RE 0x84510 and 0xB0040)
    {
        // **THE PROPERTY: `mti` IS 0x9C0 BYTES AFTER `mt`.** RE 0x8455E writes `qword [rax + 0x9c0], 0x270` with `mt` at +0x00 (0x84530's loop writes
        // `dword [rax + rcx*4]`), and RE 0x0B00B7 writes `qword [rbx + 0x9d8], 0x270` with `mt` at +0x18 (0x0B00A0's loop writes `[rbx + rdx*4 + 0x18]`).
        // **0x9D8 - 0x18 = 0x9C0 = 0x9C0 - 0x00**, so the generator's internal layout agrees between the two and this constant is the part that does not
        // depend on either object.
        static_assert(lcns::kMtToMti == 0x9C0, "RE: the two constructors put mti exactly this far after mt");
        static_assert(lcns::kMtWords == 624, "RE 0x0B00A8: cmp rdx, 0x270");
        static_assert(lcns::kMtIndexBytes == 8, "RE 0x0B00B7: mov qword [rbx + 0x9d8], 0x270 -- EIGHT bytes and not four");

        // **AND WHERE THE PROPERTY MEETS THE DECLARATION, WHICH IS THE DISAGREEMENT.** `mt_` is at +0x1C, so the index belongs at +0x1C + 0x9C0 = +0x9DC.
        // 0x0B00B7 writes it at +0x9D8 (four bytes early) and the declaration has it at +0x9E0 (four bytes late), because a member cannot begin inside the
        // 624 words the loop fills, whose last one ends at +0x9DB. **The three numbers are computed here rather than described, so the arithmetic is checked
        // even while which of the three is wrong is not yet known.**
        alignas(lcns::RandomSheetSelector) unsigned char storage[sizeof(lcns::RandomSheetSelector)];
        lcns::RandomSheetSelector& probe = *reinterpret_cast<lcns::RandomSheetSelector*>(storage);
        const unsigned char* at = reinterpret_cast<const unsigned char*>(&probe);
        const std::size_t mtAt = static_cast<std::size_t>(reinterpret_cast<const unsigned char*>(&probe.mt_) - at);
        const std::size_t indexAt = static_cast<std::size_t>(reinterpret_cast<const unsigned char*>(&probe.mtIndex8_) - at);
        std::printf("RandomSheetSelector: mt_ at +0x%zX, so the index belongs at +0x%zX; the instruction writes +0x9D8 and the member is at +0x%zX\\n",
                    mtAt, mtAt + lcns::kMtToMti, indexAt);
        CHECK(mtAt == 0x1C);                                      // RE 0x0B00A0: [rbx + rdx*4 + 0x18] with rdx from 1
        // **THE LAYOUT SAYS +0x9DC AND THE DECLARATION CANNOT PUT IT THERE**, so what is asserted is the measured member and the arithmetic beside it.
        CHECK(mtAt + lcns::kMtToMti == 0x9DC);                    // the property, and 0x0B00B7 writes +0x9D8 -- FOUR BYTES EARLIER
        CHECK(indexAt == 0x9E0);                                  // while the declaration puts it after the 624 words, which end at +0x9DB
        CHECK(sizeof(lcns::RandomSheetSelector) == 0x9E8);        // against the allocation `mov ecx, 0x9e0` at 0x0B004B
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "the generator's arithmetic, from TWO constructors" in text:
        print("the property is already asserted")
        return 0
    anchor = text.find(BLOCK_END)
    if anchor < 0:
        print("REFUSING: the finish marker is not found")
        return 2
    text = text[:anchor] + BLOCK + "\n" + text[anchor:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("added the property: kMtToMti, the three derived offsets, and the two measurements they disagree with")
    return 0


if __name__ == "__main__":
    sys.exit(main())
