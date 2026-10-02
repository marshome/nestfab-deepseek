# -*- coding: utf-8 -*-
"""Batch twelve: the vector growth, the node tree and the container release of the LaunchLocalComputation closure.

Round 530. Four functions are left that a reader would otherwise take for engine code, and each one's own instructions say
what it is:

    0x8F9220  loads begin and end at [rcx] and [rcx+8], takes the distance, divides by 8 -- a vector of pointers -- tests
              it against 0x1FFFFFFFFFFFFFFF, doubles it, and checks the multiply for overflow before allocating, with the
              nought case allocating 8 bytes. That is libstdc++'s _M_realloc_insert growth; the overflow constant and the
              eight byte minimum are its own. 1462 bytes because the whole insertion is inlined into it.
    0x929FA0  recurses on [node + 0x18] six times over, then frees a contiguous array of 0x30 byte slots one member at a
              time and the member at +0x28, and finally frees the node. 24 callers, among them itself and 0x92B940, and
              its caller inside the closure is a container release: the destructor of the tree's node type.
    0x9308C0  the release of the 0x48 byte nodes 0x22A20 builds: a back pointer at +0x10, a forward pointer at +0x18, an
              inline string at +0x20 with its length at +0x28. It recurses on the forward pointer, frees the string only
              when it does not point at the node's own +0x30, then frees the node, and walks the list at +0x10 the same
              way. 16 callers.
    0x9302C0  the same node, copied: 0x48 bytes allocated, the string moved into the new node's inline buffer at +0x30,
              the type dword at +0, the argument at +8, the forward chain recursed. 0x22A20 calls it once for the object's
              +0x20 member and once per node in the list it walks.

The list 0x9302C0 and 0x9308C0 maintain is intrusive and has a bookkeeping variable in a register rather than a field, which
is why neither is a plain destructor. Both are called from 0x2AB0, 0x5007C0, 0x870070 and 0x8F9220, so what a node MEANS
becomes determinable once 0x5007C0 and 0x870070 are read; until then they are recorded as read, with the layout, and not
implemented.

Two more entries join them for the same reason: 0x1B070 is the string constructor that 0x22A20, 0x1B170, 0x9302C0 and the
orchestration all use to build a string from a buffer and a length, and 0x895F80 is the eight byte accessor the constructor
zeroes at +0xE8.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")

LIBRARY = [
    (0x1B070, "constructs a string from a buffer and a length through the strlen stub: the string constructor every layer here uses"),
    (0x895F80, "eight bytes, loaded and zeroed by the constructor: the string or pointer accessor of that family"),
    (0x8F9220, "takes the distance between [rcx] and [rcx+8], divides by 8, tests against 0x1FFFFFFFFFFFFFFF, doubles and allocates with an 8 byte minimum: the vector of pointers growth"),
    (0x929FA0, "recurses six levels into [node+0x18], frees a contiguous array of 0x30 byte slots and the member at +0x28, then the node: the destructor of the tree's node type"),
    (0x9308C0, "walks the 0x48 byte doubly linked nodes through +0x10 and +0x18, frees the inline string at +0x20 only when it is not the node's own +0x30, and frees each node: the node tree release"),
    (0x9302C0, "allocates 0x48 byte nodes, moves the string at +0x20 into the new node's inline buffer at +0x30, copies the type dword at +0, and recurses the forward chain: the node tree copy"),
]


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    s = read(TOOLCHAIN)
    a = "    0x63F170,  # word by word scan of a string, the strcmp family"
    assert a in s, "the g_toolchain anchor line is gone"
    added = []
    for rva, why in LIBRARY:
        if "0x%X," % rva in s:
            print("    0x%X is already classified, skipped" % rva)
            continue
        added.append((rva, why))
    lines = [a] + ["    0x%X,  # %s" % (rva, why) for rva, why in added]
    write(TOOLCHAIN, s.replace(a, "\n".join(lines), 1))
    print("g_toolchain.py  %d functions classified as library" % len(added))
    print("done")


if __name__ == "__main__":
    main()
