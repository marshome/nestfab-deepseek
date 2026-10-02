# -*- coding: utf-8 -*-
"""Test the records written as structs, which is the conversion the human asked for."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
ANCHOR = '    return check::finish("test_recovered");'

BLOCK = '''
    // ---------------------------------------------------------------- records as STRUCTS (converted from layout.hpp's offsets)
    //
    // layout.hpp is 3389 lines of `inline constexpr std::size_t` with an instruction on each and not one `struct`. **Offsets with
    // instructions are good evidence and a poor deliverable.** These two records say what they ARE, with the instruction on each member, and
    // the offsets are the struct's own rather than a list beside it.
    {
        // the 0x60 byte polymorphic record
        lcns::PolymorphicRecord record{};
        CHECK(offsetof(lcns::PolymorphicRecord, vtable) == 0x00u);      // RE 0x6DE4F5
        CHECK(offsetof(lcns::PolymorphicRecord, wordA) == 0x08u);       // RE 0x6DE4E7
        CHECK(offsetof(lcns::PolymorphicRecord, wordB) == 0x0Cu);       // RE 0x6DE4EE
        CHECK(offsetof(lcns::PolymorphicRecord, wordB) - offsetof(lcns::PolymorphicRecord, wordA) == 4u);
        CHECK(sizeof(lcns::PolymorphicRecord) == 0x60u);                // RE 0x6DE4D0
        CHECK(lcns::PolymorphicRecord::kVtableRva == 0x35E739u);        // RE 0x6DE4E0

        // the fields can be SET, which a list of offsets cannot do, and the unplaced region is named as such
        record.wordA = 7;
        record.wordB = 9;
        CHECK(record.wordA == 7u && record.wordB == 9u);
        CHECK(sizeof(record.unplaced) == 0x60u - 0x10u);

        // the 240 byte record the walk advances by
        lcns::RunRecord run{};
        CHECK(offsetof(lcns::RunRecord, value) == 0x18u);               // kRecordValueOffset
        CHECK(offsetof(lcns::RunRecord, wide) == 0x20u);                // kRecordWideOffset
        CHECK(offsetof(lcns::RunRecord, flag) == 0x28u);                // kRecordFlagOffset
        CHECK(sizeof(lcns::RunRecord) == 0xF0u);                        // kRunRecordStride
        CHECK(lcns::RunRecord::kStride == 0xF0u);
        run.value = 42;
        run.flag = 1;
        CHECK(run.value == 42u && run.flag == 1u);
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "PolymorphicRecord" in text:
        print("already present")
        return 0
    include = '#include "lcns/records.hpp"\n'
    if include not in text:
        anchor = '#include "lcns/nesting_nester_layout.hpp"\n'
        assert anchor in text, "the nesting_nester_layout include is gone"
        text = text.replace(anchor, anchor + include, 1)
        print("include added")
    text = text.replace(ANCHOR, BLOCK + "\n" + ANCHOR, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("records test added; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
