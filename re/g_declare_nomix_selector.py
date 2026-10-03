# -*- coding: utf-8 -*-
"""Declare `Multi::SheetSelector` and `NoMixSheetSelector` from its constructor, which is the first class in the family with one.

**THE CONSTRUCTOR IS 0xAFD60, 671 BYTES, AND IT IS DECISIVE**: it allocates ONCE, installs the vtable, and initialises every field.

    0AFD6D  mov rdi, rcx                       ; the destination the caller passes
    0AFD70  mov ecx, 0x50                      ; THE OBJECT IS 0x50 BYTES -- the only size in the function
    0AFD7E  call 0x998500                      ; allocate
    0AFD86  mov rbx, rax                       ; rbx IS the object; rcx is a DESTINATION and not `this`
    0AFD89  mov qword [rax + 8], rsi           ; +0x08 = the first parameter
    0AFD8D  lea rax, [rip + 0x98bc4c]          ; -> 0xA3B9E0, i.e. Multi::NoMixSheetSelector
    0AFD94  mov dword [rbx + 0x10], r12d       ; +0x10 = the third parameter, FOUR bytes
    0AFD98  mov qword [rbx], rax               ; +0x00 = the vtable
    0AFD9B  mov rax, qword [rbp]               ; +0x18 takes OWNERSHIP of what r9 points at
    0AFDA3  mov qword [rbp], 0                 ; ... and CLEARS the source, so it is a moved-from pointer
    0AFDAB  mov qword [rbx + 0x18], rax
    0AFD9F  lea rcx, [rbx + 0x20] / 0AFDAF call 0x523fe0    ; a sub-object AT +0x20
    0AFDB4  lea rcx, [rbx + 0x38] / 0AFDBB call 0xaf7d0    ; and ONE MORE AT +0x38
    0AFDCA  mov qword [rdi], rbx               ; the caller receives the pointer

**AND THE ARITHMETIC CLOSES**: 0x523FE0 touches `rbp` at +0x0 and +0x10 only, so the sub-object at +0x20 is 0x18 bytes and reaches 0x38; 0xAF7D0 touches `rbp`
at +0x0 and +0x10 only, so the one at +0x38 is 0x18 bytes and reaches **0x50, which is exactly what was allocated.** **A layout whose parts sum to the allocation
is a layout with nothing missing and nothing invented.**

**AND THE NAMES ARE NOT RECOVERED, WHICH IS SAID RATHER THAN WORKED AROUND.** The module's strings name the class -- `N5Multi18NoMixSheetSelectorE` -- and name
none of its six fields, and the two sub-objects are built by 0x523FE0 and 0xAF7D0 whose own types the RTTI does not carry here. **So the members are typed and
placed and their names are the CLASS's plus the offset, with `not_reversed` marking the three that carry no name at all.**
"""
import io
import sys

TARGET = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"

