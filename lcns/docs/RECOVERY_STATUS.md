# 逆向状态总表（由 `include/lcns/recovery.hpp` 生成）

本工程把代码分成五种状态，**每一处在源码里都有一个可 grep 的标记**，
并与 `recovery.hpp::kGaps` 登记表逐条对应；`tools/check_recovery.py` 强制「代码标记集合 == 登记表集合」，且带具体 RVA 的缺口必须出现在 `re/` 文档中。

| 状态 | 含义 | 条目数 |
|---|---|---:|
| `Recovered`（已恢复） | instruction-level faithful; constants cite RVAs checked by tests | 7 |
| `Structural`（结构已恢复） | structure/algorithm skeleton recovered; body re-implemented | 14 |
| `Substituted`（替代实现） | the original uses something unavailable here, or heuristic constants were NOT recovered | 27 |
| `NotReversed`（**尚未逆向**） | feature exists in the DLL but has NOT been reverse engineered (the only macro that means this) | 11 |
| `NotInBinary`（非原库） | our own extension | 1 |

> 未逆向 ≠ 未知：凡是标为 `NotReversed` 的，都给出了它在二进制中的地址（或明确写了"-"），说明它**存在**但我们**没有译出**；凡是 `Substituted` 的，说明这里跑的是**替代实现**，不是原库算法。


## Recovered（已恢复）

| id | DLL 地址 | 说明 | 标记位置 |
|---|---|---|---|
| `module.api` | `168 exports` | export table (ordinal only, NumberOfNames = 0) recovered from the PE export directory | src/api.cpp:21 |
| `api.ordinal_loader` | `0x0` | ordinal -> function mapping and the 162 recovered names (REPORT section 4) | src/api.cpp:64 |
| `geom.orient128` | `0x58E450` | exact orientation predicate; its complete caller set (13) is enumerated in findings_geometry.md | include/lcns/geom.hpp:128 |
| `module.model` | `-` | Part/Sheet/Order/Nesting/Solution field order and the Set*/Add* landing offsets are recovered from the setters and CreateProblem 0x1EE50 (REPORT section 7.4) | src/model.cpp:8 |
| `module.row` | `0x134470 0x133DE0 0x136350 0x13A360` | the per-part path was translated instruction by instruction; the 216 B element layout is locked by 15 static_asserts in include/lcns/row.hpp | src/row.cpp:7 |
| `lp.clp_backend` | `Coin::CoinLP slots 3/4/5/8; OsiClpSolverInterface` | the REAL COIN-OR CoinUtils/Osi/Clp is downloaded (third_party/README.md) and linked: third_party/CMakeLists.txt builds the trio with the project's own GCC 13.1, and lcns::lp::ClpLinearProgram drives OsiClpSolverInterface through the recovered contract (reset/addColumn/addRow/solve/primal/dual) with the recovered storage shape (3 parallel per-column vectors + a 16 B triplet list sorted column-major, i.e. 0x7CA830). tests/test_linear_program.cpp cross-checks it against the built-in backend on the recovered driver buildAndSolveLp (0x7D7200): objective and duals must agree, and each answer must be feasible and reproduce its own objective. VERSION IS EVIDENCED, not guessed: the dump contains '@C:\\Users\\renaud\\nest\\external\\clp-1.15.3\\Clp\\src\\ClpSimplexDual.cpp' at 0x9C9E1F and 'Clp-1.15.3\\CoinUtils\\src\\CoinLpIO.cpp' at 0x9D2D30, so Clp is built from the exact releases/1.15.3 tag (its configure reports CLP_VERSION \"1.15.3\"); CoinUtils/Osi come from the matching stable/2.10 and stable/0.107 branches, whose exact patch levels are NOT string proven | src/lp_clp.cpp:18 |
| `lp.canonicalise` | `0x7CA830` | in-place sort of the +0x90 triplet accumulator into column-major COO order, then 3-space text rendering | src/lp.cpp:463 |

