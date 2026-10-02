# -*- coding: utf-8 -*-
"""Add the NestingNester fields test."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- Multi::NestingNester's fields (RE 0x342E0)
    //
    // One instruction per position, and the constructor is the best source because it sets its object register once: 0x342EC mov rbx,rcx
    // and 0x343F1 pop rbx, with nothing writing rbx in between.
    {
        CHECK(lcns::kNestingNesterCtorAddress == 0x342E0u);
        CHECK(lcns::kNestingNesterCtorBytes == 422u);
        CHECK(lcns::kNestingNesterVtableField == 0x00u);

        std::size_t count = 0;
        const lcns::FieldStore* fields = lcns::nestingNesterCtorFields(count);
        CHECK(count == 8u);                             // eight stores, seven distinct offsets

        // every offset has an instruction, and the instruction is inside the constructor
        for (std::size_t i = 0; i < count; ++i) {
            CHECK(fields[i].address >= lcns::kNestingNesterCtorAddress);
            CHECK(fields[i].address < lcns::kNestingNesterCtorAddress + lcns::kNestingNesterCtorBytes);
            CHECK(fields[i].width != nullptr);
        }

        // the offsets themselves, in order, and the duplicate at 0x30 which is two stores rather than two fields
        CHECK(fields[0].offset == 0x000u);
        CHECK(fields[1].offset == 0x018u);
        CHECK(fields[2].offset == 0x020u);
        CHECK(fields[3].offset == 0x028u);
        CHECK(fields[4].offset == 0x030u);
        CHECK(fields[5].offset == 0x030u);              // RE 0x343E3 sets the same offset from xmm6
        CHECK(fields[6].offset == 0x038u);
        CHECK(fields[7].offset == 0x9F8u);              // RE 0x3436D: 0x270, which is 624

        // the vtable is installed first and at offset 0, which is what makes it the object's first quadword
        CHECK(fields[0].offset == lcns::kNestingNesterVtableField);
        CHECK(fields[0].address == 0x34308u);           // RE 0x34308: mov [rbx], rax

        // 0x30 is written twice and the SECOND write is a double, which is the evidence that the field is a double rather than a pointer
        CHECK(std::string(fields[4].width) == "qword");
        CHECK(std::string(fields[5].width) == "qword");
        CHECK(std::string(fields[5].note).find("DOUBLE") != std::string::npos);

        // the smallest and largest offsets, which bound the class's own storage that the constructor names
        CHECK(fields[0].offset == 0u);
        CHECK(fields[7].offset == 0x9F8u);

        // and slot 2's contribution, which the same scan found after 0x3311F made rbp the object
        std::size_t slot2Count = 0;
        const lcns::FieldStore* slot2 = lcns::nestingNesterSlot2Fields(slot2Count);
        CHECK(slot2Count == 3u);
        for (std::size_t i = 0; i < slot2Count; ++i) {
            CHECK(slot2[i].address >= 0x33100u);
            CHECK(slot2[i].address < 0x33100u + 2240u);
        }
        // and the two sets agree about the vtable pointer being at 0
        CHECK(slot2[0].offset == fields[0].offset);
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "nestingNesterCtorFields" in text:
        print("already present")
        return 0
    if '#include "lcns/nesting_nester_fields.hpp"' not in text:
        anchor = '#include "lcns/vtable_layout.hpp"\n'
        assert anchor in text, "the vtable_layout include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/nesting_nester_fields.hpp"\n', 1)
        print("include added")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("NestingNester fields test added; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
