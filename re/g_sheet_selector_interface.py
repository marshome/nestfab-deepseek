# -*- coding: utf-8 -*-
"""Give `SheetSelector` its TWO REAL METHODS, which the slot bodies name -- so it is an interface rather than a placeholder.

**THE AUDIT WAS RIGHT AND MY DECLARATION WAS THE PROBLEM.** `re/g_full_cpp_audit.py` flagged `tiling.hpp` with "1 placeholder class(es)" for a class that was a
name and a destructor with no members, **and the rule it enforces is the human's: an empty class is a placeholder.** `Nester` is not flagged because it declares
its slots. **I had read four slot bodies and then declared only the destructor.**

**AND SLOT 3 IS A NAME RETURNED BY VALUE.** `Multi::AllSheetSelector`'s slot 3 at 0x7D25E0 is

    7D25E0  lea rdx, [rcx + 0x10]          ; a buffer INSIDE the returned object, at +0x10 -- the small-string form
    7D25E7  mov qword [rcx], rdx           ; +0x00 points at it
    7D25EA  movabs rcx, 0x74656568536c6c41 ; "AllSheet"
    7D25F4  mov qword [rax + 0x10], rcx    ; the bytes, at +0x10
    7D25F8  mov byte [rax + 0x18], 0x73    ; 's'
    7D25FC  mov qword [rax + 8], 9         ; +0x08 is the LENGTH, 9
    7D2604  mov byte [rax + 0x19], 0

**so it returns `std::string` and its content is `"AllSheets"`.** `Multi::LargestSheetSelector`'s slot 3 at 0x7D3CE0 is the same shape with
`movabs rcx, 0x537473656772614c` = "Largest", a `dword [rax + 0x18] = 0x74656568` = "heet" and `qword [rax + 8] = 0xc` = 12, so `"LargestSheet"` -- **12 characters,
and the LENGTH field is what proves the reading and not the register dump.**

**AND SLOT 2 USES THE SAME RETURN-BUFFER CONVENTION** -- `mov r12, rcx` then writes at `[rcx]`, `[rcx + 8]` and `[rcx + 0x10]` -- which is three words and
therefore a `std::vector`, **not the three object fields an earlier probe reported.** Its element type is not established, so the declaration says `std::size_t`
and marks it.
"""
import io
import sys

TARGET = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"

OLD = '''/** **A FOUR SLOT INTERFACE, AND THE BASE ITSELF HAS NO VTABLE INSTANCE** -- the RTTI carries `N5Multi13SheetSelectorE` and `re/vtables.json` has no table for it,
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
};'''

NEW = '''/** **A FOUR SLOT INTERFACE, AND THE BASE ITSELF HAS NO VTABLE INSTANCE** -- the RTTI carries `N5Multi13SheetSelectorE` and `re/vtables.json` has no table for it,
 *  which is what an abstract base with no out-of-line constructor looks like. Every subclass's table is
 *
 *      slot 0  the deleting destructor          `jmp 0x9984B0`
 *      slot 1  the destructor
 *      slot 2  the selection                    FILLS THE BUFFER THE CALLER PASSES
 *      slot 3  the selector's NAME              also returns through that buffer
 *
 *  **AND SLOT 2'S `rcx` IS THE BUFFER AND NOT `this`**: `Multi::AllSheetSelector`'s body begins `mov r12, rcx` (the object) and then `mov qword [rcx], 0`,
 *  `[rcx + 8]` and `[rcx + 0x10]` -- **three stores into the CALLER'S memory**, which an earlier probe read as three of the object's own fields. **That is why
 *  the object register is established before any offset is believed.**
 *
 *  **AND SLOT 3'S CONTENT IS A NAME.** RE `Multi::AllSheetSelector` 0x7D25E0 and `Multi::LargestSheetSelector` 0x7D3CE0: each builds the three word
 *  small-string form with the bytes at +0x10 and **the LENGTH at +0x08** -- 9 for `"AllSheets"` and **0xc for `"LargestSheet"`**, which is twelve characters. */
class SheetSelector {
public:
    virtual ~SheetSelector() = default;

    /** Slot 2. **RETURNED THROUGH A BUFFER THE CALLER SUPPLIES**, which is the three word `std::vector` form: `[rcx]`, `[rcx + 8]` and `[rcx + 0x10]` are
     *  initialised and the object is returned by `ret`. **The element type is NOT established** -- the bodies index sheets, not indices -- so it is declared as
     *  `std::size_t` and marked, rather than guessed at. */
    virtual std::vector<std::size_t> select() const = 0;      // NOT REVERSED: the element type
    /** Slot 3. RE 0x7D25E0 and 0x7D3CE0, and the length field at +0x08 settling it: `"AllSheets"` and `"LargestSheet"`. */
    virtual std::string name() const = 0;
};'''


def main():
    text = io.open(TARGET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "virtual std::string name() const = 0;" in text:
        print("the interface already declares its two methods")
        return 0
    if OLD not in text:
        print("REFUSING: the SheetSelector block is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("SheetSelector now declares select() and name(), both from slot bodies with their addresses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
