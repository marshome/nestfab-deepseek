# -*- coding: utf-8 -*-
"""Add the window carrier that GetLength and GetHeight read, and the assertion that names it.

Rounds 463 to 466 read both implementers whole and settled the arithmetic: each returns one of two differences of window
fields, chosen by a status test, and zero for an empty container. What is NOT yet established is where that status test
gets its operand. In 0x526160 the sequence is

    526206  call 0x4F9200
    52620B  rcx = rsi ; rdx = rax ; call 0x5CD800
    526216  lea rcx, [rsp + 0x108]
    52621E  call 0x52F810          ; cmp dword ptr [rcx], 1 ; setbe al

so the status is the first dword of an object at rsp+0x108, which is rsi+0x98 if rsi is rsp+0x70. Which of the two calls
fills that dword has not been read yet, and implementing the two exports with a guessed offset would raise forwardedCount
on a guess, which the sixth criterion forbids outright.

So this script lands only what is certain: the eight window fields the two implementers actually subtract, with a
static_assert for each offset and each one citing the instruction that reads it. The exports themselves wait for one more
read.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
LAYOUT = os.path.join(ROOT, "lcns", "include", "lcns", "dll_layout.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_exports.cpp")


def patch(path, old, new, what):
    t = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    assert old in t, "anchor missing in %s: %s" % (path, what)
    io.open(path, "w", encoding="utf-8", newline="\n").write(t.replace(old, new, 1))
    print("patched %-24s (%s)" % (os.path.basename(path), what))


patch(LAYOUT, "}  // namespace dll",
      '''/**
 * The window object that GetLength and GetHeight read.
 *
 * Both implementers build it through 0x4F9200 and 0x5CD800, then subtract one of four pairs of these fields. The pairs are
 * 0x10 apart inside a pair and the four pairs sit at 0x08, 0x10, 0x18, 0x20 on the low side and 0x38, 0x40, 0x48, 0x50 on
 * the high side, so the window holds two dimension records. Each assertion below names the instruction that produces the
 * read it pins.
 */
struct WindowSlots {
    unsigned char opaque00[0x08];
    double slot08;   // 0x526230 and 0x526770 (status false in both implementers)
    double slot10;   // 0x526770 minus, the low side of the second record
    double slot18;   // 0x526227 (0x526160, status true) and rsi+0x18 of the first record
    double slot20;   // 0x526767 (0x5266A0, status true) and rsi+0x20
    unsigned char opaque28[0x10];
    double slot38;   // 0x52624D (0x526160, status true)
    double slot40;   // 0x526767 (0x5266A0, status true)
    double slot48;   // 0x526227 (0x526160, status false)
    double slot50;   // 0x526767 (0x5266A0, status false)
};
static_assert(offsetof(WindowSlots, slot08) == 0x08, "RE 0x526230");
static_assert(offsetof(WindowSlots, slot10) == 0x10, "RE 0x526770");
static_assert(offsetof(WindowSlots, slot18) == 0x18, "RE 0x526227");
static_assert(offsetof(WindowSlots, slot20) == 0x20, "RE 0x526767");
static_assert(offsetof(WindowSlots, slot38) == 0x38, "RE 0x52624D");
static_assert(offsetof(WindowSlots, slot40) == 0x40, "RE 0x526767");
static_assert(offsetof(WindowSlots, slot48) == 0x48, "RE 0x526227");
static_assert(offsetof(WindowSlots, slot50) == 0x50, "RE 0x526767");

/** Where the status test in the two implementers reads its operand, as read from the code but NOT yet traced to a writer. */
constexpr std::size_t kWindowStatusOffset = 0x98;   // rsp+0x108 with rsi = rsp+0x70; the writer is still to be read

}  // namespace dll''', "WindowSlots")

patch(TEST, '    return check::finish("exports");',
      '''        CHECK(offsetof(lcns::dll::WindowSlots, slot08) == 0x08);   // the four pairs GetLength and GetHeight subtract
        CHECK(offsetof(lcns::dll::WindowSlots, slot10) == 0x10);
        CHECK(offsetof(lcns::dll::WindowSlots, slot18) == 0x18);
        CHECK(offsetof(lcns::dll::WindowSlots, slot20) == 0x20);
        CHECK(offsetof(lcns::dll::WindowSlots, slot38) == 0x38);
        CHECK(offsetof(lcns::dll::WindowSlots, slot40) == 0x40);
        CHECK(offsetof(lcns::dll::WindowSlots, slot48) == 0x48);
        CHECK(offsetof(lcns::dll::WindowSlots, slot50) == 0x50);
        CHECK(lcns::dll::kWindowStatusOffset == 0x98);             // read from the code, writer not yet traced

    return check::finish("exports");''', "window assertions")

print("")
print("the window carrier is in the model and named by the test; the two exports wait for one more read")
