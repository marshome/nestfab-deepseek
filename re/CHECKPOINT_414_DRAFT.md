# Round 414 checkpoint -- draft, computed from the tree

Drafted at round 388 from the artifacts themselves (no figure here is typed by hand). HEAD `8e8dc41`.

## The numbers

| Measure | Value | Source |
|---|---:|---|
| Exported entry points implemented (`forwardedCount()`) | **14 of 168** | rows of `lcns/include/lcns/detail/exports_forwarding.inc` (hand-written) |
| Entry points defined in the C ABI layer | 168 of 168 | `extern "C"` definitions in `lcns/src/api_exports.cpp` |
| Embedded blocks | 195 (20 executable, 174 comment-only, 1 data) | `re/embedded_registry.json` |
| Embedded bytes | 92,861, all matching the module | `re/check_embeddings.py` |
| Lines added to `lcns/src` over the last 60 commits | +19717 / -238 | `git log --numstat -60 -- lcns/src` |
| Commits in that window | 60 | `git log --oneline -60` |
| Domain code still to reverse | 2,490 functions / 1,449,418 bytes / 31.0% | `re/g_coverage.py` (round 384) |

## What is implemented and how it is held to the assembly

| Category | Routines | Evidence |
|---|---|---|
| 2x3 affine library | `0x5CE7B0`, `0x5CED50`, `0x5CE970`, `0x5CF6B0`, `0x5CFD80`, `0x5CFDC0` | `tests/test_affine.cpp`, 862 checks, all six compared bit for bit; the inverse comparison found a signed-zero difference property tests cannot see |
| Orientation determinant | `0x24B440` | bit-exact over four operand sets plus sign semantics |
| Segment threshold kernel | `0x55E190` | `tests/test_segcost.cpp`, 3,072 combinations, both outcomes exercised |
| Box accumulator pair | `0x5C8A10`, `0x50FD40` | `tests/test_boxacc.cpp`, the whole 0x28-byte box compared byte for byte |
| Box merge | `0x5C8C50` | differential test written; 521 of 5,000 random boxes disagree, fault localised to `maxX` at `0x5C8C88` |
| Exported entry points | 14 of 168 | `re/EXPORT_IMPLS.md`; the rest fail loudly and their bytes are embedded |

## What the checkpoint still owes

1. The `maxX` reading of `0x5C8C50` corrected, then 0 mismatches of 5,000, then the model moved into `lcns/src/boxmerge.cpp`.
2. The read-only export family behind the queue's first eight entries (`GetFillRatio`, `GetLength`, `GetHeight`, `GetNestingFillRatio`, the version trio), each with a behavioural test.
3. `GetBuildVersion`/`GetBuildDate`/`GetMajorVersion` recorded as deliberately not implemented: they return a pointer held in the module's own global data, which a reimplementation cannot reproduce as an address.

## Gate, as of this draft

Build 0 errors / 0 warnings; ctest 22 of 22 with freshly linked binaries; `check_recovery.py`, `check_embeddings.py`, `g_coverage.py`, `g_acceptance.py` all clean.


## Per-export status at round 402 (generated, not typed)

Produced by cross-referencing the hand-written forwarding map with re/exports_table.json. An entry not listed here
reports its call and returns the documented neutral value, with its original bytes embedded and verified.

