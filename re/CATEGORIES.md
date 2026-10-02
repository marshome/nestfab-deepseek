# Category accounting

Required by C1 and C3: every category of reachable domain code is either **implemented** in `lcns/` with tests that pin
its behaviour, or **carried** 鈥?its original bytes embedded in the project, with the reason it is not callable recorded
in the code 鈥?or **unread**. This file is the ledger. It is maintained by hand on purpose: a mechanical count of
"addresses mentioned" is the metric this work already rejected once, because writing an address is not implementing
anything.

Counts are stated per category, not summed into a single progress number, so that the gap stays visible.

## Implemented, with the evidence

| Category | Routines | Where | Evidence |
|---|---|---:|---|
| **2x3 affine library** | `0x5CE7B0` build, `0x5CED50` invert, `0x5CE970` compose, `0x5CF6B0` apply out of place, `0x5CFD80` apply in place (one point), `0x5CFDC0` apply in place (two points) | `lcns/include/lcns/affine.hpp`, `lcns/src/affine.cpp` | `tests/test_affine.cpp` (862 checks) 鈥?**all six routines compared bit for bit with the original**: compose over 36 matrix pairs, the three apply forms over 6 matrices x 5 points, the builder over 5 points, and the inverse over every non-singular matrix in the set; the inverse comparison found a **signed-zero** difference that a property test cannot see (appendix 274). Properties remain only for what has no oracle (singular rejection) |
| **Orientation determinant** | `0x24B440` | `lcns/src/affine.cpp` | `tests/test_affine.cpp` 鈥?bit-exact against the original over four operand sets, plus the sign distinction between turn directions |
| **Box accumulator pair** | `0x5C8A10` init-or-extend one pair, `0x50FD40` the box over a range of 312-byte elements | `lcns/include/lcns/boxacc.hpp`, `lcns/src/boxacc.cpp` | `tests/test_boxacc.cpp` -- the whole 0x28-byte box compared **byte for byte** (the flag included) against both originals over seven element sets and ten single-pair cases |
| **Segment threshold kernel** | `0x55E190` | `lcns/include/lcns/segcost.hpp`, `lcns/src/segcost.cpp` | `tests/test_segcost.cpp` -- compared against the original over **3072 segment/parameter combinations**, with both outcomes exercised; properties pin the operand order (which length takes which weight), the strictness of the comparison and zero-length degeneracies |
| **Angle transform readers** (pre-existing) | `0x5D38C0`'s transform, `0x5CEE50` angle -> transform | `lcns/include/lcns/row.hpp` | held to the original bytes by `tests/test_affine.cpp`: `transformX`/`transformY`/`transformDet` compared with `0x5CFD80` over 6 matrices x 5 points |
| **Embedded-original oracle** | the 11 callable blocks | `lcns/src/embedded/gen_orig.S` | `tests/test_embedded.cpp` (275 checks) and `tests/test_affine.cpp` call the originals; `re/check_embeddings.py` re-reads the DLL and fails on any byte or hash drift |

"Bit-exact" is the strongest evidence available here and it is why the embedding was built: an implementation that
produces the same bits as the original on the same inputs cannot be wrong about the arithmetic, only about the parts of
the original the tests never exercise.

## Carried, not yet implemented (bytes embedded, reason recorded)

These are read, registered and now embedded, but the project does not execute them and does not claim to:

| Category | Routines | Why not callable |
|---|---|---|
| ~~Floating-point class/range guard~~ -> **excluded as toolchain, see below** | `0x62FE20` | identified in round 356 as libm's sqrt |
| ~~Segment length pair and min/max~~ -> **implemented, see above** | `0x55E190` | was blocked by a call to libm's sqrt; now relocated and tested |
| ~~Accumulator over 312-byte elements~~ -> **implemented, see above** | `0x50FD40`, `0x5C8A10` | calls relocated to embedded blocks |
| Composition of two fields with weights | `0x24DD40` | relative calls to two helpers |
| Four-stage geometry chain | `0x24C610` | relative calls and RIP-relative data |
| Tolerance owner object | `0x4B81D0` | a relative call to the allocator |
| Twins' constructor | `0x111AD0` | a relative call plus two vtables read through RIP-relative operands |
| Largest routine's head | `0x243820` (15,524 bytes) | relative calls, RIP-relative data, and its size |
| Packed point add | `0x16C270` | *callable* and used as an oracle; its behaviour is not yet a library function |
| Field accessors | `0x51D2F0`, `0x4F8370`, `0x4F8380`, `0x4DDD10` | *callable*; the offsets are registered in `layout.hpp`, and the project's own object model is what needs them, so no code was added |

