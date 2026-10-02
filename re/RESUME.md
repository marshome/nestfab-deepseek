# RESUME — how to continue this reverse engineering in a fresh session

## What this project is

`libcns_dump_64.dll` (Optalog CNS, MinGW-w64 GCC x64) is being reimplemented as the `lcns` C++ project. The working
directory is `D:\Nesting\nestfab`. `lcns/` holds the project, `re/` holds the reverse engineering evidence and the tools.

## The rules that govern the work

1. **`forwardedCount()` is the only progress number** and it must never rise on a guess. It counts rows in the hand written
   forwarding map `lcns/include/lcns/detail/exports_forwarding.inc`, one per export ordinal that forwards to a recovered
   implementation. It stands at **31 of 168**.
2. Never claim unread code is zero. `re/g_coverage.py` reports the unread domain mass honestly.
3. Keep the gate green before committing: build with zero errors and zero warnings, delete `build/test_*.exe` first so a
   stale binary cannot fake a pass, then `ctest`, then `tools/check_recovery.py`, `re/check_embeddings.py`,
   `re/g_coverage.py`, `re/g_acceptance.py`. Commit only when all of that is green **and** `git status --porcelain` is
   non-empty.
4. Do not push unless the human asks. Commits stay local.
5. Mark everything: `[已证实]` verified, `[推断]` inferred, `[未确认]` unconfirmed, `[不可恢复+原因]` not recoverable
   with the reason.
6. Scripts go in files under `re/`, never inline in a shell command. Two dozen rounds were lost to quoting, to a stray
   `if` in a one-liner, and to anchors that were an in-line prefix of a line instead of a whole line.

7. **Report every thirty rounds, not every round.** Work continuously between syncs; a round is one batch of work (a read, a
   classification, an implementation, a tool). Keep going until thirty have accumulated, then write one summary that says
   what moved, what the numbers are now, and what is next. The gate and the local commit still happen every round.

## The tools, and what each answers

| tool | usage | what it gives |
|---|---|---|
| `re/gate.ps1` | `.\re\gate.ps1` | the whole gate in one call: clean, build, ctest, check_recovery, check_arch, embeddings, coverage, acceptance. It sets PATH, CMake, Ninja and Python itself, so a fresh shell needs no setup. |
| `re/g_closure_work.py` | `python g_closure_work.py 51 38 2000` | the whole closure in work order, depth then size, followed by the unread leaf bodies: one batch per run |
| `re/g_closure_labels.py` | `python g_closure_labels.py 51 6` | every literal each function of the closure loads, with its target address, then the head of its body |
| `re/g_callers.py` | `python g_callers.py 0x9449E0` | who calls it, inside the closure first. A caller's address is context, not evidence; several library functions here are called by 0x2AB0 itself |
| `re/g_domain_closure.py` | `python g_domain_closure.py 51 [--all]` | what is left once library code is transparent: the domain set is computed FORWARD from the entry point, so nothing reached only through library code can enter it. This is the work list for this objective |
| `re/g_closure.py` | `python g_closure.py` | the transitive closure of every unimplemented export, and the leverage ranking, written to `re/WORKLIST.md` |
| `re/g_closure_of.py` | `python g_closure_of.py 51` | one export's closure, leaves first, plus the functions several closures share |
| `re/g_leaves.py` | `python g_leaves.py 51 12` | the smallest leaves of a closure, with their bodies |
| `re/g_eat_leaves.py` | `python g_eat_leaves.py 51 300` | recognises sixteen small shapes mechanically, generates accessors with their RVAs in the names and tests, registers them, prints what it cannot classify |
| `re/g_ready.py` | `python g_ready.py` | which exports need no further reading, which are platform forwarding, which cannot be equivalent by address |
| `re/g_labels.py` | `python g_labels.py [0x2AB0]` | the string literals a function hands the logger, which is where the names are |
| `re/g_label_classify.py` | `python g_label_classify.py 51` | classifies functions as library from their own strings: this removed 932 standard library functions from one closure in a single pass |
| `re/g_classify.py` | `python g_classify.py 0xADDR "reason" ...` | appends library classifications with their reasons |
| `re/g_embed.py`, `re/check_embeddings.py` | | the embedded original bytes and their byte for byte check against the dll |

