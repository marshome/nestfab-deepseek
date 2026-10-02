# Export implementations

What stands behind each exported entry point, and what the claim rests on. `forwardedCount()` is the number of entries
whose behaviour is implemented. Every other entry reports the call and returns the documented neutral value, with its
original bytes embedded and verified against the module by `re/check_embeddings.py`.

| Entry (ordinals) | rva | Recovered behaviour | Held to the assembly by |
|---|---:|---|---|
| `GetNumberOfNestings` (25/26) | `0xB0C0` | element count, 312-byte stride, container at +0x50/+0x58 | behavioural test; the multiply is the modular inverse of 39 |
| `GetNumberOfNestedParts` (23/24) | `0xB190` | the same over `[+8]+0x28`, stride 120 | behavioural test; inverse of 15 |
| `GetMultiplicity` (17/18) | `0xB100` | 32-bit field at `[+8]+0x20` (via `0x51D090`) | behavioural test |
| `GetPartUserString` (27/28) | `0xC5E0` | pointer at +0x1B8 | behavioural test |
| `GetSolution` (33/34) | `0xB0A0` | identity: returns its argument, no memory touched | behavioural test |
| `sub_16CF0` (210/211) | `0x16CF0` | pointer at +0x1B8, without the logger call | behavioural test |
| `sub_AFF0` (288/289) | `0x0AFF0` | byte +0xF8 = (arg != 0) | behavioural test |
| `sub_B000` (286/287) | `0x0B000` | double at +0x100, byte +0xF9 = (arg != 0) | behavioural test |

## Why these cannot be compared by running the original

Each begins by passing a RIP-relative label string to the logger, or is reached only through a fragment that does, so the
embedded copy cannot execute from a different image address. They are therefore established by **behavioural** tests built
from the decoded field offsets and instruction sequence, each expectation computed by hand and printed by the test.

## Deliberately not implemented, with the reason

| Entry (ordinals) | rva | Why not |
|---|---:|---|
| `sub_AFE0` (270/271) | `0x0AFE0` | a thunk: `setne cl; movzx ecx,cl; jmp 0x1B270`. It converts its first argument to a boolean and tail-calls `0x1B270`, whose behaviour is not recovered. Writing the thunk without the callee would do nothing or invent the callee's effect. |
| `GetBuildVersion` (88/89) | `0x0B490` | returns the pointer held in the MODULE's global at rva `0xAB7660` -- data owned by the original image. A reimplementation cannot return that address, and what it should return instead is a semantics decision, not a decoding one. |

## Side effects not reproduced

Several entries log through `dbg::symlog` before doing their work. Logging is a toolchain facility, not domain behaviour,
and it affects no return value; it is not reproduced. Where an entry's only effect beyond logging is a return value, that
value is reproduced exactly.


## A contradiction found while modelling the objects (round 362) -- recorded because it invalidates an assumption

Attempting to express the recovered offsets as real C++ structures produced four compile-time contradictions, and they
are informative rather than cosmetic:

* GetNumberOfNestings (0xB0C0) reads [order+0x50] and [order+0x58] as POINTERS and counts elements of 312 bytes --
  that is a container whose begin and end live at +0x50 and +0x58;
* SetShearRepulseFromBorders (0x0DE20) stores a 32-BIT value at [order+0x58];
* SetShearMode (0x0DDC0) stores one at +0x44, SetLocalMaximumIterations (0x0D400) at +0x1FC, UnLockLaunchingOrder
  (0x0D430) at +0x244.

A field cannot be both a pointer and a 32-bit integer, so **these functions do not all take the same object type**. The
only reason they were attributed to one object is the inferred signature column of lcns/detail/api_typed.inc, which
says SetShearMode(Order, int) and so on -- and that file states, in its own header, that its signatures are INFERRED.
The contradiction is therefore evidence that the inferred signatures are not reliable enough to merge objects on, and the
model has to keep them apart:

* the object that owns the nesting container: +0x50 begin, +0x58 end, +0x60 capacity (312-byte elements);
* the objects the int setters write: +0x18, +0x1C, +0x44, +0x58, +0x1FC, +0x244, as 32-bit fields -- at least one of
  which is a DIFFERENT type from the first, since +0x58 is spoken for.

Until an entry point's own code ties a setter to the container's owner (for instance a setter that reads or writes both),
the two stay separate types in the model. The implementations themselves are unaffected: a store to a fixed offset is a
store to a fixed offset, and that is what the tests verify.


## 0x5C8C50 differential test: draft result (round 380)

