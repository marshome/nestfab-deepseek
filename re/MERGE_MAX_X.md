# 0x5C8C50: what the box merge's maxX actually is, measured

Written at round 391. The measurement is from round 389's probe (nine points, the ORIGINAL called each time); the probe
source itself was temporary and has been deleted, so this file is the record.

## The sweep

The source box was fixed to one of round 386's failing cases:

    src = { flag 0, minX -0.0, minY 7.0, maxX 1.5, maxY 100.0 }

and the destination was `{ flag 0, minX 5.0, minY 6.0, maxY 50.0 }` with only `dst.maxX` changing:

| dst.maxX in | original maxX out | original minX out |
|---:|---:|---:|
| -100, -0.0, 0, 1.0, 1.5 | **1.5** (= src.maxX) | -0.0 |
| 2.0 | 2.0 | -0.0 |
| 7.0 | 7.0 | -0.0 |
| 100, 1000 | 100, 1000 | -0.0 |

For these inputs the original computes `maxX = max(dst.maxX, src.maxX)` and `minX = min(dst.minX, src.minX)`, which is
exactly what the model of round 380/386 does. **Nine of nine agree.**

## What that means for round 386's 521 failures

Read this way, the result is more useful than "one instruction was misread":

* on **valid** boxes (`minX <= maxX`) the model already agrees with the original;
* round 386's random generator produced **arbitrary four values per box**, so `minX > maxX` occurred often, and the 521
  failures are confined to those **invalid** inputs -- where only an exact reproduction of the instruction order agrees,
  in particular of WHEN `xmm1`, `xmm3` and `xmm2` are captured and reloaded;
* that is why ten hand-written fixtures (all valid boxes) never exposed it and 5,000 random ones did. The lesson is about
  the fixture set, not only about the model: **a differential test is only as good as the inputs it feeds**.

## The ordering detail the next experiment must settle

From the listing (re/EXPORT_BODIES.md holds all 62 instructions):

* `0x5C8C83` reloads `xmm1` from `[rcx+8]` immediately after the store at `0x5C8C79`, so `xmm1` is the destination's
  **just-written** minX;
* `xmm3` is updated only by the `movapd xmm3, xmm0` at `0x5C8CA9`, and `xmm2` only by `movapd xmm2, xmm0` at `0x5C8CC2`;
* the INIT path at `0x5C8D10` falls into the tail at `0x5C8CDB` carrying `xmm1`/`xmm3`/`xmm2` from the fields it just
  wrote, which is a different starting state from the normal path.

## The next experiment, narrowed to one run

Feed an explicitly **invalid** box to both implementations and print both 0x28-byte boxes, for example:

    src = { flag 0, minX 100.0, minY -9.0, maxX -9.0, maxY -1.0 }
    dst = { flag 0, minX 5.0,  minY 6.0, maxX 50.0, maxY 50.0 }

Then correct the one ordering slip that shows up and re-run the randomised comparison until it reports **0 mismatches of
5,000 including invalid boxes**. Only then does the model move into `lcns/src/boxmerge.cpp` and into the forwarding map.

## Why this is worth the care

`0x5C8C50` is the common step behind `GetLength`'s implementer (`0x526160`), `GetHeight`'s (`0x5266A0`) and the container
construction of `0x5CD800` -- three exports whose bodies were read in rounds 371-376 and which cannot be implemented
faithfully until their shared box step is exactly right.
