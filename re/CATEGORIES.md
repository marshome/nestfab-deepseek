# Category accounting

Required by C1 and C3: every category of reachable domain code is either **implemented** in `lcns/` with tests that pin
its behaviour, or **carried** — its original bytes embedded in the project, with the reason it is not callable recorded
in the code — or **unread**. This file is the ledger. It is maintained by hand on purpose: a mechanical count of
"addresses mentioned" is the metric this work already rejected once, because writing an address is not implementing
anything.

Counts are stated per category, not summed into a single progress number, so that the gap stays visible.

## Implemented, with the evidence

| Category | Routines | Where | Evidence |
|---|---|---:|---|
| **2x3 affine library** | `0x5CE7B0` build, `0x5CED50` invert, `0x5CE970` compose, `0x5CF6B0` apply out of place, `0x5CFD80` apply in place (one point), `0x5CFDC0` apply in place (two points) | `lcns/include/lcns/affine.hpp`, `lcns/src/affine.cpp` | `tests/test_affine.cpp` — compose compared to the original over **36 matrix pairs, all six doubles bit-exact**; the three apply forms bit-exact over 6 matrices x 5 points; properties for the builder and the inverse (composition with the inverse, round-trip points, singular rejection) |
| **Orientation determinant** | `0x24B440` | `lcns/src/affine.cpp` | `tests/test_affine.cpp` — bit-exact against the original over four operand sets, plus the sign distinction between turn directions |
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
| Accumulator over 312-byte elements | `0x50FD40` | relative calls to three helpers outside the block |
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
satisfies without any behaviour existing — it is a proxy that can be satisfied by annotation, and it was rejected for
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
another **embedded block** whose symbol already exists. That is what turned `0x55E190` from comment-only into something a
differential test can call, and it is the mechanism the remaining call-blocked blocks will use.