## Structural（结构已恢复）

| id | DLL 地址 | 说明 | 标记位置 |
|---|---|---|---|
| `tu.svg_io` | `0x7CCDF0 writer; exports 326/328 (0x9550/0x9790)` | the DOCUMENT SCHEMA is recovered and implemented in lcns::toSvg: px+viewBox header with version/xmlns:xlink, <defs><pattern id=diagonalHatch0 patternUnits=userSpaceOnUse>, the outer <g transform=scale(1,-1)>, per-item translate groups, fill-rule=evenodd paths, the mark circle r=0.5% in stroke:rgb(192,0,0), and the style fragments of 0x5DAEB0/0x5DDDD0/0x5DC9D0/ 0x5DE320/0x5DCE70/0x5D9BF0/0x516380. NOT reversed yet: the remaining ~169 KB of the TU (the <use>/<defs> geometry variant of export 328, the HTML report side at 0x5100D0/0x5190B0, and the part-statistics lines multiplicity/height/fill-ratio) | src/engine.cpp:219 |
| `module.geom` | `..\\exact\\* + ..\\geom\\*` | fixed-point scale 1e10 (0x9AD708) and the 128-bit predicate (0x58E450) are recovered; the boolean/offset bodies are a re-implementation of the recovered structure | src/geom.cpp:10 |
| `geom.boolean_kernel` | `0x596100 etc.` | the convolution core's quadrant classification and event merge are recovered as a structure; the implementation here is not a transcription | src/boolean.cpp:11 |
| `geom.point_in_polygon` | `inlined; 0x1C1A60` | the DLL has no standalone containment routine: the test is INLINED at its assertion sites; the recovered predicate (+0x60/+0x68 with epsilon 0.001 @0x9BFD30) is reproduced here | src/geom.cpp:203 |
| `geom.offset` | `0x58A7E0 / 0x12C60` | N = floor(dist/step + 0.5) incremental offset and outer +gap / inner -gap are recovered; the body is a re-implementation | src/geom.cpp:131 |
| `module.nfp` | `0x8AC0 / 0x665BF0 / 0x687080` | cache thresholds (25000 @0x61A8, 19999999 @0x1312CFF) are recovered constants; the map machinery here is a re-implementation | src/nfp.cpp:9 |
| `row.finalize_passes` | `0x1B33B0 / 0x40720 / 0x1E1BF0` | the recovered order (postop -> renest in holes -> packed bottom left) is honoured; each pass is a re-implementation | src/nester.cpp:955 |
| `module.engine` | `0x827F0 / 0x2DF60 / 0x2CCF0` | the supervisor/cascade structure and the cancel gate (elapsed / Problem[+0x408] > 1.0) are recovered; the per-strategy budget bookkeeping here is a re-implementation | src/engine.cpp:10 |
| `module.lp` | `Lp::LinearProgram / Coin::CoinLP` | the CoinLP slot structure and the 3 parallel vector + COO accumulator layout are recovered | src/lp.cpp:13 |
| `lp.pricers` | `0xA3B0C0 / 0xA3B100 / 0xA3B140 / 0xA3B180` | the four pricers and their accessors are recovered (Box area 0x7C9D90, Hull +0x48, Alpha +0x68, weighted mean); the surrounding driver is a re-implementation | src/lp.cpp:589 |
| `module.io` | `JsonCpp keys @0x9DA300..0x9DB010` | the problem/solution JSON keys are recovered from the string table; the parser/writer is self contained here | src/io.cpp:13 |
| `io.dxf` | `GenerateDxfNesting 0xBF70 -> DrawDxf` | R12 DXF with SHEET/PART/HOLES layers is recovered as a structure | src/io.cpp:619 |
| `module.cloud` | `0x26A60 (CloudEngine::Run)` | the HTTP shape (/pb/, /sol/, best_sol, the request headers) is recovered from literals | src/cloud.cpp:36 |
| `module.licensing` | `0x14620 etc.` | PCId/machine binding and the HASP flags are recovered; the Sentinel API itself is loaded at runtime and is not reconstructed | src/licensing.cpp:22 |