The interpreter is `C:\Users\16479\AppData\Local\Python\bin\python.exe` (3.14, with pefile and capstone). A bare `python`
may not resolve in this shell, which is one reason `gate.ps1` names everything it runs.

## Where the work stands

* **31 of 168 exports forward** to recovered code. `re/EXPORT_IMPLS.md` records each with its evidence.
* **205 embedded blocks, 95533 bytes, all matching the dll**, 24 of them executable, which is what makes differential
  testing possible. `re/EMBEDDED.md` and `re/embedded_registry.json` are the registry.
* **Nine routines are held to the original by running it**: six affine routines, the orientation determinant, the segment
  threshold kernel, the box accumulator pair, the box merge, and four accessors. `lcns/tests/test_boxacc.cpp` and
  `lcns/tests/test_affine.cpp` are where they live.
* **The object model** in `lcns/include/lcns/dll_layout.hpp` has four element families (312, 120, 48, 216 bytes) with the
  modular inverses asserted, the window slots, the cached box carrier, and the angle constants.
* **`re/CATEGORIES.md`** holds the five classes of export (domain, platform, diagnostic, toolchain, platform forwarding),
  the three gate defects found, and the further lessons.
* **`re/EXPORT_BODIES.md`** holds the read bodies, the dependency chains, the span tables and the corrections.

## The current objective: LaunchLocalComputation

`re/LAUNCH_LOCAL_COMPUTATION.md` holds the terrain. It is `0x2AB0`, ordinals 51 and 52, 2134 bytes and 491 instructions,
the top level entry to the local optimiser, with two thin wrappers that ride on it (`0x3310` ordinal 164,
`0x3360` ordinal 216). Its closure was **1208 functions and 713168 bytes**; the label pass and the leaf work have taken it
to **131 functions and 37 leaves**. Its own labels say what it is: `LaunchLocalComputation`,
`// LaunchLocalComputation`, `c:\Temp\cns.pb.json`, `cns_force_cloud`, `cns1.optalog.com;cns2.optalog.com`.

**Batch seven (round 525) read all 38 leaves whole.** Forty five of them are library code with the evidence recorded next
to the address: the whole 0x63xxxx block of this closure is libstdc++'s `printf`/`num_put` numerics (0x63A2A0 divides by
ten with grouping, 0x63BF20 returns 'NaN' and 'Infinity'), the 0x86F/0x90E/0x921/0x922/0x944 cluster are the numpunct and
moneypunct facet-cache constructors (0x9449E0 stores '.' and ',' and then 'true' and 'false'), 0x874DD0 and 0x875640 fill
the time_put cache with the day and month names, 0x8268E0 is the ctype name table, and 0x998CD0/0x998EE0/0x998DA0 are
`__cxa_guard_acquire`/release/abort. One is domain: **0x5F3900**, twenty two bytes, which stores the timer object that
0x5F47C0 allocates, and it is implemented with its two assertions. The read is in `re/LEAVES51.txt`, the reasoning in the
round 525 section of `re/CATEGORIES.md`, and the recorder is `re/g_add_batch7.py`.

The order to work in: finish the remaining leaves, then the intermediate layers, and when the closure is empty write the
orchestration at `0x2AB0` itself and forward ordinals 51, 164 and 216 together, which is where `forwardedCount` goes up by
three.

**Batches eight and nine (rounds 526 and 527) took the closure from 131 functions to 26.** The twenty four functions
`0x2AB0` calls directly were read whole and none is an algorithm: they are libstdc++'s iostreams (the sentries, the write
through the vtable's `xsputn`, the `filebuf` open and close), the locale facet accessors that dynamic cast through
`0x9990E0`, the `basic_ios` state word, and the `shared_ptr` release and assignment. Batch nine closed the numeric layer:
`0x63B140` and the `num_put` overloads, and `0x6398E0`, which classifies an 80-bit long double as zero, infinity or NaN.
The reasoning is in the round 525, 526 and 527 sections of `re/CATEGORIES.md`.

