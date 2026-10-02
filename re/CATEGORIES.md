# Category accounting

Required by C1 and C3: every category of reachable domain code is either **implemented** in `lcns/` with tests that pin
its behaviour, or **carried** 闂?its original bytes embedded in the project, with the reason it is not callable recorded
in the code 闂?or **unread**. This file is the ledger. It is maintained by hand on purpose: a mechanical count of
"addresses mentioned" is the metric this work already rejected once, because writing an address is not implementing
anything.

Counts are stated per category, not summed into a single progress number, so that the gap stays visible.

## Implemented, with the evidence

| Category | Routines | Where | Evidence |
|---|---|---:|---|
| **2x3 affine library** | `0x5CE7B0` build, `0x5CED50` invert, `0x5CE970` compose, `0x5CF6B0` apply out of place, `0x5CFD80` apply in place (one point), `0x5CFDC0` apply in place (two points) | `lcns/include/lcns/affine.hpp`, `lcns/src/affine.cpp` | `tests/test_affine.cpp` (862 checks) 闂?**all six routines compared bit for bit with the original**: compose over 36 matrix pairs, the three apply forms over 6 matrices x 5 points, the builder over 5 points, and the inverse over every non-singular matrix in the set; the inverse comparison found a **signed-zero** difference that a property test cannot see (appendix 274). Properties remain only for what has no oracle (singular rejection) |
| **Orientation determinant** | `0x24B440` | `lcns/src/affine.cpp` | `tests/test_affine.cpp` 闂?bit-exact against the original over four operand sets, plus the sign distinction between turn directions |
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
satisfies without any behaviour existing 闂?it is a proxy that can be satisfied by annotation, and it was rejected for
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

## Blocker kinds beyond domain: what the small ones turned out to be (round 427)

Three of the smallest high-frequency blockers were read whole. None is a domain algorithm:

| address | blocks | bytes | what it is |
|---|---:|---:|---|
| 0xAB20 | 29 | 98 | compiler-generated initialisation of a function-local static: read a global byte, double check under a guard, register a destructor through 0x63F6C8, construct through 0x998EE0, return the object address. **Not a domain dependency: it is boilerplate.** |
| 0x978750 | 38 | 51 | an allocation wrapper: allocate 8 bytes through 0x9988C0, store a vtable pointer loaded from a global, then call 0x999030 to construct. A constructor wrapper rather than an algorithm. |
| 0x8761B0 | 50 | 48 | a destructor-shaped routine: if the flag at +8 is clear it takes an error path, otherwise free the pointer at +0 through 0x63F6B8 and clear the flag. **This one IS domain**, and its dependencies are shallow: a free and an error call. |

The useful consequence: a fourth mechanical rule belongs in re/g_toolchain.py, for the static-initialisation boilerplate.
Its shape is a global byte flag, a test and branch on it, a call into the 0x63F6xx registration family, and a
LEA of a RIP-relative address returned to the caller. Functions of that shape have many callers, a handful of
instructions and no algorithm, so a frequency ranking puts them near the top for no good reason.

And the pair to read next is shallow: 0x97ABF0, the error path that 0x8761B0 calls, blocks 51 exports at 183 bytes;
with it and 0x8761B0 the destructor family can be implemented together.

## A fifth class: platform-forwarding exports, which must not count as progress (round 436)

GetPartUserStringEx (ordinal 55, rva 0xB020) and GetSheetUserStringEx (ordinal 61, rva 0xB060) were read whole. Both
are seventeen instructions and structurally identical:

    mov rdi, rcx           ; the object
    mov esi, edx           ; a 32-bit argument
    mov rbx, r8            ; the caller buffer
    lea rcx, [rip+...] ; call 0x64AEA0     ; the logger, no effect on its default path
    mov rdx, [rdi + 0x1B8] ; the user string (0x140 for the sheet variant)
    mov r8d, esi ; mov rcx, rbx
    jmp 0x63F228                           ; an import stub