## Substituted（替代实现）

| id | DLL 地址 | 说明 | 标记位置 |
|---|---|---|---|
| `module.nester` | `12 strategies` | each strategy's identity (vtable address point, Run size, key literals) is recovered, but EVERY Run body here is our own placement search: the original bodies are not transcribed | src/nester.cpp:348 |
| `search.pack_all` | `0x378E0 (NestingNester::Run, 14374 B)` | packAll is a bottom-left/beam placement search we wrote; the original main packer was not transcribed | src/nester.cpp:349 |
| `search.beam_width` | `option beam_width (reader 0x4EECB)` | BeamParams::width. The MECHANISM is recovered: the binary holds no constant at all, it looks the value up in the option table under beam_width / beam_advanced_width (reader 0x4F342) / beam_expert_width (reader 0x4F365), and reports it at 0x655DC6. The default value here is therefore ours (a tunable), not a recovered number | include/lcns/nester.hpp:180 |
| `strategy.nesting` | `0x378E0` | Run body not transcribed | src/nester.cpp:444 |
| `strategy.flip` | `0x4B870` | mirror-and-compare; literal \"temporary_flipped\" recovered | src/nester.cpp:489 |
| `strategy.filter` | `0xB3AE0` | filter/lower-bound wrapper; body not transcribed | src/nester.cpp:512 |
| `strategy.nofill` | `0x7F240` | fill-forbidding variant; body not transcribed | src/nester.cpp:524 |
| `strategy.tiling` | `0x46940` | pattern-based; body not transcribed | src/nester.cpp:538 |
| `strategy.compact` | `0xB13D0` | compact-then-evaluate; body not transcribed | src/nester.cpp:648 |
| `strategy.limited` | `0x4AB40` | limited wrapper; body not transcribed | src/nester.cpp:659 |
| `strategy.database` | `0x5B250` | tree_db/bucket_manager reuse; not transcribed | src/nester.cpp:698 |
| `strategy.rectangle` | `0x75FB0` | rectangle fast path; parameter keys recovered, body not transcribed | src/nester.cpp:712 |
| `strategy.row` | `0x913E0` | row/pipe packing; the row CORE is recovered (module.row), this Run body is not | src/nester.cpp:794 |
| `strategy.multitorch` | `0x7BCC0` | multitorch packing; body not transcribed | src/nester.cpp:817 |
| `strategy.composite` | `0xA3B780` | runs sub-nesters and keeps the best; shell only | src/nester.cpp:830 |
| `strategy.pack_best` | `0x15E410` | best-of-children; body not transcribed | src/nester.cpp:848 |
| `strategy.pack_knapsack` | `0x15DD70 -> 0x15D1F0` | knapsack selection; not transcribed | src/nester.cpp:863 |
| `strategy.pack_recursive` | `0x165680 -> 0x164FE0` | recursive packing; not transcribed | src/nester.cpp:868 |
| `module.tiling` | `Tiling::BoxMultiTiler etc.` | class names and parameter keys are recovered; the pattern generation here is our own | src/tiling.cpp:8 |
| `tiling.eval.density` | `Tiling::DensityEvaluator` | scoring formula NOT recovered | src/tiling.cpp:131 |
| `tiling.eval.unlimited_density` | `-` | scoring formula NOT recovered | src/tiling.cpp:136 |
| `tiling.eval.unlimited_x_density` | `-` | scoring formula NOT recovered | src/tiling.cpp:150 |
| `tiling.eval.quantity` | `-` | scoring formula NOT recovered | src/tiling.cpp:162 |
| `tiling.eval.reusable` | `-` | scoring formula NOT recovered (weight 0.25 here is ours) | src/tiling.cpp:168 |
| `tiling.eval.oblique` | `-` | scoring formula NOT recovered | src/tiling.cpp:178 |
| `tiling.eval.multitorch` | `-` | scoring formula NOT recovered | src/tiling.cpp:188 |
| `lp.simplex_fallback` | `not in the binary (lcns only)` | the zero dependency Simplex stays as a fallback for builds configured without the COIN-OR archives (-DLCNS_WITH_CLP=OFF, or archives absent). It is NOT what the original runs, so any build using it must be described as using a substitute backend | src/lp.cpp:272 |

