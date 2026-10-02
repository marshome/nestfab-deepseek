# -*- coding: utf-8 -*-
"""Batch nine: the printf numerics and the stream destructors of the LaunchLocalComputation closure.

Round 527. After batch eight the closure of ordinal 51 stands at 37 functions and 20425 bytes. Two groups are decided here.

The first is the rest of the `0x639xxx`/`0x63Axxx`/`0x63Bxxx` numeric layer. Batch seven classified `0x63A2A0` and `0x63A8E0`
by their bodies -- long division by ten with grouping, called per character through `0x6399E0`, which the toolchain already
holds as "reads the stream state flags" -- and `0x63BF20` by its literals 'NaN', 'Infinity', 'aCoc' and '2ZGU'. What is
left is the same family, and each one's own instructions say so:

    0x63A1C0, 0x63A6A0, 0x63A750  open by loading an 80-bit long double with `fld xword ptr [rcx]` and reading a count from
              [rdx + 0x10], which is the same prologue batch seven read in 0x63A2A0 and 0x63A8E0. They are the double and
              long double overloads of the same `num_put` member.
    0x6398E0  reads the 0x7fff exponent mask of an 80-bit long double, classifies it as zero, infinity, NaN or finite, and
              calls 0x63BF20 -- the classification `num_put` does before it formats.
    0x639B50, 0x639CA0, 0x639C50, 0x639D40  pad, adjust and emit through 0x6399E0, and 0x639C50 stores the '(null)' literal
              for a null string argument. 0x639A40 does the same for a wide character array through 0x630DA0.
    0x639E30  is the largest of them at 910 bytes and reads the same stream fields, so it is the same layer.
    0x63B140  reads the stream state words, dispatches on the format flags and reaches eleven of the above: the `num_put`
              entry point they hang from.
    0x63BD80  shifts 1 left by the word count at [rcx - 4] and stores it next to the word count before jumping to 0x63E530:
              the bignum normalisation batch seven classified at 0x63E530.

The second group is stream destruction, and its evidence is its callers:

    0x9445E0  has 237 callers and four of them are in this closure, among them 0x65A530 -- the routine that opens the three
              log files -- and two destructors of the stream family. Batch eight classified 0x9454D0 as the basic_ios
              initialisation; 0x9445E0 is what undoes it.
    0x87F2A0  is called by 0x2AB0 and by the same destructor chain, and its body is the same shape as 0x9445E0: a vtable
              from the image, a released member string, a shared_ptr handover.

The counting rule from the round 526 section applies to both groups: their work is the standard library's, so they are
classified and recorded, not reimplemented.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")

LIBRARY = [
    (0x63A1C0, "loads an 80-bit long double and reads a count from the second argument, then pads through 0x6399E0: a num_put overload"),
    (0x63A6A0, "the same prologue as 0x63A1C0: another num_put overload"),
    (0x63A750, "the same prologue as 0x63A1C0 at 390 bytes: the long double overload"),
    (0x6398E0, "reads the 0x7fff exponent mask of an 80-bit long double, classifies zero, infinity and NaN, and calls 0x63BF20"),
    (0x639B50, "pads and adjusts through 0x6399E0 using the stream width at +0xc: part of the num_put formatting"),
    (0x639CA0, "the same padding path, storing 0xffffffff as the width"),
    (0x639C50, "stores the '(null)' literal when the string argument is null: the num_put null string path"),
    (0x639D40, "the same family, emitting through 0x6399E0"),
    (0x639A40, "emits a wide character array through 0x630DA0 and 0x6399E0 with the same width padding"),
    (0x639E30, "reads the same stream fields and reaches three of the above: the same num_put layer"),
    (0x63B140, "reads the stream state words, dispatches on the format flags and reaches eleven num_put functions: the num_put entry point"),
    (0x63BD80, "shifts 1 left by the word count at [rcx - 4] and jumps to 0x63E530: the bignum normalisation"),
    (0x9445E0, "installs a vtable from the image, releases the member string at +0xc8 and hands +0xd0 to the shared_ptr release; 237 callers, among them the stream construction: a destructor"),
    (0x87F2A0, "the same destructor shape as 0x9445E0, called from the same construction and from 0x2AB0"),
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
    for rva, reason in LIBRARY:
        if "0x%X," % rva in s:
            print("    0x%X is already classified, skipped" % rva)
            continue
        added.append((rva, reason))
    lines = [a] + ["    0x%X,  # %s" % (rva, reason) for rva, reason in added]
    write(TOOLCHAIN, s.replace(a, "\n".join(lines), 1))
    print("g_toolchain.py  %d functions classified as library" % len(added))
    print("done")


if __name__ == "__main__":
    main()
