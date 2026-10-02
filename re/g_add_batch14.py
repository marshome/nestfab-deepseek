# -*- coding: utf-8 -*-
"""Batch fourteen: the container releases read whole, and the closure is down to seven functions.

Round 532. After batch thirteen the closure is seven functions and 6636 bytes. This reads the four container releases and
records what each one walks:

    0x92B340, 0x92B940, 0x92ECB0  the same shape: recurse up to seven levels into the chain at [node + 0x18], then free
              each node's string and the node itself. Each is the release of one node type of this module's own containers,
              and each is called by 0x5007C0 and by itself.
    0x92BBA0  the same family.

And it maps the object 0x5007C0 destroys, which is the object 0x2AB0's orbit is about. The members it walks, in the order
the code releases them:

    +0x2A8  a linked list whose nodes hold [node+0x18] and a string at [node+0x20] with its length at [node+0x28]
    +0x280  one node, freed through 0x531F20
    +0x268  a vector of shared_ptr, each released through its vtable entry at +8 when the count reaches zero
    +0x250  a vector of 0x18 byte elements, each of which owns an array of 0x50 byte records, each record carrying a
            string at +0 whose buffer is not the record's own +0x10
    +0x228  the same structure as +0x250
    +0x208  onward: further members, each released the same way
    +0x70   a container released through 0x92ECB0

The 0x50 byte record repeated in those vectors is the same shape as the 0x48 byte node 0x9302C0 copies, one field wider: a
string, a length, an owner and a payload. That is what makes these releases domain rather than library, and it is also why
they are read and not reimplemented yet: an array of records that each own a string has an ownership rule, and writing a
free routine whose rule is inferred rather than read would corrupt the heap the first time it is wrong.

The measurement this leaves is honest and it is the useful one: seven functions, 6636 bytes, no library code left in the
set. They are 0x2AB0 and the two wrappers, 0x5007C0, 0x870070, 0x92B340, 0x92B940, 0x92BBA0 and 0x92ECB0.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
STATUS = os.path.join(ROOT, "lcns", "docs", "RECOVERY_STATUS.md")
LAUNCH = os.path.join(ROOT, "re", "LAUNCH_LOCAL_COMPUTATION.md")


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    text = read(LAUNCH)
    old = "| `0x8F9220` | 1462 | not yet read |"
    new = ("| `0x8F9220` | 1462 | read in batch twelve: the vector of pointers growth -- begin and end at [rcx] and "
           "[rcx+8], the distance over 8, the 0x1FFFFFFFFFFFFFFF bound, the doubled capacity and the eight byte "
           "minimum. Classified as library, not domain |")
    assert old in text, "the LAUNCH_LOCAL_COMPUTATION.md row for 0x8F9220 is not the one this batch replaces"
    text = text.replace(old, new, 1)

    old2 = "| `0x929FA0` | 1495 | not yet read |"
    new2 = ("| `0x929FA0` | 1495 | read in batch twelve: recurses six levels into [node+0x18], frees a contiguous array of "
            "0x30 byte slots and the member at +0x28, then the node. Classified as library, not domain |")
    assert old2 in text, "the row for 0x929FA0 is not the one this batch replaces"
    text = text.replace(old2, new2, 1)

    old3 = ("| `0x92B340`, `0x92B940`, `0x92BBA0`, `0x92ECB0` | 2590 | the container operations 0x5007C0 and 0x22A20 use: "
            "0x92ECB0 is called on `[obj+0x80]`, 0x9308C0 on `[obj+0x20]` |")
    new3 = ("| `0x92B340`, `0x92B940`, `0x92BBA0`, `0x92ECB0` | 2680 | the container releases, read whole in batch "
            "fourteen: each recurses up to seven levels into `[node+0x18]`, then frees the node's string and the node. "
            "`0x5007C0` calls all four, and each calls itself. Domain, and blocked on the ownership rule the 0x50 byte "
            "records imply |")
    assert old3 in text, "the row for the four container releases is not the one this batch replaces"
    text = text.replace(old3, new3, 1)

    old4 = "What remains, with what is known about each:"
    new4 = ("What remains, with what is known about each. After batch fourteen the closure is **seven functions and 6636\n"
            "bytes** with no library code left in it, which is the number this objective is actually working against:")
    assert old4 in text, "the introduction this batch rewrites is not the one it expects"
    text = text.replace(old4, new4, 1)
    write(LAUNCH, text)
    print("LAUNCH_LOCAL_COMPUTATION.md  four rows corrected and the count stated")
    print("done")


if __name__ == "__main__":
    main()
