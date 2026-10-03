# -*- coding: utf-8 -*-
"""Declare the two 0x10-byte Canceller-family objects the Supervisor allocates, and CORRECT the placement I got wrong.

**WHAT EACH ONE IS, AND BOTH ARE THE SAME SHAPE:**

    0x3290C  lea rax, [rip + 0xa0909d]   ; 0x32913 + 0xA0909D = 0xA3B9B0 = Multi::NestingContextPool's vtable
    0x32913  mov ecx, 0x10               ; THE OBJECT IS 0x10 BYTES
    0x32AE9  lea rsi, [rip + 0xa08e00]   ; 0x32AF0 + 0xA08E00 = 0xA3B8F0 = Multi::NoFitMapCanceller's vtable
    0x32AD7  mov ecx, 0x10               ; ALSO 0x10 BYTES
    0x32AFC  mov qword [rax], rsi        ; +0x00 = that vtable
    0x32AFF  mov qword [rax + 8], rdx    ; +0x08 = a pointer, and rdx came from `mov rdx, [rbx + 8]` at 0x32AE5

**SO EACH IS `{vptr, owner}`, ALLOCATED ON ITS OWN AND REACHED THROUGH THE STATE OBJECT** -- and `[rbx + 8]` at 0x32AE5 is the Supervisor itself, because the
constructor stored it there at 0x32AD2. **The pointer at +0x08 is therefore the object's OWNER, and that is what makes these cancellers: they need the object
whose work they can cancel.**

**AND LAST ROUND'S PLACEMENT WAS WRONG, WHICH IS WHY THIS CORRECTS IT.** I wrote that `Multi::NoFitMapCanceller` is installed at `[rbx + 0x478]` and
`Multi::NestingContextPool` at `[rbx + 0x4C8]`. **Neither is right**: `+0x478` is an 0x18 byte sub-object built by 0x523FE0's neighbour and `+0x4C8` is a
`std::shared_ptr` whose 0x18 byte control block has `_M_use_count = 1`, `_M_weak_count = 1` and `_M_ptr = r14`, installed from 0xA560C0. **The two cancellers are
separate 0x10 byte allocations**, and the error came from reading vtable installs without asking WHICH base register they were written through.
"""
import io
import sys

TARGET = r"D:\Nesting\nestfab\lcns\include\lcns\engine.hpp"

BLOCK = '''/** RE 0xA3B9A0, THREE SLOTS: 0x69A500 and 0x69A480 the destructor pair, and 0x7D2E20 the one method. **The object is 0x10 bytes**, from
 *  `mov ecx, 0x10` at 0x32913 in the Supervisor's constructor, which is where this class is allocated.
 *
 *      0x3290C  lea rax, [rip + 0xa0909d]   ; 0x32913 + 0xA0909D = 0xA3B9B0 = this class's vtable
 *      and the pointer at +0x08 is the object that owns the pool, stored by the same constructor.
 *
 *  **ITS METHOD ALLOCATES 8 BYTES OF ITS OWN**: slot 2 at 0x7D2E20 begins `mov ecx, 8` at 0x7D2E29 then `call 0x998500`, and reads `mov rdx, qword [rbx + 0x40]`
 *  at 0x7D2E33 before passing both to 0x45490 -- which itself allocates 0x1c8 bytes at 0x4549D. **So a pool object owns a chain of allocations, and NONE of their
 *  fields is established yet**: the method's body is 176 bytes and has been read only far enough to say what it allocates. */
class NestingContextPool {
public:
    virtual ~NestingContextPool() = default;

    /** Slot 2, RE 0x7D2E20, 176 bytes. **Not named, because the module gives no string for it and its body has only been read as far as its first
     *  allocation.** What is established is that it allocates 8 bytes, reads the owner's +0x40 and calls 0x45490. */
    virtual void acquireContext();               // NOT REVERSED: named for what it does, not for a module name

    // +0x00  RE 0x3290C: this class's vtable
    /** +0x08, RE 0x32AFF's counterpart for the other class and 0x32AFC here: **the OWNER**, the object whose work can be cancelled. */
    void* owner_ = nullptr;                      // +0x08
};

/** RE 0xA3B8E0, THREE SLOTS: 0x69A410 and 0x69A400 the destructor pair, and 0x7D29F0 the one method. **Also 0x10 bytes**, from `mov ecx, 0x10` at 0x32AD7.
 *
 *      0x32AE9  lea rsi, [rip + 0xa08e00]   ; 0x32AF0 + 0xA08E00 = 0xA3B8F0 = this class's vtable
 *      0x32AFC  mov qword [rax], rsi        ; +0x00 = the vptr
 *      0x32AE5  mov rdx, qword [rbx + 8]    ; and rbx + 8 is the Supervisor, stored at 0x32AD2
 *      0x32AFF  mov qword [rax + 8], rdx    ; +0x08 = THE OWNER
 *
 *  **SO `{vptr, owner}` IS THE WHOLE OBJECT, AND THE NAME SAYS WHAT IT IS FOR**: a canceller that stops work when the map of parts that fit runs out, holding the
 *  object it cancels. **And its method's shape agrees**: slot 2 at 0x7D29F0 begins `mov rcx, qword [rcx + 8]` at 0x7D29FE -- **it loads its OWNER first** --
 *  then `test rcx, rcx` and `je`, then reads `[rcx + 8]`. **A body that starts by dereferencing its owner is a body that acts on it.** */
class NoFitMapCanceller {
public:
    virtual ~NoFitMapCanceller() = default;

    /** Slot 2, RE 0x7D29F0, 698 bytes. **Not named**: the module has no string for it, and what has been read is that it dereferences `owner_` and then two
     *  levels into it. Naming it "cancel" would be a plausible name and not an oracle. */
    virtual void onNoFit();                      // NOT REVERSED: the body's first act is to dereference the owner

    // +0x00  RE 0x32AFC: this class's vtable
    /** +0x08, RE 0x32AFF: `mov qword [rax + 8], rdx`, where rdx came from `mov rdx, qword [rbx + 8]` at 0x32AE5 -- **the Supervisor itself**. */
    void* owner_ = nullptr;                      // +0x08
};

'''

MARKER = "// RE Multi::Supervisor (vtable 0xA3B4D0), Run at 0x827F0"


def main():
    text = io.open(TARGET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "class NoFitMapCanceller" in text:
        print("the two classes are already declared")
        return 0
    if MARKER not in text:
        print("REFUSING: the Supervisor anchor is not found")
        return 2
    text = text.replace(MARKER, BLOCK + MARKER, 1)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("engine.hpp: declared NestingContextPool and NoFitMapCanceller, both 0x10 bytes with their owner at +0x08")
    return 0


if __name__ == "__main__":
    sys.exit(main())
