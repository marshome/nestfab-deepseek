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

## The tools, and what each answers

| tool | usage | what it gives |
|---|---|---|
| `re/g_closure.py` | `python g_closure.py` | the transitive closure of every unimplemented export, and the leverage ranking, written to `re/WORKLIST.md` |
| `re/g_closure_of.py` | `python g_closure_of.py 51` | one export's closure, leaves first, plus the functions several closures share |
| `re/g_leaves.py` | `python g_leaves.py 51 12` | the smallest leaves of a closure, with their bodies |
| `re/g_eat_leaves.py` | `python g_eat_leaves.py 51 300` | recognises sixteen small shapes mechanically, generates accessors with their RVAs in the names and tests, registers them, prints what it cannot classify |
| `re/g_ready.py` | `python g_ready.py` | which exports need no further reading, which are platform forwarding, which cannot be equivalent by address |
| `re/g_labels.py` | `python g_labels.py [0x2AB0]` | the string literals a function hands the logger, which is where the names are |
| `re/g_label_classify.py` | `python g_label_classify.py 51` | classifies functions as library from their own strings: this removed 932 standard library functions from one closure in a single pass |
| `re/g_classify.py` | `python g_classify.py 0xADDR "reason" ...` | appends library classifications with their reasons |
| `re/g_embed.py`, `re/check_embeddings.py` | | the embedded original bytes and their byte for byte check against the dll |

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
to **131 functions and 38 leaves**. Its own labels say what it is: `LaunchLocalComputation`,
`// LaunchLocalComputation`, `c:\Temp\cns.pb.json`, `cns_force_cloud`, `cns1.optalog.com;cns2.optalog.com`.

The order to work in: eat the remaining leaves, then the intermediate layers, and when the closure is empty write the
orchestration at `0x2AB0` itself and forward ordinals 51, 164 and 216 together, which is where `forwardedCount` goes up by
three.

## What to tell a fresh session

> Continue the reverse engineering. Read `re/RESUME.md` first, then use the tools under `re/`. Work continuously without
> reporting every round, keep the gate green, commit locally, and do not push. The current objective is
> `re/LAUNCH_LOCAL_COMPUTATION.md`.
