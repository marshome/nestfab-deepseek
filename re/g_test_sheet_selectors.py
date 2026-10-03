# -*- coding: utf-8 -*-
"""Test the two new classes the one way that is available: the interface's shape, and the LAYOUT its constructor establishes.

**THE TEST CANNOT CONSTRUCT `NoMixSheetSelector`**, because its constructor is the module's and has no C++ body here -- so what is asserted is what a
declaration can be held to:

  * **THE INTERFACE HAS TWO METHODS AND A VIRTUAL DESTRUCTOR**, which RE 0x7D25E0 and 0x7D3CE0 put in slots 2 and 3 behind the destructor pair;
  * **`NoMixSheetSelector`'s FIELDS ARE AT THE OFFSETS ITS CONSTRUCTOR WRITES**, because that is a property of the declaration and 0xAFD60 is the evidence;
  * **AND ITS SIZE IS THE 0x50 BYTES 0xAFD70 ALLOCATES**, which is the assertion that closes the layout: the parts are +0x00 the vptr, +0x08, +0x10, +0x18,
    **a 0x18 byte sub-object at +0x20** and **a 0x18 byte sub-object at +0x38**, and 0x38 + 0x18 = 0x50.
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
BLOCK_END = '    return check::finish("test_recovered");'

BLOCK = '''
    // ---------------------------------------------------------------- the sheet-selector family (RE 0xAFD60 and the four tables)
    {
        // **THE INTERFACE'S SHAPE.** RE 0x7D25E0 and 0x7D3CE0 are slot 3 of two tables: each builds the three word small-string form with the length at +0x08,
        // 9 for "AllSheets" and 0xc for "LargestSheet". **The classes are abstract, which is what an interface with no out-of-line constructor looks like** --
        // `N5Multi13SheetSelectorE` is in the RTTI and `re/vtables.json` has no table for it.
        static_assert(std::is_abstract<lcns::SheetSelector>::value, "the base has no vtable instance, so it must be abstract");
        static_assert(std::has_virtual_destructor<lcns::SheetSelector>::value, "slots 0 and 1 of every table are the deleting destructor and the destructor");

        // **AND `NoMixSheetSelector`'S SIZE IS WHAT ITS CONSTRUCTOR ALLOCATES.** RE 0xAFD70 `mov ecx, 0x50` is the only allocation size in 0xAFD60, and the two
        // sub-objects it builds -- at +0x20 by 0x523FE0 and at +0x38 by 0xAF7D0 -- are 0x18 bytes each, because each of those functions touches `rbp` at +0x0
        // and +0x10 and nothing else. **0x38 + 0x18 = 0x50, so a wrong declaration cannot fit.**
        static_assert(sizeof(lcns::NoMixSheetSelector) == 0x50, "RE 0xAFD70 allocates 0x50 and the parts must sum to it");
        static_assert(std::has_virtual_destructor<lcns::NoMixSheetSelector>::value, "RE 0xAFD98 installs a vtable, so it is polymorphic");

        // **AND THE FOUR FIELD OFFSETS, WHICH IS THE PART A SIZE ALONE WOULD NOT CATCH** -- a transposed pair of same-sized members keeps the size and moves the
        // offsets. Each is one store in 0xAFD60: +0x08 at 0xAFD89, +0x10 at 0xAFD94, +0x18 at 0xAFD9B with the source CLEARED at 0xAFDA3, +0x20 at 0xAFD9F.
        lcns::NoMixSheetSelector* probe = nullptr;    // only for offsetof, which needs no object
        CHECK(offsetof(lcns::NoMixSheetSelector, firstArg_) == 0x08);   // RE 0xAFD89: mov qword [rax + 8], rsi
        CHECK(offsetof(lcns::NoMixSheetSelector, thirdArg_) == 0x10);   // RE 0xAFD94: mov dword [rbx + 0x10], r12d
        CHECK(offsetof(lcns::NoMixSheetSelector, owned18_) == 0x18);    // RE 0xAFD9B and 0xAFDA3: a moved-from pointer
        CHECK(offsetof(lcns::NoMixSheetSelector, member20_) == 0x20);   // RE 0xAFD9F: lea rcx, [rbx + 0x20]
        CHECK(offsetof(lcns::NoMixSheetSelector, member38_) == 0x38);   // RE 0xAFDB4: lea rcx, [rbx + 0x38]
        CHECK(sizeof(lcns::NoMixSheetSelector::member20_) == 0x18);     // 0x523FE0 touches rbp at +0x0 and +0x10 only
        CHECK(sizeof(lcns::NoMixSheetSelector::member38_) == 0x18);     // 0xAF7D0 touches rbp at +0x0 and +0x10 only
        (void)probe;
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "the sheet-selector family" in text:
        print("the family already has a test")
        return 0
    anchor = text.find(BLOCK_END)
    if anchor < 0:
        print("REFUSING: the finish marker is not found")
        return 2
    text = text[:anchor] + BLOCK + "\n" + text[anchor:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("added the family's test: the interface's shape, the size 0xAFD70 allocates, and five offsets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
