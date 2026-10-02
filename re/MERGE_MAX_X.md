# 0x5C8C50: the box merge, and how its one ordering slip was found

CORRECTED at round 395. An earlier version of this file concluded that the model's disagreements with the original were
confined to *invalid* boxes (minX > maxX). **That was wrong**, and this file now records what is true.

## The root cause

The original's INIT path -- taken when the destination's flag byte is non-zero, meaning "not yet initialised" -- writes
the source's min corner into all four fields and then **jumps to `0x5C8CDB`**. That address is the **maxX check inside the
second pass**, and it runs **before** the tail at `0x5C8CE7`. The model did only the minX half on that path and fell
straight through to the tail, so **the maxX store never happened on the INIT path**.

The fix is three lines in the INIT branch:

    if (x0 > loadD(dst, lcns::kBoxMaxX)) { storeD(dst, lcns::kBoxMaxX, x0); }

## What made it findable

Every mismatching fixture had a **destination flag of 1** -- the INIT path -- which is visible only when the failing
case's inputs are printed. Two earlier rounds of inference had failed:

1. round 380, ten hand-written fixtures (all valid boxes, all with flag 0): nine agreed, one did not, and nothing in the
   output said which path it was;
2. round 386, 5,000 random boxes: 521 disagreed, and the printed values localised the fault to maxX but not to a path;
3. round 389, a nine-point sweep of dst.maxX with a flag-0 destination: **all nine agreed**, which I misread as "the
   failures must be invalid boxes" -- they were not;
4. round 393, printing the **first failing case's full input** (src, dst-in, and both outputs) ended it immediately: both
   mismatching cases had `dst-in flag=1`.

**The lesson, which cost two rounds: print the failing case's complete input before theorising about why it fails.**

## The measurement that is still valid

With the source fixed to a flag-0 box and only dst.maxX swept, the original computes
`maxX = max(dst.maxX, src.maxX)` and `minX = min(dst.minX, src.minX)`, and the model already agreed on all nine points:

| dst.maxX in | original maxX out |
|---:|---:|
| -100, -0.0, 0, 1.0, 1.5 | 1.5 (= src.maxX) |
| 2.0 / 7.0 / 100 / 1000 | 2.0 / 7.0 / 100 / 1000 |

That is a statement about the normal path, and it remains true; it simply was not evidence about the INIT path, which is
where the failures lived.

## Evidence

`re/_probe_invalid.cpp` holds the corrected model and the comparison that settled it: three hand-made cases (invalid
source, invalid destination, uninitialised destination) plus **5,000 random boxes with invalid ones allowed**, and it
reports **0 mismatches**. Build and run it from `lcns/`:

    g++ -std=c++17 -I include -DLCNS_HAS_EMBEDDED_ASM=1 ..\re\_probe_invalid.cpp \
        build\liblcns_geom.a build\liblcns_embedded.a -o probe_invalid.exe
    .\probe_invalid.exe

## What remains

The verified model is not yet in `lcns/src/`: landing it (plus the randomised comparison in `tests/test_boxacc.cpp`) is
mechanical and is the next step. `0x5C8C50` is the common step behind `GetLength`'s implementer (`0x526160`),
`GetHeight`'s (`0x5266A0`) and the container construction of `0x5CD800`, so getting it exactly right is what unblocks
those three exports.
