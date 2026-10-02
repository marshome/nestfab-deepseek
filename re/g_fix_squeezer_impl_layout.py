# -*- coding: utf-8 -*-
"""Rewrite Row::Squeezer's Impl and insert() from the instructions that read the trees.

RE 0x13A360, 221 BYTES, AND IT IS THE INSERT:

    0x13A368  mov rdi, [rcx + 8]        ; **THE Impl** -- so the class's +8 is confirmed a second time
    0x13A36C  mov rax, [rdi + 0x250]    ; a tree's ROOT at impl + 0x250
    0x13A379  lea r8, [rdi + 0x248]     ; and a HEAD at impl + 0x248, the sentinel a tree walk starts from
    0x13A390  mov rdx, [rax + 0x20]     ; A NODE: its lower key at +0x20
    0x13A399  cmp rsi, [rax + 0x28]     ; and its upper key at +0x28
    0x13A3A4  mov rax, [rax + 0x18]     ; the child link at +0x18
    0x13A3CC  call 0x1380D0             ; on a MISS, a routine that computes the value
    0x13A3EB  lea rdx, [rdi + 0x240]    ; **THE TREE THE INSERT GOES INTO is at impl + 0x240**

**SO THE Impl HAS TWO TREES**, at +0x240 and +0x248/+0x250, with nodes `{link @0x18, lowerKey @0x20, upperKey @0x28}` -- and two 64 bit keys per
box, which is a bounding box and matches the `lo`/`hi` pair this project's `cost` already takes.

**AND `call 0x1380D0` IS THE `enabled` CHECK**: the constructor's `mov byte [rax + 8], 1` at 0x138A6B writes the flag, and that routine tests
`cmp byte [rdx + 8], 0` as its own comment beside `enabled_` already recorded. So a miss is computed only when the squeezer is enabled.
"""
import io
import sys

ROW = r"D:\Nesting\nestfab\lcns\include\lcns\row.hpp"

OLD = """    struct Impl {
            bool enabled = true;              // inner +0x08, RE 0x138A6B
            double coeff = 0.0;               // inner +0x00, RE 0x138A72 -- the constructor's second argument
            double threshold = 0.0;           // inner +0x10, RE 0x138A79 -- its third
            double twiceMaxExtent = 0.0;      // RE 0x138A8F: addsd xmm7, xmm6, handed to 0x2530D0
        };"""

NEW = """    struct Impl {
        bool enabled = true;              // +0x08, RE 0x138A6B, and 0x1380D0 tests it with `cmp byte [rdx + 8], 0`
        double coeff = 0.0;               // +0x00, RE 0x138A72 -- the constructor's second argument
        double threshold = 0.0;           // +0x10, RE 0x138A79 -- its third
        double twiceMaxExtent = 0.0;      // RE 0x138A8F: addsd xmm7, xmm6, handed to 0x2530D0

        /** THE NODE OF BOTH TREES, RE 0x13A390 through 0x13A3A4: `{link @0x18, lowerKey @0x20, upperKey @0x28}`. **Two 64 bit keys per node**,
         *  which is a bounding box -- and it is the `lo`/`hi` pair `cost` already takes. */
        struct Node {
            Node* link = nullptr;         // +0x18, RE 0x13A3A4: mov rax, [rax + 0x18]
            std::uintptr_t lowerKey = 0;  // +0x20, RE 0x13A390: mov rdx, [rax + 0x20]
            std::uintptr_t upperKey = 0;  // +0x28, RE 0x13A399: cmp rsi, [rax + 0x28]
        };

        /** **TWO TREES, and the two instructions that read their heads are four bytes apart.**
         *  RE 0x13A379: `lea r8, [rdi + 0x248]` is the head a walk starts from, with the root at +0x250 by 0x13A36C.
         *  RE 0x13A3EB: `lea rdx, [rdi + 0x240]` is the tree the insert goes INTO. */
        Node* lookupHead = nullptr;       // +0x248, RE 0x13A379
        Node* lookupRoot = nullptr;       // +0x250, RE 0x13A36C
        Node* cacheTree = nullptr;        // +0x240, RE 0x13A3EB
    };"""


def main():
    text = io.open(ROW, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD not in text:
        print("REFUSING: the Impl block is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(ROW, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote Squeezer's Impl with the two trees and the node layout")
    return 0


if __name__ == "__main__":
    sys.exit(main())