The two differ only in which field they read and in the log label. Their actual work -- copying the string into the
caller buffer -- is done by the imported function at 0x63F228, which sits in the same stub bank as 0x63F390.

So implementing them would mean either forwarding to the platform function, in which case no domain logic has been
reversed, or reimplementing a CRT copy, which is not what this objective is about. Either way they are not evidence of
recovered domain behaviour, and they are therefore NOT counted in forwardedCount. They are recorded here as a fifth
class, platform-forwarding, with the mechanical rule that identifies them: a body that assembles its arguments and
then jumps or calls into 0x63F2xx or 0x63F3xx -- the import stub bank -- does its work outside the module.

This also corrects what the ready list means. re/g_toolchain.py reports six entries as implementable, but two of them
(55 and 61) are this class, so the real candidates are four: GetLength (96), GetHeight (100), GetFillRatio (168) and
GetNestingFillRatio (192). Those four hand an OBJECT to a domain implementer -- 0x526160, 0x5266A0 and 0x5297C0 --
rather than to an import stub, which is the distinction that matters.

## Two more gate lessons, both from rounds 495 to 498

These are recorded because each cost a round, and because the first one is a new class of mistake rather than a
repeat of the quoting problems already listed above.

1. An anchor must be a whole line or a structural line, never an in-line prefix. The script that added the angle
   constants used as its anchor the beginning of a declaration line,

       void copyPair28(void* destination, const void* element);   // RE 0x5203F0 -- first argument is the destination, per RCX/RDX

   which is a prefix of the real line, because the real line continues with the pair offsets. The membership test
   passed -- the prefix is a substring -- so the script wrote happily, and it inserted its new text in the MIDDLE of
   that comment, leaving the tail of the comment to start a new line with a colon. The compiler then reported
   expected unqualified-id before colon, twice, forty lines further down. An assertion that passes is not evidence
   that the edit is correct, so anchors are whole lines now: the angle script uses the namespace close line, which is
   unique and entire.

2. A variable that memcpy writes into must not be const. The angle test declared its bit pattern holder as
   const std::uint64_t and then passed its address to memcpy, which needs a void pointer. One word, one build failure,
   and the message pointed at the test line rather than at the declaration, which is why it took a read of the file to
   find.

Both were caught by the gate and neither was committed: the build failing is what stops a red tree from entering the
history, and the files were reverted to the last green commit in both cases.

## The LaunchLocalComputation leaves, read whole (round 525)

The closure of ordinal 51 came down to 131 functions and 38 leaves once the label pass had removed the standard library
functions that name themselves. All 38 were then read whole in one pass, and the split is not what the addresses suggest:
only one of them is domain code.

The whole 0x63xxxx block of that closure -- 0x639xxx, 0x63Axxx, 0x63Bxxx, 0x63Dxxx and 0x63Exxx, twenty three functions --
is libstdc++'s numeric layer, and the proof is per function rather than positional:

* 0x63A2A0 divides by ten with zero padding and digit grouping and calls 0x6399E0 per character emitted, which is already
  classified as library for reading the stream state flags. Its caller 0x63A570 is classified for its own label
  'PRINTF_EXPONENT_DIGITS'. That is `std::num_put::do_put(long)` and its unsigned sibling.
* 0x63BF20 returns the literals 'NaN', 'Infinity', 'aCoc' and '2ZGU' and calls 0x63BDA0, a bignum division over a 32-bit
  word array whose length sits at +0x14. 0x63EC00 turns the same word array into an IEEE double through bsr and shifts.
  That is printf's floating point formatter.
