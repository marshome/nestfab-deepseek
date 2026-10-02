# -*- coding: utf-8 -*-
"""Implement Squeezer::insert from RE 0x13A360, which is the routine that reads the two trees.

RE 0x13A360, 221 bytes:

    0x13A368  mov rdi, [rcx + 8]        ; THE Impl
    0x13A36C  mov rax, [rdi + 0x250]    ; the lookup tree's ROOT
    0x13A376  mov rbx, rdx              ; the first key
    0x13A373  mov rsi, r8               ; the second key -- so the signature is (this, key1, key2, ...)
    0x13A379  lea r8, [rdi + 0x248]     ; the head the walk starts from
    0x13A390  mov rdx, [rax + 0x20]     ; the node's lower key
    0x13A394  cmp rbx, rdx / ja ...     ; THE WALK: lower first, then upper
    0x13A399  cmp rsi, [rax + 0x28]
    0x13A3A4  mov rax, [rax + 0x18]     ; and the child link
    0x13A3CC  call 0x1380D0             ; A MISS: compute, and 0x1380D0 is the routine whose first act tests `[rdx + 8]`, the enabled flag
    0x13A3EB  lea rdx, [rdi + 0x240]    ; THE TREE THE INSERT GOES INTO
"""
import io
import sys

SRC = r"D:\Nesting\nestfab\lcns\src\row.cpp"
ROW = r"D:\Nesting\nestfab\lcns\include\lcns\row.hpp"

BODY = '''// RE 0x13A360, 221 bytes. **IT WALKS THE LOOKUP TREE AT impl + 0x250 BEFORE IT INSERTS INTO THE ONE AT impl + 0x240**, and the two are four
// bytes apart in the object -- which is why the head at +0x248 and the root at +0x250 are separate fields in `Impl`.
//
//     0x13A36C  mov rax, [rdi + 0x250]     ; the root of the tree to SEARCH
//     0x13A390  mov rdx, [rax + 0x20]      ; a node's lower key
//     0x13A399  cmp rsi, [rax + 0x28]      ; and its upper key
//     0x13A3A4  mov rax, [rax + 0x18]      ; the child link
//     0x13A3CC  call 0x1380D0              ; ON A MISS: compute, and 0x1380D0's first act is `cmp byte [rdx + 8], 0` -- the enabled flag
//     0x13A3EB  lea rdx, [rdi + 0x240]     ; the tree the insert goes INTO
void Squeezer::insert(std::uintptr_t lo, std::uintptr_t hi, double value) {
    // **THE MODEL'S STORE, AND IT SAYS SO.** The module's two trees are `Impl::Node` chains keyed by the pair (lo, hi); the port keeps the
    // vector `cost` already searches, because a tree whose node type is established but whose comparator is not would be a guess in C++ where
    // the module's is in assembly. The keys and the ORDER are the module's: 0x13A394 compares the first key BEFORE 0x13A399 compares the
    // second, so the search is by lower key first.
    for (Entry& e : cache_) {
        if (e.keyLo == lo && e.keyHi == hi) {
            e.value = value;                  // the module updates the node it found rather than inserting a second
            return;
        }
    }
    Entry e;
    e.keyLo = lo;
    e.keyHi = hi;
    e.value = value;
    cache_.push_back(e);
}

'''


def main():
    text = io.open(SRC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "Squeezer::insert" in text:
        print("insert is already implemented")
        return 0
    marker = "void Squeezer::clear() {"
    if marker not in text:
        print("REFUSING: the insertion point is not found")
        return 2
    text = text.replace(marker, BODY + marker, 1)
    io.open(SRC, "w", encoding="utf-8", newline="\n").write(text)
    print("added Squeezer::insert")
    return 0


if __name__ == "__main__":
    sys.exit(main())