| ordinal | entry point | rva | size | implementation |
|---:|---|---:|---:|---|
| 25 | GetNumberOfNestings | 0xB0C0 | 52 | lcns::dll::exports::impl::getNumberOfNestings |
| 23 | GetNumberOfNestedParts | 0xB190 | 63 | lcns::dll::exports::impl::getNumberOfNestedParts |
| 17 | GetMultiplicity | 0xB100 | 34 | lcns::dll::exports::impl::getMultiplicity |
| 27 | GetPartUserString | 0xC5E0 | 36 | lcns::dll::exports::impl::getPartUserString |
| 210 | sub_16CF0 | 0x16CF0 | 8 | lcns::dll::exports::impl::getUserStringAt1B8 |
| 288 | sub_0AFF0 | 0xAFF0 | 10 | lcns::dll::exports::impl::setByteAtF8 |
| 286 | sub_0B000 | 0xB000 | 18 | lcns::dll::exports::impl::setDoubleAndFlag |
| 33 | GetSolution | 0xB0A0 | 29 | lcns::dll::exports::impl::getSolutionIdentity |
| 84 | SetLocalMaximumIterations | 0xD400 | 36 | lcns::dll::exports::impl::setInt_1FC |
| 146 | SetShearMode | 0xDDC0 | 33 | lcns::dll::exports::impl::setShearMode |
| 188 | CNS_SetNoMixPreference | 0xD310 | 33 | lcns::dll::exports::impl::setNoMixPreference |
| 222 | CNS_SetNoSheetMixPreference | 0xD340 | 33 | lcns::dll::exports::impl::setNoSheetMixPreference |
| 304 | SetShearRepulseFromBorders | 0xDE20 | 33 | lcns::dll::exports::impl::setShearRepulseFromBorders |
| 76 | UnLockLaunchingOrder | 0xD430 | 36 | lcns::dll::exports::impl::unlockLaunchingOrder |

Total: 14 of 168 entry points implemented. The remaining 154 fail loudly; the work queue in re/EXPORT_QUEUE.md
orders them by structural cost, and re/EXPORT_IMPLS.md records why the ones deliberately left alone are left alone.

## What pins each implemented item (round 403)

C6 asks every implemented entry point to have a differential test where the original can be executed and a
behavioural one where it cannot. The distinction is the point of the table: a differential test runs the
original and compares, a behavioural test checks the decoded field offsets and instruction sequence against
hand-computed expectations because the original reads a RIP-relative label string and cannot execute from the
embedded copy.

| entry or routine | kind | evidence |
|---|---|---|
| ordinal 25/26 -- GetNumberOfNestings | **behavioural** | tests/test_exports.cpp: container of 312-byte elements, stride derived from the element size |
| ordinal 23/24 -- GetNumberOfNestedParts | **behavioural** | tests/test_exports.cpp: container at sub+0x28, 120-byte elements |
| ordinal 17/18 -- GetMultiplicity | **behavioural** | tests/test_exports.cpp: 32-bit field at sub+0x20, not sign extended |
| ordinal 27/28 -- GetPartUserString | **behavioural** | tests/test_exports.cpp: pointer at part+0x1B8 |
| ordinal 33/34 -- GetSolution | **behavioural** | tests/test_exports.cpp: identity, no memory touched, null included |
| ordinal 210/211 -- sub_16CF0 | **behavioural** | tests/test_exports.cpp: the same field as GetPartUserString without the logger call |
| ordinal 288/289 -- sub_AFF0 | **behavioural** | tests/test_exports.cpp: byte = (arg != 0), 256 stores 1, neighbours untouched |
| ordinal 286/287 -- sub_B000 | **behavioural** | tests/test_exports.cpp: double at +0x100 and flag at +0xF9 |
| ordinals 146/188/222/304/76/84 -- the six int setters | **behavioural** | tests/test_exports.cpp: 32-bit store, -2 stored as 0xFFFFFFFE |
| not an export -- affine library, six routines | **DIFFERENTIAL** | tests/test_affine.cpp: 862 checks, bit for bit; the inverse comparison found a signed-zero difference |
| not an export -- orientation determinant 0x24B440 | **DIFFERENTIAL** | tests/test_affine.cpp: bit-exact over four operand sets plus sign semantics |
| not an export -- segment threshold kernel 0x55E190 | **DIFFERENTIAL** | tests/test_segcost.cpp: 3072 segment and parameter combinations, both outcomes |
| not an export -- box accumulator pair 0x5C8A10 and 0x50FD40 | **DIFFERENTIAL** | tests/test_boxacc.cpp: the whole 0x28-byte box byte for byte |
| not an export -- box merge 0x5C8C50 | **DIFFERENTIAL** | tests/test_boxacc.cpp: 2000 random boxes with the destination flag randomised, the INIT path included |

Two things this table makes visible: every entry point in the list is pinned by a test, and the four verified
routines that are NOT entry points (the affine library, the determinant, the segment kernel and the two box
routines) are pinned by differential comparison, which is the stronger of the two kinds.