A ten-fixture differential comparison against the original was written and built cleanly (no warnings). Nine of the ten
fixtures matched the original byte for byte; one did not, so the model was reverted rather than committed. The fixtures
were: source uninitialised; both uninitialised; destination uninitialised with positive extents; destination
uninitialised with negative extents; source inside the destination; source outside; crossing (source max below
destination min); far outside; signed zeros; equal values.

The failing one is most likely either the INIT branch (0x5C8D10, which builds the destination from the source and then
falls into the tail at 0x5C8CDB carrying xmm1/xmm3/xmm2 from the freshly written fields) or the negative-extent
initialisation, because those are the two places where the register contents across the branch differ from the plain
path. Next round: print the mismatching fixture''s 0x28 bytes from both sides, fix the model, and re-run -- the original is
callable, so this is a matter of reading the difference, not of guessing.

## The original 0x5C8C50's output, fixture by fixture (round 381 measured, round 382 recorded)

A probe called the embedded original -- executable since round 377 -- over ten fixtures and printed the resulting
box. These ARE the expected bytes, so the model is corrected against them rather than against reasoning. Layout:
flag +0x00, minX +0x08, minY +0x10, maxX +0x18, maxY +0x20.

| case | src flag | dst flag | src (minX,minY,maxX,maxY) | dst in | result | flag |
|---:|---:|---:|---|---|---|---:|
| 0 | 1 | 0 | (0,0,0,0) | (1,2,3,4) | (1,2,3,4) | 0 |
| 1 | 1 | 1 | (0,0,0,0) | (0,0,0,0) | (0,0,0,0) | 1 |
| 2 | 0 | 1 | (5,6,7,8) | (0,0,0,0) | (5,6,7,8) | 0 |
| 3 | 0 | 1 | (-5,-6,-7,-8) | (0,0,0,0) | (-7,-8,-5,-6) | 0 |
| 4 | 0 | 0 | (1.5,2.5,2.5,3.5) | (1,2,3,4) | (1,2,3,4) | 0 |
| 5 | 0 | 0 | (-1,-2,9,10) | (1,2,3,4) | (-1,-2,9,10) | 0 |
| 6 | 0 | 0 | (-9,-10,-1,-2) | (1,2,3,4) | (-9,-10,3,4) | 0 |
| 7 | 0 | 0 | (100,200,300,400) | (1,2,3,4) | (1,2,300,400) | 0 |
| 8 | 0 | 0 | (-0.0,-0.0,0.0,0.0) | (0.0,0.0,-0.0,-0.0) | (0.0,0.0,-0.0,-0.0) | 0 |
| 9 | 0 | 0 | (1,2,3,4) | (1,2,3,4) | (1,2,3,4) | 0 |

Hex exactly as printed (so signed zeros are visible):

```
case  0 -> minX=3ff0000000000000 minY=4000000000000000 maxX=4008000000000000 maxY=4010000000000000 flag=0
case  1 -> minX=0000000000000000 minY=0000000000000000 maxX=0000000000000000 maxY=0000000000000000 flag=1
case  2 -> minX=4014000000000000 minY=4018000000000000 maxX=401c000000000000 maxY=4020000000000000 flag=0
case  3 -> minX=c01c000000000000 minY=c020000000000000 maxX=c014000000000000 maxY=c018000000000000 flag=0
case  4 -> minX=3ff0000000000000 minY=4000000000000000 maxX=4008000000000000 maxY=4010000000000000 flag=0
case  5 -> minX=bff0000000000000 minY=c000000000000000 maxX=4022000000000000 maxY=4024000000000000 flag=0
case  6 -> minX=c022000000000000 minY=c024000000000000 maxX=4008000000000000 maxY=4010000000000000 flag=0
case  7 -> minX=3ff0000000000000 minY=4000000000000000 maxX=4072c00000000000 maxY=4079000000000000 flag=0
case  8 -> minX=0000000000000000 minY=0000000000000000 maxX=8000000000000000 maxY=8000000000000000 flag=0
case  9 -> minX=3ff0000000000000 minY=4000000000000000 maxX=4008000000000000 maxY=4010000000000000 flag=0
```

What these bytes settle, and what they do NOT:

* the INIT path (destination flag non-zero) stores the source's MIN corner into all four fields, and the tail then
  moves minX and minY DOWN to the source's maxX and maxY while the maxes keep what INIT stored: case 3 ends at
  (-7,-8,-5,-6), not at (-5,-6,-5,-6). A model that treated the source's max corner as an upper bound would fail
  exactly here, which is the kind of plausible-looking error a differential test exists to catch;
