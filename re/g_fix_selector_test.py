# -*- coding: utf-8 -*-
"""Replace `offsetof` with a POINTER DIFFERENCE, because a polymorphic class is not standard-layout.

**THE WARNING IS CORRECT AND IT IS NOT COSMETIC**: `offsetof` within a non-standard-layout type is conditionally-supported and GCC says so. **A class with a
vtable is exactly that**, so the five offset assertions move to

    reinterpret_cast<const unsigned char*>(&object.field) - reinterpret_cast<const unsigned char*>(&object)

which is the form the node-family test already uses and which needs a real object rather than `offsetof`'s null. **The object is a `union`-free POD-free
`alignas` array here, so the assertion keeps its meaning and loses the extension.**
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD = '''        lcns::NoMixSheetSelector* probe = nullptr;    // only for offsetof, which needs no object
        CHECK(offsetof(lcns::NoMixSheetSelector, firstArg_) == 0x08);   // RE 0xAFD89: mov qword [rax + 8], rsi
        CHECK(offsetof(lcns::NoMixSheetSelector, thirdArg_) == 0x10);   // RE 0xAFD94: mov dword [rbx + 0x10], r12d
        CHECK(offsetof(lcns::NoMixSheetSelector, owned18_) == 0x18);    // RE 0xAFD9B and 0xAFDA3: a moved-from pointer
        CHECK(offsetof(lcns::NoMixSheetSelector, member20_) == 0x20);   // RE 0xAFD9F: lea rcx, [rbx + 0x20]
        CHECK(offsetof(lcns::NoMixSheetSelector, member38_) == 0x38);   // RE 0xAFDB4: lea rcx, [rbx + 0x38]
        CHECK(sizeof(lcns::NoMixSheetSelector::member20_) == 0x18);     // 0x523FE0 touches rbp at +0x0 and +0x10 only
        CHECK(sizeof(lcns::NoMixSheetSelector::member38_) == 0x18);     // 0xAF7D0 touches rbp at +0x0 and +0x10 only
        (void)probe;'''

NEW = '''        // **AND THE FIVE OFFSETS, WHICH A SIZE ALONE WOULD NOT CATCH** -- a transposed pair of same-sized members keeps the size and moves the offsets. Each
        // is one store in 0xAFD60: +0x08 at 0xAFD89, +0x10 at 0xAFD94, +0x18 at 0xAFD9B with the source CLEARED at 0xAFDA3, +0x20 at 0xAFD9F and +0x38 at
        // 0xAFDB4. **A POINTER DIFFERENCE RATHER THAN `offsetof`**, because a class with a vtable is not standard-layout and GCC warns about the extension.
        alignas(lcns::NoMixSheetSelector) unsigned char storage[sizeof(lcns::NoMixSheetSelector)];
        lcns::NoMixSheetSelector& probe = *reinterpret_cast<lcns::NoMixSheetSelector*>(storage);
        const unsigned char* at = reinterpret_cast<const unsigned char*>(&probe);
        CHECK(reinterpret_cast<const unsigned char*>(&probe.firstArg_) - at == 0x08);   // RE 0xAFD89: mov qword [rax + 8], rsi
        CHECK(reinterpret_cast<const unsigned char*>(&probe.thirdArg_) - at == 0x10);   // RE 0xAFD94: mov dword [rbx + 0x10], r12d
        CHECK(reinterpret_cast<const unsigned char*>(&probe.owned18_) - at == 0x18);    // RE 0xAFD9B and 0xAFDA3: a moved-from pointer
        CHECK(reinterpret_cast<const unsigned char*>(&probe.member20_) - at == 0x20);   // RE 0xAFD9F: lea rcx, [rbx + 0x20]
        CHECK(reinterpret_cast<const unsigned char*>(&probe.member38_) - at == 0x38);   // RE 0xAFDB4: lea rcx, [rbx + 0x38]
        CHECK(sizeof(lcns::NoMixSheetSelector::member20_) == 0x18);     // 0x523FE0 touches rbp at +0x0 and +0x10 only
        CHECK(sizeof(lcns::NoMixSheetSelector::member38_) == 0x18);     // 0xAF7D0 touches rbp at +0x0 and +0x10 only'''

# and drop the now-duplicated sentence above, so the block does not say the same thing twice
DUP = '''        // **AND THE FOUR FIELD OFFSETS, WHICH IS THE PART A SIZE ALONE WOULD NOT CATCH** -- a transposed pair of same-sized members keeps the size and moves the
        // offsets. Each is one store in 0xAFD60: +0x08 at 0xAFD89, +0x10 at 0xAFD94, +0x18 at 0xAFD9B with the source CLEARED at 0xAFDA3, +0x20 at 0xAFD9F.
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "offsetof(lcns::NoMixSheetSelector" not in text and "alignas(lcns::NoMixSheetSelector)" in text:
        print("the assertions already use a pointer difference")
        return 0
    if OLD not in text:
        print("REFUSING: the offsetof block is not as expected")
        return 2
    text = text.replace(DUP, "", 1)
    text = text.replace(OLD, NEW, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("the five offsets are asserted by pointer difference, so no extension is used")
    return 0


if __name__ == "__main__":
    sys.exit(main())
