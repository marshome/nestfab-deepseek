# Review plan — the 60-round checkpoint

Set up in round 355 on the user's instruction: **"1+2"** (implement what has been recovered instead of annotating it;
re-scope the completion criterion to something real) plus **"every 60 rounds stop so I can look"**, plus **"where a
region has not been reversed, put its assembly into the C++ — executable, or at least in a comment"**.

## Why the plan changed

Measured over the 30 rounds before round 355, from `git log --numstat`:

| directory | lines added |
|---|---:|
| `lcns/src` (the implementation) | **0** |
| `lcns/include/lcns/layout.hpp` (constants) | 855 |
| `lcns/tests/test_recovered.cpp` (checks of those constants) | 1,286 |
| `re/` (documents) | 638 |

`lcns/src` had not been touched for 62 commits, while the un-cited domain mass moved from 2,581 to 2,563 functions in
26 rounds — about 0.7 functions per round, against a backlog of 2,563. The method could not reach the old criterion,
which was stated each round and yet not changed. That is what this plan fixes.

## The criterion now (C1–C5)

* **C1** Every category of reachable domain code is accounted for: either implemented in `lcns/src` with behavioural
  tests, or listed in `re/` as not recovered **with its original bytes embedded in `lcns/`** (executable where
  possible, otherwise as data with the disassembly).
* **C2** Zero build warnings; boost 1.63.0, CoinUtils, Osi, Clp, CryptoPP and JsonCpp really linked; `ctest` green.
* **C3** `tools/check_recovery.py` and `re/g_acceptance.py` green. `re/g_coverage.py`'s three numbers are reported
  separately — **implemented**, **annotated only**, **unread** — and the unread number is **not** claimed to be zero.
* **C4** Every embedded block is either called by a differential test and compared bit for bit, or marked
  `comment_only` with the reason it cannot be called.
* **C5** `re/check_embeddings.py` re-reads the DLL and fails on any byte or hash drift.

## What "embedded" means here

`re/g_embed.py` generates, from the DLL:

| artifact | content |
|---|---|
| `lcns/src/embedded/gen_blobs.cpp` | every block's original bytes as an array, plus the metadata table |
| `lcns/src/embedded/gen_orig.S` | an executable copy of each **callable** block, with the disassembly as a comment |
| `lcns/src/embedded/gen_table.cpp` | the addresses, as function pointers |
| `re/EMBEDDED.md` | the registry with a full disassembly listing per block |
| `re/embedded_registry.json` | the machine-readable registry the verifier reads |

A block is **callable** only when the classifier finds no RIP-relative memory operand, no call or jump leaving the
block, and no absolute image address in it — then the bytes are position-independent and an executable copy behaves
exactly as the original. Otherwise it is **comment_only**, the reason is recorded in the code itself, and the bytes are
still embedded as data.

First run: **21 blocks, 18,200 bytes, 11 callable, 10 comment-only.**

An embedded block is **not** "recovered code": it is the original binary, carried as a fallback and as the oracle for
differential tests. Nothing under `src/` outside the tests refers to it.

### The first thing the originals settled

`0x16C270` leaves its two sums **packed in xmm0**. Declaring the call as `struct {double lo, hi;}` returns zeros under
MinGW, because that struct's return convention does not match a raw packed pair. Declaring it `__m128d` returns
`{2.0, 2.75}` for the documented inputs, which is what the C++ model predicts. Recorded in `tests/test_embedded.cpp`,
because a reader would otherwise assume the two declarations are interchangeable.

## What the differential tests already prove (round 355)

Against the original bytes, bit for bit:

* the four small accessors (`0x51D2F0`, `0x4F8370`, `0x4F8380`, `0x4DDD10`);
* the packed point addition `0x16C270`, including which operand supplies which coordinate;
* the orientation determinant `0x24B440` against the C++ formula, four triples;
* the in-place affine transforms `0x5CFD80` (one point) and `0x5CFDC0` (both points of a segment);
* `0x5CF6B0` agreeing with `0x5CFDC0` on the same input while leaving its source untouched;
* `0x5CE970` composing two matrices such that composing-then-applying equals applying in turn.

`ctest` runs it as `embedded`; the count at the time of writing is 275 checks.

## The checkpoint

The user asked for a stop every 60 rounds. `update_goal` would not accept a change to `maxGoalRounds` (it stays 500),
and resuming a paused goal is not something the model may do, so the checkpoint is kept here instead:

> **Checkpoint at round 414** = the 354 rounds already started plus 60. When that round is reached, work stops and this
> document is the agenda.

At the checkpoint I will bring:

1. the three counters (implemented / annotated / unread) with the commands used to measure them, and the change since
   round 354;
2. the list of categories implemented in `lcns/src`, each with the tests that check its behaviour;
3. the embedded registry — blocks, bytes, and for each comment-only block the reason;
4. `git log --numstat` for the 60 rounds, so the same zero-in-`src` question can be asked of the new method;
5. what is still not recovered, by category, with sizes, so the remaining work is visible rather than implied.

## What to inspect (commands that reproduce every claim above)

```powershell
# the change in the implementation, per round
git -C D:\Nesting\nestfab log --numstat --pretty=format:'%h %s' -- lcns/src | Select-Object -First 40

# the embedded originals still match the DLL
python D:\Nesting\nestfab\re\check_embeddings.py

# the differential tests
D:\Nesting\nestfab\lcns\build\test_embedded.exe

# the registry, with the listing of every block
notepad D:\Nesting\nestfab\re\EMBEDDED.md
```
