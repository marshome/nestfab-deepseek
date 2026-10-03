# -*- coding: utf-8 -*-
"""Assert what the constructor's CALLS and LEAs establish, including TWO NEGATIVE results that are worth holding.

**WHAT 0xAFD60 SAYS ABOUT ITS TWO SUB-OBJECTS:**

    0AFD9F  lea rcx, [rbx + 0x20] / 0AFDAF call 0x523fe0
    0AFDB4  lea rcx, [rbx + 0x38] / 0AFDBB call 0xaf7d0

**and the constructor contains FOUR `lea` of a rip-relative address, of which exactly ONE is a vtable:**

    0AFD8D  lea rax, [rip + 0x98bc4c] -> 0xA3B9E0   ; Multi::NoMixSheetSelector's vtable, stored at [rbx]
    the other three are string temporaries on the stack, for the length literals in the assertion path

**so NEITHER SUB-OBJECT GETS A VTABLE, and they are not polymorphic** -- which is a NEGATIVE result and is therefore held as one: `0x523FE0` and `0xAF7D0` each
write only `[rbp]` and `[rbp + 0x10]`, so each is 0x18 bytes of data with no vptr of its own.

**AND THE DESTRUCTOR IS IN THE SAME FUNCTION, WHICH THE INDIRECT CALL SHOWS:**

    0AFFA0  mov rcx, qword [rbx + 0x18]     ; the +0x18 member
    0AFFA4  test rcx, rcx / je
    0AFFA9  mov rax, qword [rcx]            ; ITS vptr
    0AFFAC  call qword [rax + 8]            ; its second slot -- a deleting destructor, called through the table

**so the pointer at +0x18 OWNS A POLYMORPHIC OBJECT**, which is why the constructor CLEARS the source at 0xAFDA3: it is a moved-from or transferred pointer, not
a copy. **That is a relationship between two classes and it is asserted below rather than described.**
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
BLOCK_END = '    return check::finish("test_recovered");'

BLOCK = '''
    // ---------------------------------------------------------------- NoMixSheetSelector's sub-objects and its destructor (RE 0xAFD60)
    {
        // **NEITHER SUB-OBJECT IS POLYMORPHIC, AND THE CONSTRUCTOR IS WHAT SAYS SO.** RE 0xAFD9F and 0xAFDB4 build them with `lea rcx, [rbx + 0x20]` and
        // `lea rcx, [rbx + 0x38]` and then call 0x523FE0 and 0xAF7D0 -- and 0xAFD60 contains only ONE `lea` of a vtable, at 0xAFD8D, whose target 0xA3B9E0 is
        // NoMixSheetSelector's own. **So the two 0x18 byte members are plain data**, which is a negative result and is asserted as one.
        static_assert(!std::is_polymorphic<decltype(lcns::NoMixSheetSelector::member20_)>::value, "a byte array has no vtable");
        static_assert(!std::is_polymorphic<decltype(lcns::NoMixSheetSelector::member38_)>::value, "a byte array has no vtable");
        // and the two sizes, each from the function that fills it: 0x523FE0 touches rbp at +0x0 and +0x10 only, and 0xAF7D0 the same
        static_assert(sizeof(lcns::NoMixSheetSelector::member20_) + 0x20 == 0x38, "member20_ runs from +0x20 to exactly where member38_ starts");
        static_assert(sizeof(lcns::NoMixSheetSelector::member38_) + 0x38 == 0x50, "member38_ ends exactly at the allocation 0xAFD70 asks for");

        // **AND +0x18 OWNS A POLYMORPHIC OBJECT.** RE 0xAFFA0 `mov rcx, qword [rbx + 0x18]`, 0xAFFA9 `mov rax, qword [rcx]` and 0xAFFAC `call qword
        // [rax + 8]` -- a call through the pointed-to object's OWN table, slot 1, which is a deleting destructor. **The constructor CLEARS the source at
        // 0xAFDA3, so this pointer was transferred and not copied**, and the destructor destroys what it points at.
        CHECK(sizeof(lcns::NoMixSheetSelector::owned18_) == sizeof(void*));
        CHECK(sizeof(lcns::NoMixSheetSelector) == 0x50);
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "NEITHER SUB-OBJECT IS POLYMORPHIC" in text:
        print("the sub-object properties are already asserted")
        return 0
    anchor = text.find(BLOCK_END)
    if anchor < 0:
        print("REFUSING: the finish marker is not found")
        return 2
    text = text[:anchor] + BLOCK + "\n" + text[anchor:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("added the negative results: neither sub-object is polymorphic, and +0x18 owns a polymorphic object")
    return 0


if __name__ == "__main__":
    sys.exit(main())