## NotReversed（**尚未逆向**）

| id | DLL 地址 | 说明 | 标记位置 |
|---|---|---|---|
| `geom.exact_records` | `40 B / 64 B records` | the exact record layouts emitted by 0x595A80 (40 B directed edge) and 0x596000 (64 B Edge) are described but not constructed here | src/boolean.cpp:502 |
| `geom.detect_overlap` | `0x99EAC0` | zero callers in the whole image (dead assertion-message builder); nothing is reconstructed for it beyond knowing it is unreachable | src/boolean.cpp:481 |
| `model.item_unknown_fields` | `Item+0x20..+0x50` | the Item layout is known at +0x00/+0x08/+0x20/+0x58/+0x70/+0x88 but the fields between +0x20 and +0x50 have no per-field producer/consumer pairing yet | src/model.cpp:71 |
| `row.135040` | `0x135040` | the element SLOT producer: (out,src) -> a present flag plus four doubles; called twice by 0x136350 (the stores at 0x1364B4.. put those doubles into +0x50..+0x68 and +0x78..+0x90). Constants 0.005 @0x9BCEE8 and 1e-06 @0x9BCEE0 recovered, wiring verified -- the BODY is NOT transcribed | include/lcns/row.hpp:741 |
| `row.135780` | `0x135780` | the element VECTOR producer: (out,src) -> std::vector, move-assigned into +0xa8 and +0xc0 (the old pointer goes through operator delete 0x9984B0); emits 32 B two-point records and calls the row helpers 0x134890/0x134C10/0x8C5D40. Wiring verified -- the BODY is NOT transcribed | include/lcns/row.hpp:765 |
| `engine.advanced_strategist` | `0x2DF60` | the DISPATCHER and the 40 B descriptor layout are fully decoded, and 0x2D330's default schedule (8 mode-1 steps differing in the six enable flags, gated by the options object) is tabulated. NOT transcribed: StrategyAdder::Add 0x2C4D0 (the mode/flags -> Nester table) and the gate bodies 0x2DA00/0x2DA20/0x2DA32/0x2DAC1/0x2DC60/0x2D7E1/0x2D650 | src/engine.cpp:28 |
| `engine.beam_tree` | `0x22CCA0 / 0x1C1650 / 0x974F0` | tree_db preparation and node scoring (leaf value at +0x48, internal at +0x50) are located; the beam tree is not reconstructed here | src/engine.cpp:60 |
| `lp.column_generation_unproven` | `-` | whether the original's pricing layer forms a column generation loop is NOT established | src/lp.cpp:590 |
| `cloud.payload_schema` | `-` | the exact JSON payload exchanged with cns1/cns2.optalog.com is NOT recovered | src/cloud.cpp:107 |
| `licensing.sentinel_native` | `LoadLibraryA` | the Sentinel HASP / Admin API calls are NOT reproduced: the original loads them dynamically | src/licensing.cpp:272 |
| `licensing.vendor_code` | `-` | the vendor code needed for a genuine licence check is deliberately not embedded | src/licensing.cpp:312 |

## NotInBinary（非原库）

| id | DLL 地址 | 说明 | 标记位置 |
|---|---|---|---|
| `lp.column_generation` | `-` | lp_column_generation.* is our own extension (file header says NOT PART OF THE BINARY) and lp.hpp does not include it | src/lp_column_generation.cpp:9 |