## Unread

The mass the coverage report names: **2,548 reachable domain functions / 1,479,459 bytes (31.7%)** at the last
measurement. `re/g_coverage.py` prints it; this file does not repeat it as a claim of progress.

## How this is counted, and why not mechanically

An earlier version of this work counted "addresses cited anywhere in `lcns/` or `re/`", which a constant in a header
satisfies without any behaviour existing 鈥?it is a proxy that can be satisfied by annotation, and it was rejected for
that reason. The implemented column above is therefore an explicit list, each row naming the routines and the test that
pins them. If the list is wrong, it is wrong in a way a reader can check by running one executable.

## Excluded: toolchain, with the evidence in the project

The objective excludes MinGW/libstdc++ from reverse engineering. Round 356 moved a block across that line, on evidence
rather than on convenience:

| Address | What it is | Evidence |
|---|---|---|
| `0x62FE20` (89 callers) | libm's `sqrt` | its own error path: the name string `"sqrt"` at rva `0xA06820`, `EDOM` (0x21) stored through the pointer `0x63F4D8` returns, then a call to the `__math_invalid`-shaped reporter `0x63FA50`; plus the standard shape of the routine (exponent/mantissa masks separating zero, denormal, normal, inf and NaN, an x87 `fsqrt`, and `+/-0.0`, `+inf` and `1.0` as its only constants) |
| `0x62FE00` | the packed sibling | it operates on the same constant cluster with `subps`/`xorpd` |
| `0x63F4D8` | `__errno` | returns the pointer that `sqrt`'s error path writes `EDOM` through |
| `0x63FA50` | libm's domain-error reporter | called from that path with the name string and the argument |

The evidence is not only written down: the thirty-two bytes at `0xA06820` are embedded in `lcns/` as a **data block**,
`re/check_embeddings.py` keeps them byte-identical to the DLL's, and `tests/test_embedded.cpp` asserts that they spell
`"sqrt"` and hold `-0.0`, `+inf` and `1.0`. A reader can therefore check the exclusion without opening the binary.

Consequence for the work: `0x55E190`'s recorded obstacle ("call to 0x62FE20 outside the block") is not a domain
dependency at all -- the segment kernel calls the C library's square root, which is what a length computation does.

## Relocated executable copies

A block whose only obstacle is a **call** can still be executed: the generated assembly writes that one instruction
symbolically (`call lcns_stub_sqrt`) so the assembler computes a displacement into this project, and the block is marked
`Status::CallableRelocated` with a **relocation list** recording every site, its original target and its replacement. The
original bytes remain embedded unchanged and `re/check_embeddings.py` keeps checking those, so the copy is visibly a test
instrument rather than a claim about the bytes.

Two kinds of target are supported: a **stub** the project supplies (`0x62FE20` -> `lcns_sqrt_shim`, i.e. `std::sqrt`), and
another **embedded block** whose symbol already exists. `0x55E190` was the first to use it (three sqrt calls to a stub)
and `0x50FD40` the first to use it entirely with blocks (six sites: the getter `0x51D2F0` twice, the accessors
`0x4F8370`/`0x4F8380`, and the box accumulator `0x5C8A10` twice).

## The export C ABI surface (added in round 360)

The original module exports **168 functions**. The user's requirement is that the project correspond to all of them and
that each implementation agree with the assembly, so this surface is now a category of its own rather than an omission:

| | |
|---|---|
| Entry points **defined** in `lcns/src/api_exports.cpp` (generated by `re/g_api_exports.py`) | **168 / 168** |
| With a signature from the inferred typed table | 141 |
| With a signature synthesized from the argument-register analysis | 27 (recorded as opaque: the interleaving of integer and floating-point arguments is not recoverable from the table) |
| **Forwarding** to a recovered C++ implementation | **0** |
| Reporting the call and returning the documented neutral value | **168** |
| Entry points whose original bytes are embedded and verified against the module | **168 / 168** (70.5 KB, by `re/g_embed.py` reading `re/exports_table.json`, checked by `re/check_embeddings.py`) |