* The locale facets are identifiable the same way: 0x9449E0 stores '.' and ',' and then copies a 0x24 byte and a 0x1a byte
  table and the four and five byte strings 'true' and 'false', which is precisely the numpunct cache of decimal_point,
  thousands_sep, grouping, truename and falsename; 0x874DD0 fills its cache with Sunday, Monday, '%m/%d/%y', '%H:%M:%S',
  January and Jan, which is the time_put cache; 0x8268E0 is a jump table on the 16-bit character class constant that loads
  'upper', 'lower', 'alpha', 'digit', 'xdigit', 'space', 'print', 'graph', 'punct', 'cntrl', 'blank' and 'alnum'.
* 0x998CD0, 0x998EE0 and 0x998DA0 are `__cxa_guard_acquire`, the guarded static construction and `__cxa_guard_abort`:
  they take a guard byte, register a destructor through 0x63F6C8 and set the byte. Round 427 had already read 0xAB20 as a
  static initialiser that "constructs through 0x998EE0" without knowing that 0x998EE0 was the constructor it was calling.

The one domain leaf of the batch is 0x5F3900, twenty two bytes: it calls the timer accessor 0x5F47C0 -- sixteen bytes
allocated, a vtable stored, the process timer read twice and divided -- and stores the result in the caller's object. It is
implemented in `lcns/include/lcns/field_accessors.hpp` and held there by two assertions: the stored pointer is the
accessor's result, and two calls cannot return the same object.

The lesson worth keeping: a caller's address is not evidence. 0x8264E0 is called by 0x2AB0 itself, the entry point of this
objective, and it is still library code; 0x8A82F0 and 0x827240 call half of the locale constructors and are library code
themselves. What decided every entry above was a literal decoded from the function's own body, an offset pattern that names
a standard class, or the guard and throw machinery it hands control to.

## What the LaunchLocalComputation closure actually contains, and the counting rule (round 526)

Batch eight read the twenty four functions the entry point calls directly. Not one of them is an algorithm: they are
libstdc++'s iostreams, its locale facet accessors, its shared_ptr reference counting and a handful of destructors. The
evidence is recorded next to each address in `re/g_toolchain.py`, and the shape of it is worth stating because it decides
how the rest of this objective should be counted:

* The whole `0x63xxxx` block of the closure is the numeric and locale layer, and the `0x8Axxxx`/`0x90Exxx`/`0x921xxx`/
  `0x922xxx`/`0x944xxx`/`0x945xxx` block is the iostreams and the locale's facet caches. `0x8A82F0` is
  `std::locale::_S_initialize`, which installs every facet there is, and that is why one call reaches twelve hundred
  functions: it is not a domain dependency chain, it is the standard library's own construction.
* `0x2AB0` itself is orchestration over those objects. It builds an input file stream over `c:\Temp\cns.pb.json` (the
  stream construction at 0x2BB6 to 0x2C92 calls exactly the four functions batch eight classified), writes '-> ' and
  'LaunchLocalComputation' into an output stream, writes the double argument, and at the end reads two configuration strings,
  `cns_force_cloud` and the server list `cns1.optalog.com;cns2.optalog.com`, plus the debug marker
  `// LaunchLocalComputation`.

So the honest way to finish this objective is NOT to write reimplementations of `basic_ios::clear` or a facet accessor:
those already exist in the standard library this project links against, and reimplementing them would add code without
adding recovered behaviour. `forwardedCount` is a count of *recovered domain behaviour*, and the rule that keeps it honest
is the one this project already uses for the platform-forwarding class: code whose work is done by the standard library or
by the platform is classified, recorded, and not counted as progress.

What is left of the closure after batch eight is the orchestration at 0x2AB0, the two wrappers, and the domain routines
that touch this module's own objects -- among them `0x1BF40` (the engine fetch, whose own literal is
`c:\Temp\debug_nest.txt`), `0x22A20`, `0x65A530` (which opens the three log files `log_nest.txt`, `cloud_nest.txt` and
`local_nest.txt` and records three success flags) and `0x7BB430` (whose literal is `CNS informations`). Those are the
functions the orchestration is about, and they are what the next batches read.
