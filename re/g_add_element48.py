# -*- coding: utf-8 -*-
"""Add the third element family to the object model, and document the GetLength dependency chain.

Round 447 read 0x8C4530 and found it counting a container with the modular inverse of three: the difference is shifted
by four and multiplied by 0xAAAAAAAAAAAAAAAB, so the element it counts is 16 * 3 = 48 bytes. That is the third such
constant the module uses, after 39 (312 bytes) and 15 (120 bytes), and like them it belongs in the model as a derivation
rather than as a literal.

Rounds 448 and 449 tried to land this from a one line command twice and failed on quoting both times. It is a script file
now, which is the rule this session keeps proving: code goes in a file, not in a command.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"


def patch(path, old, new, what):
    t = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    assert old in t, "anchor missing in %s: %s" % (path, what)
    io.open(path, "w", encoding="utf-8", newline="\n").write(t.replace(old, new, 1))
    print("patched %-24s (%s)" % (os.path.basename(path), what))


# 1. the model entry
patch(os.path.join(ROOT, "lcns", "include", "lcns", "dll_layout.hpp"),
      "}  // namespace dll",
      '''/**
 * A third element family. 0x8C4530 counts a container of these: it shifts the difference by four and multiplies by
 * 0xAAAAAAAAAAAAAAAB, which is inv(3) mod 2**64, so the element is 16 * 3 = 48 bytes. With this the module's three
 * counting constants are 39, 15 and 3, each derived from an element size rather than written down.
 */
struct Element48 {
    unsigned char opaque[48];
};
static_assert(sizeof(Element48) == 48, "RE 0x8C4530");
static_assert(modularInverse(3) == 0xAAAAAAAAAAAAAAABull, "the constant 0x8C4530 multiplies by");

}  // namespace dll''', "Element48 and inv(3)")

# 2. the chain documentation
patch(os.path.join(ROOT, "re", "EXPORT_BODIES.md"),
      "## The 0x52F8xx family (round 375)",
      '''## The dependency chain behind GetLength, layer by layer (rounds 441 to 447)

0x524EE0 (1051 bytes, 241 instructions) turns one container element into a pair of values. Its dependencies, read from
the top down:

| address | bytes | what it is |
|---|---:|---|
| 0x5F4310 | 35 | stores a pointer at +0, hands +8 to 0x5F3900, stores a byte at +0x10 |
| 0x5F3900 | 22 | stores whatever 0x5F47C0 returns at +0 |
| 0x5F47C0 | 112 | allocates 16 bytes through operator new, stores a constant at +0, makes two IAT calls, then stores the QUOTIENT of their two results as a double at +8. A ratio singleton, and platform-flavoured for that reason |
| 0x5C6BE0 | 65 | clears a 24-byte object, then constructs through 0x8C4530, with 0x8C5090 and the platform stub on the exception path |
| 0x8C4530 | 1209 | the size idiom: (end - begin) shifted by four, multiplied by inv(3), so the element is 48 bytes |
| 0x8C5090 | 147 | the matching destructor, 133 callers, walking the same container |
| 0x5203C0 | 4 | mov eax, dword ptr [rcx + 0x20] -- differentially tested against the original in round 445 |
| 0x547620 | 5 | lea rax, [rcx + 0x18] -- differentially tested against the original in round 445 |

Still to read before this chain is finished: 0x520440 (479 bytes, 55 callers), 0x4F73E0 (530 bytes, 12 callers) and
0x524EE0 itself. The two accessors at the bottom are already held to the original bit for bit, which is what makes this
chain worth walking one layer at a time rather than in one go.

## The 0x52F8xx family (round 375)''', "chain table")

print("")
print("done: Element48 is in the model and the chain is documented")