BLOCK = '''
// ---------------------------------------------------------------------------
// The sheet-selector family -- RE: 0xAFD60 (NoMixSheetSelector's constructor), vtables 0xA3B840 / 0xA3B9D0 / 0xA3BA60 / 0xA3BAC0
// ---------------------------------------------------------------------------

/** **A FOUR SLOT INTERFACE, AND THE BASE ITSELF HAS NO VTABLE INSTANCE** -- the RTTI carries `N5Multi13SheetSelectorE` and `re/vtables.json` has no table for it,
 *  which is what an abstract base with no out-of-line constructor looks like. Every subclass's table is
 *
 *      slot 0  the deleting destructor, `jmp 0x9984B0`
 *      slot 1  the destructor
 *      slot 2  the selection, which FILLS A BUFFER THE CALLER PASSES
 *      slot 3  a predicate, 41 to 193 bytes
 *
 *  **AND SLOT 2'S `rcx` IS THAT BUFFER AND NOT `this`**: `Multi::AllSheetSelector`'s body begins `mov r12, rcx` (the object) and then `mov qword [rcx], 0`,
 *  `[rcx + 8]` and `[rcx + 0x10]` -- **three stores into the CALLER'S memory**, which an earlier probe read as three of the object's own fields. **That is why
 *  the object register is established before any offset is believed.** No claim about the base's methods is made here: **no member and no slot body of the base
 *  has been read, so it is an interface and nothing more.** */
class SheetSelector {
public:
    virtual ~SheetSelector() = default;
};

/** RE 0xAFD60 (671 bytes). **THE OBJECT IS 0x50 BYTES AND ITS PARTS SUM TO EXACTLY THAT**, which is what makes this class landable where its three siblings are
 *  not: `LargestSheetSelector` and `RandomSheetSelector` are built by 0xB0000 and 0xB0040, whose allocations are 0x10 and 0x9e0, and their tables' install sites
 *  are not in the profile. Six fields are placed below and ONE constructor initialises all of them.
 *
 *  **THREE OF THE SIX CARRY NO NAME, BECAUSE THE MODULE GIVES NONE.** `N5Multi18NoMixSheetSelectorE` names the class and no member string names these; the two
 *  sub-objects at +0x20 and +0x38 are built by 0x523FE0 and 0xAF7D0, whose own types this project has not read. **Their offsets, types and constructors are
 *  established and their meanings are not**, so they are named for what is known and marked. */
class NoMixSheetSelector : public SheetSelector {
public:
    /** RE 0xAFD60, and every line below is one store in it. The constructor takes a destination, a pointer, an int and a pointer, allocates 0x50 bytes,
     *  installs the vtable, and returns the object through the destination. */
    NoMixSheetSelector(void** destination);

    // +0x00  RE 0xAFD98: mov qword [rbx], rax, where rax is 0xA3B9E0 -- NoMixSheetSelector's vtable

    /** +0x08, RE 0xAFD89: `mov qword [rax + 8], rsi` -- the constructor's FIRST parameter, a pointer. */
    void* firstArg_ = nullptr;
    /** +0x10, RE 0xAFD94: `mov dword [rbx + 0x10], r12d` -- the constructor's THIRD parameter, FOUR bytes. */
    std::uint32_t thirdArg_ = 0;
    /** +0x18, RE 0xAFD9B and 0xAFDAB: `mov rax, qword [rbp]` then `mov qword [rbp], 0` then `mov qword [rbx + 0x18], rax`
     *  -- **the source is CLEARED, so this is a moved-from pointer and not a copy.** */
    void* owned18_ = nullptr;
    /** +0x20, RE 0xAFD9F `lea rcx, [rbx + 0x20]` and 0xAFDAF `call 0x523FE0`. **0x18 BYTES**, because 0x523FE0 touches `rbp` at +0x0 and +0x10 and nothing else,
     *  so it reaches +0x38. **Its meaning is not recovered.** */
    std::byte member20_[0x18];                        // NOT REVERSED: a sub-object constructed by 0x523FE0
    /** +0x38, RE 0xAFDB4 `lea rcx, [rbx + 0x38]` and 0xAFDBB `call 0xAF7D0`. **0x18 BYTES**, and 0x38 + 0x18 = 0x50, which is exactly the allocation. */
    std::byte member38_[0x18];                        // NOT REVERSED: a sub-object constructed by 0xAF7D0
};
'''


def main():
    text = io.open(TARGET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "class NoMixSheetSelector" in text:
        print("the class is already declared")
        return 0
    if "#pragma once" not in text:
        print("REFUSING: tiling.hpp does not look like the expected header")
        return 2
    # the block goes before the first class that follows the include guard and its includes
    anchor = text.find("\nclass ")
    anchor = text.find("\nclass ", anchor + 1) if anchor >= 0 else -1
    if anchor < 0:
        print("REFUSING: no class declaration found to insert before")
        return 2
    text = text[:anchor] + "\n" + BLOCK + text[anchor:]
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("declared SheetSelector and NoMixSheetSelector in tiling.hpp")
    return 0


if __name__ == "__main__":
    sys.exit(main())
