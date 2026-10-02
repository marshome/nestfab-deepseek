# -*- coding: utf-8 -*-
"""Add the cached box that 0x4F9200 returns, which round 479 pinned to offset 0x108.

The opening of 0x4F9200 is nine instructions and unambiguous:

    4F920B  cmp byte ptr [rcx + 0x100], 0    ; is it already built?
    4F9215  je 0x4F9230                      ; no: go and build it
    4F9217  lea rax, [rbx + 0x108]           ; yes: return the address of the box itself
    4F9229  ret

So the argument carries an initialisation byte at +0x100 and a box starting at +0x108, and the function returns the address
of that box rather than a copy. This is the same object that lcns/dll_layout.hpp already models as UnknownFlagCarrier with
a value100 field at +0x100 -- round 479 checked that too -- and it is the value handed to 0x5CD800 as the second argument
by 0x526160, so it is one half of every span those implementers compute.

What is NOT yet modelled, and is why the two export ordinals are still not forwarded: inside the loop of 0x526160 the
registers change roles in a way that has to be read rather than assumed. rsi is set to rsp+0xA0 (the window) at 0x526189,
but the merge call at 0x5261E9 takes rcx = rbp (the box at rsp+0x70) and rdx = rsi, and the clean-up call at 0x5261DE takes
rcx = rsi with rdx = the element. Which of those two objects rsi actually holds at each point decides what is being merged,
and forwarding the exports before that is settled would be a guess.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
LAYOUT = os.path.join(ROOT, "lcns", "include", "lcns", "dll_layout.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_exports.cpp")

CARRIER = '''/**
 * The cached box that 0x4F9200 returns. RE 0x4F920B tests the byte at +0x100 and RE 0x4F9217 returns rcx+0x108, so the
 * object carries an initialisation byte and then a box. The box bytes follow the same layout as this project's box model:
 * flag, minX, minY, maxX, maxY, each eight bytes apart after the flag.
 */
struct CachedBoxCarrier {
    unsigned char opaque00[0x100];
    unsigned char initialised;   // +0x100, RE 0x4F920B (the same field UnknownFlagCarrier calls value100)
    unsigned char opaque01[0x07];
    unsigned char box[0x28];     // +0x108, RE 0x4F9217: flag, minX, minY, maxX, maxY
};
static_assert(offsetof(CachedBoxCarrier, initialised) == 0x100, "RE 0x4F920B");
static_assert(offsetof(CachedBoxCarrier, box) == 0x108, "RE 0x4F9217");

'''

TESTS = '''        CHECK(offsetof(lcns::dll::CachedBoxCarrier, initialised) == 0x100);   // RE 0x4F920B
        CHECK(offsetof(lcns::dll::CachedBoxCarrier, box) == 0x108);           // RE 0x4F9217

    return check::finish("exports");'''


def main():
    t = io.open(LAYOUT, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    anchor = "}  // namespace dll"
    assert anchor in t, "the dll namespace close is not in dll_layout.hpp"
    t = t.replace(anchor, CARRIER + anchor, 1)
    io.open(LAYOUT, "w", encoding="utf-8", newline="\n").write(t)
    print("dll_layout.hpp   CachedBoxCarrier added with two offset assertions")

    s = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    finish = '    return check::finish("exports");'
    assert finish in s, "the exports finish anchor is missing"
    s = s.replace(finish, TESTS, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(s)
    print("test_exports.cpp two checks added, so the new class is named by a test as check_recovery requires")

    print("")
    print("done. The exports wait for the loop register roles to be read")


if __name__ == "__main__":
    main()