That leaves **26 functions**: the orchestration at `0x2AB0`, the two wrappers, and the routines that touch this module's
own objects -- `0x1BF40`/`0x1BF00` over the module's lazy static (whose literal is `c:\Temp\debug_nest.txt`), `0x22A20`,
`0x65A530` (the three log files), `0x7BB430` (`CNS informations`), `0x5007C0`, `0x8F9220`, `0x92B340`, `0x92B940`,
`0x92BBA0`, `0x92ECB0`, `0x929FA0`, `0x9302C0` and `0x9308C0`. Those are the real work, and `re/g_domain_closure.py`
prints them in work order.

## Checkpoint (round 538)

| measure | value | where |
|---|---|---|
| `forwardedCount()` | **40 of 168** | `lcns/include/lcns/detail/exports_forwarding.inc` |
| embedded blocks | 205 / 95533 bytes, all matching | `re/EMBEDDED.md` |
| tests | 22 of 22, 116 of 116 acceptance checks | `re/gate.ps1` |
| domain functions named by the reporter channels | 251 read from their own call sites, 281 guessed and kept apart | `re/NAMES.md`, `re/name_registry.json` |
| this module's classes | **75**, from RTTI | `re/CLASSES.md` |
| LaunchLocalComputation closure | 7 functions, 6636 bytes | `re/LAUNCH_LOCAL_COMPUTATION.md` |

Implemented in this stretch, each with its evidence and its test:

* the launch order's layout, 0x2C0 bytes and 96 fields, read out of `0x14620 NewLaunchingOrder` -- `lcns/include/lcns/launching_order.hpp`
* the 0x48 byte node's copy and release, `0x9302C0` and `0x9308C0`, with the ownership rule the instructions gave --
  `lcns/include/lcns/cns_node.hpp`
* nine exports in one batch, all setters whose closures were empty: `SetOrigin` (86), `SetCommonCutCuttingPreference` (154),
  `CNS_SetMultiplicityPreference` (128), `SetAutomaticStop` (140), `SetCommonCutSafetyPreference` (150),
  `SetMultiTorchCuttingPreference` (176), `SetSpecificSheetOrigin` (298), `SetSpecificSheetObjective` (300) and `SetMarkMode`
  (246) -- `lcns/src/exports_impl.cpp`, and `test_exports.cpp` asserts every store

The rule that decides when a NAME may be used, which cost several rounds to get right:

* a field is named only when the module names it: an export that sets it, an accessor of at most 0x100 bytes that touches
  exactly that one offset and is named, or a serialiser key paired by its VALUE FLOW (key -> the accessor -> the argument the
  JSON constructor receives). Two independent witnesses are preferred and the count is recorded next to each name.
* twenty-six of the launch order's 96 fields clear that bar. The rest keep an offset-derived name (`unnamedXXX`) and the
  header says why. A plausible name with one weak witness is worse than a placeholder, because it hides the gap.

The three data sources that are open but not finished:

* the serialisers -- `..\structure\text_io.cpp`, `ToJson` at 0x50DB70, `LoadSheet` 0x5091B0, `LoadCommonCutEvaluation`
  0x509A40. The key vocabulary is recovered; the key-to-offset pairing needs the value flow, not the nearest accessor.
* the Multi vtables -- `re/CLASSES.md` lists them; the twelve strategies' `Run` bodies are the biggest single gap in this
  project and their classes are now identifiable.
* `re/g_class_sites.py` -- where each class is constructed, needing one more step: attribute a construction site by vtable
  ADDRESS rather than by class name, since two classes can share a name.

## What to tell a fresh session

> Continue the reverse engineering. Read `re/RESUME.md` first, then use the tools under `re/`. Work continuously without
> reporting every round, keep the gate green, commit locally, and do not push. The current objective is
> `re/LAUNCH_LOCAL_COMPUTATION.md`.