* case 2 shows the tail does run on the INIT path (maxY ends at 8, the source's maxY, not at 6);
* case 8 keeps signed zeros: the maxes stay -0.0 although +0.0 was offered, because +0.0 > -0.0 is false;
* and the outstanding contradiction is recorded rather than resolved: hand-checking the model against ALL ten of
  these rows says it matches every one, so round 380's single failure is more likely a defect in the test harness
  (fixture plumbing) than in the model. The next run must print BOTH sides per fixture to decide.

## 0x5C8C50 randomised cross-check: the mismatch is localised (round 386)

A probe compared the model with the original over 5000 deterministic pseudo-random boxes. **521 disagreed**, and the
printed cases localise the fault to one place: **maxX**. In every printed case the original keeps a maxX that is the
larger of what was there and the source''s max corner, while the model ends with a smaller value -- the source''s minX, or
a value derived from it:

```
case  0  src maxX=1.5    model maxX=-0.0   original maxX=1.5
case 13  src maxX=100    model maxX=1.5    original maxX=100
case 19  src maxX=7      model maxX=0.0    original maxX=7
```

So the reading error is in the instruction at `0x5C8C88` (`ucomisd xmm0, [rcx+0x18]` followed by the conditional store at
`0x5C8C8F`), which the model implements as "maxX = max(maxX, src.minX)". Either the operand it compares is not
`src.minX` at that point, or the store is guarded by an earlier branch''s register state that the model does not
reproduce. The ten fixed fixtures did not expose it; 5000 random ones did, and the differential comparison is what found
it -- the same mechanism that caught the signed-zero error in the affine inverse in round 359.

Next step is narrow: dump `0x5C8C50`''s first twelve instructions again, trace `xmm0` at `0x5C8C88` through BOTH entry
branches, correct the model, and re-run this probe until it reports zero mismatches of 5000. Only then is the model moved
into `lcns/src/boxmerge.cpp`.

## 0x5C8C50 status correction (round 405)

An earlier section of this file says the box merge model was reverted rather than committed after nine of ten
fixtures agreed. That is now out of date, and this note supersedes it:

* the root cause was found in round 393 and is recorded in re/MERGE_MAX_X.md: on the INIT path the original jumps
  to 0x5C8CDB, the maxX check inside the second pass, which runs BEFORE the tail at 0x5C8CE7, while the model did
  only the minX half on that path; every mismatching fixture had a destination flag of 1;
* with that corrected, the model agrees with the original on **5000 of 5000** random boxes, invalid ones included
  (re/_probe_invalid.cpp);
* the verified worker is now in **lcns/src/boxmerge.cpp** with its declaration in lcns/include/lcns/boxmerge.hpp
  (commit ec6f689), copied unchanged and only wrapped;
* and it is **continuously tested**: tests/test_boxacc.cpp compares it with the original over 2000 random boxes
  with the destination flag randomised, so the INIT path is inside the sample (commit efc99d7).

Nothing calls it yet, so no exported behaviour has changed: it is a verified piece of the common step behind
GetLength (0x526160), GetHeight (0x5266A0) and the container construction of 0x5CD800, waiting for those three
exports to be implemented on top of it.

## GetPartWithBadGeometry (ordinals 29/30, rva 0xB510) -- implemented in round 432

Thirteen instructions, no calls but the logger, read whole:

    0B524  edx = dword [rbx + 0x4C]      ; a 32-bit status field
    0B527  eax = 0                       ; the default return is null
    0B529  cmp edx, 1 ; jne 0B535        ; only status 1 continues
    0B52E  rax = qword [rbx + 0xA0]      ; the pointer that is returned
    0B535  ret

So: object[+0xA0] when object[+0x4C] is 1, null otherwise. Implemented in lcns/src/exports_impl.cpp as
getPartWithBadGeometry, with the two offsets asserted by the compiler in BadGeometryCarrier (lcns/dll_layout.hpp).
That carrier is deliberately NOT PartObject: the export has a log label but no typed signature a reader can trust, so
only the two offsets are known and the type name says so.

Evidence: BEHAVIOURAL, not differential. None of the entries in this file can be compared by running the original,
because each begins by handing a RIP-relative label string to the logger at 0x64AEA0, so the embedded copy cannot
execute from a different image address. What the behavioural test checks is exactly the decoded behaviour: status 0
returns null, status 2 returns null, status 1 returns the pointer at +0xA0, and a null at +0xA0 still returns null.

The logger itself was shown in round 369 to do nothing on its default path (it tests a global switch and returns), so
leaving it out is a faithful simplification rather than an omission, and that is recorded rather than assumed.