What this buys, and what it does not:

* a caller linking against the project finds **every name the original offers**, with the ABI the reverse engineering
  inferred;
* a not-reversed entry point **cannot return a plausible wrong answer**: it records the call and returns 0, null or NaN,
  and `re/check_embeddings.py` keeps its assembly in the tree byte for byte, so the gap is visible at the point of use;
* **it does not yet implement the engine behind the entry points.** `forwardedCount()` is the number that says so, it is
  printed by `tests/test_exports.cpp`, and raising it is the work of the coming rounds -- each entry recovered with a
  differential test against the original where the original can be executed (the relocation machinery of rounds 357-359
  is what decides that).

The original exports by **ordinal** (`NumberOfNames = 0`); its "names" are the labels the functions log, which is why two
entries can share a label. The table keeps the label as evidence and uses the ordinal as the identity -- including as the
key of the forwarding map.

## State at round 385 (measured, not asserted)

Recorded here so the round-414 checkpoint finds the numbers in the tree. Every figure below was measured in round 384
with freshly linked binaries -- the stale `test_*.exe` files were deleted before `ctest` ran, which is the lesson from
round 380, where a stale binary made a failed build look green.

| Measure | Value | How it was obtained |
|---|---|---|
| Exported entry points implemented (`forwardedCount()`) | **14 of 168** | rows in `lcns/include/lcns/detail/exports_forwarding.inc`, which is hand-written so regeneration cannot erase one |
| Entry points defined in the C ABI layer | **168 of 168** | `lcns/src/api_exports.cpp`, generated from `re/exports_table.json` |
| Entry points whose original bytes are embedded and verified | **168 of 168** | `re/g_embed.py` reads the whole export table; `re/check_embeddings.py` compares them with the module |
| Embedded blocks / bytes | **195 / 92,861** (20 executable) | `re/check_embeddings.py`: "checked against libcns_dump_64.dll: all match" |
| `tests/test_exports` checks | **?** | its own output |
| Build | 0 errors, 0 warnings | `cmake --build build` |
| Tests | 22 of 22 | `ctest` after deleting stale binaries |
| Domain code still to reverse | 2,490 functions / 1,449,418 bytes / 31.0% | `re/g_coverage.py` |

A not-reversed entry point is not silent: its definition calls `lcns::dll::exports::notReversed()`, which records the call
and identifies the export, and it returns the documented neutral value for its return type (0, null or NaN). The number
`forwardedCount()` is the only figure this work treats as progress, and it is monotonic: 0, 4, 8, 13, 14 over rounds 360
to 364.

### What is verified by differential comparison rather than by property

The affine library (six routines, 862 checks, including a signed-zero difference the property tests could not see), the
orientation determinant, the segment threshold kernel (3,072 combinations), the box accumulator pair (whole 0x28-byte box,
byte for byte), and the box merge `0x5C8C50` -- whose differential test is written and whose model agreed on nine of ten
fixtures in round 380, with the tenth left open and the original's ten outputs recorded in `re/EXPORT_IMPLS.md`.

## Gate defects found in this session, and their fixes

Three defects were found in the checks this work runs before committing. They are recorded here because each one produced
a false signal at least once, and a false green is worse than a red.

1. A stale test binary made a failed build look green. The build had failed, so the test executables were never relinked,
   and ctest then ran the OLD executables and reported 22 of 22. Fix: delete build/test_*.exe before building and before
   running ctest. This is now done in every gate run.

2. A commit was reported when nothing had been committed. The commit branch tested only the build, ctest and registry, not
   whether the tree had actually changed, so nothing-to-commit still printed COMMITTED. Fix: require a non-empty change set
   before reporting a commit.

3. git status cannot see ignored files, so it cannot be the change test for them. The rule .gitignore line 71 re/g_*.py was
   silently hiding sixteen generator scripts, including the one that produces the embedded bytes and the one that produces
   the 168 C ABI definitions. git add -A skipped them, and git status --porcelain reported a clean tree, so the commit
   branch never ran. Fix: for any path that may match an ignore rule, run git add -f with explicit paths and then verify with
   git ls-files. Never rely on git status for that question.

The third defect also invalidated commit messages from earlier rounds that named such scripts: the message claimed a file
   the commit did not contain. Those scripts are now tracked, which is what makes the generated documents reproducible from
   a clone.
