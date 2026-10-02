# -*- coding: utf-8 -*-
"""Rewrite Row::Squeezer's declaration so its members belong to the object the instructions put them in.

WHAT THE CONSTRUCTOR ESTABLISHES, read at 0x138A20 (446 bytes):

    0x138A3E  mov rbp, rcx                ; the Squeezer object
    0x138A3B  mov [rcx], rax              ; its vtable, 0xA3B1F0 -- the pointer, which is Squeezer's slot-0 address
    0x138A41  mov ecx, 0x270 / call 0x998500   ; AN INNER OBJECT of 0x270 bytes
    0x138A6B  mov byte [rax + 8], 1       ; its enabled flag
    0x138A72  movsd [rax], xmm2           ; its coefficient
    0x138A79  movsd [rax + 0x10], xmm3    ; its threshold
    0x138B5C  mov [rbp + 8], rbx          ; AND THE INNER OBJECT IS STORED AT Squeezer + 8

**SO Squeezer IS `{vptr @0, inner* @8}` AND THE FOUR FIELDS BELONG TO THE INNER OBJECT.** The declaration carried them as Squeezer's own
members, with comments that said `inner +0x08` and `inner +0x00` beside them -- **the comment and the declaration contradicted each other, and
the comment was right.** That is why the support audit reported the class as unsupported: nothing writes `+0x08`, `+0x10` or `+0x18` of the
Squeezer object, because they are at those offsets of the object at `+8`.

THE FIELDS ARE KEPT, because they are real and their offsets are established -- **they are just inside the inner object**, which is now a type of
its own.
"""
import io
import re
import sys

ROW = r"D:\Nesting\nestfab\lcns\include\lcns\row.hpp"

OLD_START = "class Squeezer {"
OLD_END = "\n};\n"


def main():
    text = io.open(ROW, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find(OLD_START)
    if start < 0:
        print("REFUSING: the class is not found")
        return 2
    end = text.find(OLD_END, start)
    if end < 0:
        print("REFUSING: the closing brace is not found")
        return 2
    # keep the doc comment that precedes the class, since it already records the constructor correctly
    comment = text.rfind("    // RE: 0x138A20", 0, start)
    if comment < 0:
        comment = text.rfind("// RE: 0x138A20", 0, start)
    if comment > 0:
        start = comment

    new = '''    /** The 0x270 byte object RE 0x138A20 allocates and stores at Squeezer + 8.
     *
     *      0x138A6B  mov byte [rax + 8], 1        ; enabled
     *      0x138A72  movsd [rax], xmm2           ; the coefficient, the constructor's second argument
     *      0x138A79  movsd [rax + 0x10], xmm3    ; the threshold, its third
     *      0x138A8F  addsd xmm7, xmm6            ; TWICE the first argument
     *      0x138A9A  call 0x2530D0               ; and 0x2530D0 is given (twiceMaxExtent, coefficient)
     *      0x138A7E  call 0x500710               ; the sub-object at +0x20
     *      0x138AAD  mov byte [rsp + 0x50], 0x73 ; the one character string "s"
     *      0x138ADA  mov [rbx + 0x258], rax      ; and two tree headers at +0x210 and +0x240
     *
     *  **THE SCALARS LIVE HERE AND NOT IN Squeezer**, which is why the class was reported as having unsupported members: nothing writes +0x08,
     *  +0x10 or +0x18 of the Squeezer object itself.
     */
    struct Impl {
        bool enabled = true;              // inner +0x08, RE 0x138A6B
        double coeff = 0.0;               // inner +0x00, RE 0x138A72 -- the constructor's second argument
        double threshold = 0.0;           // inner +0x10, RE 0x138A79 -- its third
        double twiceMaxExtent = 0.0;      // RE 0x138A8F: addsd xmm7, xmm6, handed to 0x2530D0
    };

    /** RE 0xA3B1F0, three slots. **ITS OWN STATE IS ONE POINTER.** The constructor installs the vtable at +0, allocates the 0x270 byte Impl and
     *  stores it at +8, and touches nothing else of this object -- so `Impl` is where the fields are, and this class is the handle.
     *
     *  The cost path below the constructor reads the SCALARS through that pointer, which is why `enabled`, `threshold`, `coeff` and
     *  `twiceMaxExtent` are accessors here rather than members. */
    class Squeezer {
    public:
        Squeezer() = default;
        Squeezer(double twiceMaxExtent, double coeffAt0x18, double thresholdAt0x10);

        bool enabled() const { return impl_ != nullptr && impl_->enabled; }
        double threshold() const { return impl_ != nullptr ? impl_->threshold : 0.0; }
        double coeff() const { return impl_ != nullptr ? impl_->coeff : 0.0; }
        double twiceMaxExtent() const { return impl_ != nullptr ? impl_->twiceMaxExtent : 0.0; }

        /** RE 0x13A360, vtable slot 2: the insert into the tree at inner +0x240. */
        void insert(std::uintptr_t keyLo, std::uintptr_t keyHi, double value);
        std::size_t size() const { return cache_.size(); }
        void clear();

        std::size_t hits() const { return hits_; }
        std::size_t misses() const { return misses_; }

    private:
        // RE 0x138B5C: mov [rbp + 8], rbx -- THE ONLY MEMBER OF THIS OBJECT THE CONSTRUCTOR WRITES.
        Impl* impl_ = nullptr;             // +8, and the 0x270 byte object it points at holds the state

        // THE MODEL'S OWN CACHE, NOT THE MODULE'S. The module keeps a tree at inner +0x240; this keeps a vector, and says so, because the
        // tree's routines (0x13A360 and 0x13C380) have not been read.
        struct Entry {
            std::uintptr_t keyLo = 0;
            std::uintptr_t keyHi = 0;
            double value = 0.0;
        };
        std::vector<Entry> cache_;
        std::size_t hits_ = 0;
        std::size_t misses_ = 0;
    };
'''
    text = text[:start] + new + text[end + len(OLD_END):]
    io.open(ROW, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote Row::Squeezer's declaration")
    return 0


if __name__ == "__main__":
    sys.exit(main())
