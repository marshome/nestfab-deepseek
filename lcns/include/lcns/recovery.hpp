// lcns/recovery.hpp -- machine readable inventory of what IS and IS NOT recovered.
//                      逆向状态登记表：哪些已恢复、哪些没有。
//
// Why this exists / 为什么需要它
// -----------------------------
// The reconstruction mixes five very different kinds of code, and reading the source alone does
// not tell them apart (中文权威词表见下方 "marking macros / 标记宏" 一节):
//
//   Recovered    已恢复       instruction-level faithful: every constant and field offset cites an
//                            RVA that is checked by tests/test_recovered.cpp and re/g_acceptance.py
//   Structural   结构已恢复   the STRUCTURE (classes, call graph, algorithm skeleton, key constants)
//                            was recovered, but the body here is a re-implementation of it
//   Substituted  替代实现     the original uses something we cannot use in this environment, or a
//                            heuristic whose constants were NOT recovered -> our algorithm, not the DLL's
//   NotReversed  尚未逆向     the feature demonstrably exists in liblcns.dll but has NOT been reverse
//                            engineered; the code here is a stub, an empty shell, or simply absent
//   NotInBinary  非原库       our own extension; explicitly NOT part of the DLL
//
// How to mark code / 怎么打标记
// -----------------------------
// Put one of the macros below on its own line, e.g.
//
//     LCNS_SUBSTITUTED(strategy.tiling)   // before TilingNester::run
//
// They expand to a trivially true static_assert (zero cost) whose message carries the Chinese
// meaning, so `grep -rn "尚未逆向" src include` finds every un-reversed site directly.
//
// tools/check_recovery.py enforces the invariant that the set of ids marked in the code is
// EXACTLY the set of ids registered in kGaps below, and that every non-Recovered id is also
// mentioned in re/ (so a gap can never exist only in the code, or only in the docs).
// docs/RECOVERY_STATUS.md is generated from this table.
#pragma once

#include <cstddef>

// --- marking macros / 标记宏 -----------------------------------------------------------------
// 五个宏的中文含义（这就是本工程的"诚实性词表"，每条代码标记都必须用其中之一）：
//
//   LCNS_RECOVERED(id)      【已恢复】
//       逐指令忠实：每一个常量、字段偏移、算法细节都能追到二进制里的 RVA，
//       并由 tests/test_recovered.cpp 与 re/g_acceptance.py 机械核对。
//
//   LCNS_STRUCTURAL(id)     【结构已恢复】
//       类、调用图、算法骨架与关键常量都逆出来了，但这里的实现是**重写**，不是逐指令转写。
//       注意：这一档**不算"没逆向"**，只是保真度低于"已恢复"。
//
//   LCNS_SUBSTITUTED(id)    【替代实现】
//       原库用的东西在本环境不可用、或启发式的常数没有逆出来，因此此处跑的是**我们写的**替代算法，
//       行为不是原库的。当前最大的一块欠账就在这里（12 个策略的 Run 体、主放置器、tiling 评分公式）。
//
//   LCNS_NOT_REVERSED(id)   【尚未逆向】★ 严格意义上的"未逆向"只有这一个宏
//       这个功能在二进制里**确实存在**，但我们**没有译出来**：此处要么是壳、要么缺失。
//       凡声明为此类的，都在 kGaps 里给了地址或写明"-"以及可复核的原因。
//
//   LCNS_NOT_IN_BINARY(id)  【非原库】
//       本工程自己的扩展，不属于逆向缺口（例如自研的列生成机具、Simplex 兜底）。
//
// 实现：都展开为恒真的 static_assert —— 零开销；在文件作用域、类体内、函数体内都合法
// （展开为空语句会在类体内触发 -Wpedantic）。id 会被字符串化，所以标记既能在 grep 里枚举，
// 也会出现在编译器诊断里，连中文含义一起：
//     grep -rn "尚未逆向" src include        # 直接按中文找到所有未逆向的标记
//     grep -rn "LCNS_NOT_REVERSED" src include
#define LCNS_RECOVERED(id) static_assert(true, "已恢复 / recovered: " #id)
#define LCNS_STRUCTURAL(id) static_assert(true, "结构已恢复 / structural: " #id)
#define LCNS_SUBSTITUTED(id) static_assert(true, "替代实现 / substituted: " #id)
#define LCNS_NOT_REVERSED(id) static_assert(true, "尚未逆向 / NOT REVERSED: " #id)
#define LCNS_NOT_IN_BINARY(id) static_assert(true, "非原库 / not in binary: " #id)

namespace lcns {
namespace recovery {

// 状态枚举：与上面五个宏一一对应
enum class Status {
    Recovered = 0,     // 已恢复     —— 逐指令忠实
    Structural = 1,    // 结构已恢复 —— 骨架已逆、实现为重写
    Substituted = 2,   // 替代实现   —— 跑的不是原库算法
    NotReversed = 3,   // 尚未逆向   —— 二进制里有，我们没译出来
    NotInBinary = 4,   // 非原库     —— 本工程自己的扩展
};

// 英文标识（供脚本/生成物使用）
inline const char* toString(Status s) {
    switch (s) {
        case Status::Recovered: return "recovered";
        case Status::Structural: return "structural";
        case Status::Substituted: return "substituted";
        case Status::NotReversed: return "not-reversed";
        case Status::NotInBinary: return "not-in-binary";
    }
    return "?";
}

// 中文含义（供人读；docs/RECOVERY_STATUS.md 与 tools/check_recovery.py 的输出同源）
inline const char* toChinese(Status s) {
    switch (s) {
        case Status::Recovered: return "已恢复";
        case Status::Structural: return "结构已恢复";
        case Status::Substituted: return "替代实现";
        case Status::NotReversed: return "尚未逆向";
        case Status::NotInBinary: return "非原库";
    }
    return "?";
}

// The marker that tools/check_recovery.py writes into the generated table.
inline const char* marker(Status s) {
    switch (s) {
        case Status::Recovered: return "LCNS_RECOVERED";
        case Status::Structural: return "LCNS_STRUCTURAL";
        case Status::Substituted: return "LCNS_SUBSTITUTED";
        case Status::NotReversed: return "LCNS_NOT_REVERSED";
        case Status::NotInBinary: return "LCNS_NOT_IN_BINARY";
    }
    return "?";
}

// id | status | DLL address(es) | note
// The `id` is the contract: it appears both here and as a macro call at the marked site.
struct Gap {
    const char* id;
    Status status;
    const char* address;
    const char* note;
};

inline constexpr Gap kGaps[] = {
    // ---------------------------------------------------------------- TU dossiers (goal round 1+)
    {"tu.svg_io", Status::Structural, "0x7CCDF0 writer; exports 326/328 (0x9550/0x9790)",
     "the DOCUMENT SCHEMA is recovered and implemented in lcns::toSvg: px+viewBox header with "
     "version/xmlns:xlink, <defs><pattern id=diagonalHatch0 patternUnits=userSpaceOnUse>, the outer "
     "<g transform=scale(1,-1)>, per-item translate groups, fill-rule=evenodd paths, the mark "
     "circle r=0.5% in stroke:rgb(192,0,0), and the style fragments of 0x5DAEB0/0x5DDDD0/0x5DC9D0/"
     "0x5DE320/0x5DCE70/0x5D9BF0/0x516380. NOT reversed yet: the remaining ~169 KB of the TU (the "
     "<use>/<defs> geometry variant of export 328, the HTML report side at 0x5100D0/0x5190B0, and "
     "the part-statistics lines multiplicity/height/fill-ratio)"},
    {"module.api", Status::Recovered, "168 exports",
     "export table (ordinal only, NumberOfNames = 0) recovered from the PE export directory"},
    {"api.ordinal_loader", Status::Recovered, "0x0",
     "ordinal -> function mapping and the 162 recovered names (REPORT section 4)"},

    // ---------------------------------------------------------------- geometry kernel
    {"module.geom", Status::Structural, "..\\exact\\* + ..\\geom\\*",
     "fixed-point scale 1e10 (0x9AD708) and the 128-bit predicate (0x58E450) are recovered; the "
     "boolean/offset bodies are a re-implementation of the recovered structure"},
    {"geom.orient128", Status::Recovered, "0x58E450",
     "exact orientation predicate; its complete caller set (13) is enumerated in "
     "findings_geometry.md"},
    {"geom.boolean_kernel", Status::Structural, "0x596100 etc.",
     "the convolution core's quadrant classification and event merge are recovered as a structure; "
     "the implementation here is not a transcription"},
    {"geom.exact_records", Status::NotReversed, "40 B / 64 B records",
     "the exact record layouts emitted by 0x595A80 (40 B directed edge) and 0x596000 (64 B Edge) "
     "are described but not constructed here"},
    {"geom.point_in_polygon", Status::Structural, "inlined; 0x1C1A60",
     "the DLL has no standalone containment routine: the test is INLINED at its assertion sites; "
     "the recovered predicate (+0x60/+0x68 with epsilon 0.001 @0x9BFD30) is reproduced here"},
    {"geom.offset", Status::Structural, "0x58A7E0 / 0x12C60",
     "N = floor(dist/step + 0.5) incremental offset and outer +gap / inner -gap are recovered; the "
     "body is a re-implementation"},
    {"geom.detect_overlap", Status::NotReversed, "0x99EAC0",
     "zero callers in the whole image (dead assertion-message builder); nothing is reconstructed "
     "for it beyond knowing it is unreachable"},

    // ---------------------------------------------------------------- nfp / model
    {"module.nfp", Status::Structural, "0x8AC0 / 0x665BF0 / 0x687080",
     "cache thresholds (25000 @0x61A8, 19999999 @0x1312CFF) are recovered constants; the map "
     "machinery here is a re-implementation"},
    {"module.model", Status::Recovered, "-",
     "Part/Sheet/Order/Nesting/Solution field order and the Set*/Add* landing offsets are "
     "recovered from the setters and CreateProblem 0x1EE50 (REPORT section 7.4)"},
    {"model.item_unknown_fields", Status::NotReversed, "Item+0x20..+0x50",
     "the Item layout is known at +0x00/+0x08/+0x20/+0x58/+0x70/+0x88 but the fields between "
     "+0x20 and +0x50 have no per-field producer/consumer pairing yet"},

    // ---------------------------------------------------------------- row (the closed path)
    {"module.row", Status::Recovered, "0x134470 0x133DE0 0x136350 0x13A360",
     "the per-part path was translated instruction by instruction; the 216 B element layout is "
     "locked by 15 static_asserts in include/lcns/row.hpp"},
    {"row.135040", Status::NotReversed, "0x135040",
     "the element SLOT producer: (out,src) -> a present flag plus four doubles; called twice by "
     "0x136350 (the stores at 0x1364B4.. put those doubles into +0x50..+0x68 and +0x78..+0x90). "
     "Constants 0.005 @0x9BCEE8 and 1e-06 @0x9BCEE0 recovered, wiring verified -- the BODY is NOT "
     "transcribed"},
    {"row.135780", Status::NotReversed, "0x135780",
     "the element VECTOR producer: (out,src) -> std::vector, move-assigned into +0xa8 and +0xc0 "
     "(the old pointer goes through operator delete 0x9984B0); emits 32 B two-point records and "
     "calls the row helpers 0x134890/0x134C10/0x8C5D40. Wiring verified -- the BODY is NOT transcribed"},
    {"row.finalize_passes", Status::Structural, "0x1B33B0 / 0x40720 / 0x1E1BF0",
     "the recovered order (postop -> renest in holes -> packed bottom left) is honoured; each pass "
     "is a re-implementation"},

    // ---------------------------------------------------------------- search / strategies
    {"module.nester", Status::Substituted, "12 strategies",
     "each strategy's identity (vtable address point, Run size, key literals) is recovered, but "
     "EVERY Run body here is our own placement search: the original bodies are not transcribed"},
    {"search.nest_all_parts_aux", Status::NotReversed, "0x6D470 (11478 B, rectangle_nester.cpp)",
     "the rectangle strategy core placement routine, identified by its own inlined strings: NestAllPartsAux, the TU ..\\multi\\rectangle_nester.cpp, and the assertions sheet->is_rectangular() and availables.size() == nb_parts (rectangular sheets only, and the available-parts array must cover every part). Its constants include 0.99 -- the SAME area slack as 0x73280 -- plus 0.1, 1 and 0.5 four times. It calls the other two large kernels: 0x73280 (11567 B, reads Pb[+0xc8] and the option accessors) and 0x70150 (8524 B, with 0.5/0.25/0.001, i.e. step halving with a 0.001 stop). So the three giants are the rectangle kernel layer, not unknown code. NOT transcribed: the bodies themselves"},
    {"search.pack_all", Status::Substituted, "0x378E0 (NestingNester::Run, 14374 B)",
     "packAll is a bottom-left/beam placement search we wrote; the original main packer was not "
     "transcribed"},
    {"search.beam_width", Status::Substituted, "option beam_width (reader 0x4EECB)",
     "BeamParams::width. The MECHANISM is recovered: the binary holds no constant at all, it looks "
     "the value up in the option table under beam_width / beam_advanced_width (reader 0x4F342) / "
     "beam_expert_width (reader 0x4F365), and reports it at 0x655DC6. The default value here is "
     "therefore ours (a tunable), not a recovered number"},
    {"strategy.nesting", Status::Substituted, "0x378E0", "Run body not transcribed. idENDTIFIED FURTHER in round 27: its own inlined strings give the TU (..\\multi\\nesting_nester.cpp), the name Run, and TWO assertions -- deg_steps.size() == try_parts_ratio.size() (two parallel rotation arrays) and parameters().nesting_pow_boost >= 1.0 (the parameter nesting_pow_boost has a hard lower bound of 1.0) -- plus a degree schedule read from its constants (5, 15, 30) with weights 0.33/0.2/0.7/0.015. 75 callees, of which 0x344d0 (6748 B) and 0x35f30 (6436 B) are the largest. This is the routine whose substitute causes the density gap."},
    {"strategy.flip", Status::Substituted, "0x4B870", "mirror-and-compare; literal \"temporary_flipped\" recovered"},
    {"strategy.filter", Status::Substituted, "0xB3AE0", "filter/lower-bound wrapper; body not transcribed"},
    {"strategy.nofill", Status::Substituted, "0x7F240", "fill-forbidding variant; body not transcribed"},
    {"strategy.tiling", Status::Substituted, "0x46940", "pattern-based; body not transcribed. Round 27: identified by its strings as Tiling/Run with the TU and the pattern catalogue in tu.packer_cache; 16,258 bytes / 3,115 instructions / 72 callees, largest 0x693950 (4157 B) and 0x7d12a0 (3762 B); constants 1.0 and 1.5"},
    {"strategy.compact", Status::Substituted, "0xB13D0", "compact-then-evaluate; body not transcribed"},
    {"strategy.limited", Status::Substituted, "0x4AB40", "limited wrapper; body not transcribed"},
    {"strategy.database", Status::Substituted, "0x5B250", "tree_db/bucket_manager reuse; not transcribed"},
    {"strategy.rectangle", Status::Substituted, "0x75FB0", "rectangle fast path; parameter keys recovered, body not transcribed"},
    {"strategy.row", Status::Substituted, "0x913E0", "row/pipe packing; the row CORE is recovered (module.row), this Run body is not"},
    {"strategy.multitorch", Status::Substituted, "0x7BCC0", "multitorch packing; body not transcribed"},
    {"strategy.composite", Status::Substituted, "0xA3B780", "runs sub-nesters and keeps the best; shell only"},
    {"strategy.pack_best", Status::Substituted, "0x15E410", "best-of-children; body not transcribed"},
    {"strategy.pack_knapsack", Status::Substituted, "0x15DD70 -> 0x15D1F0", "knapsack selection; not transcribed"},
    {"strategy.pack_recursive", Status::Substituted, "0x165680 -> 0x164FE0", "recursive packing; not transcribed"},

    // ---------------------------------------------------------------- engine / supervisor
    {"tu.bucket_manager", Status::Structural, "0x215720 hub, 0x20FE90/0x212D30 InsertAllNext",
     "the beam-tree/bucket kernel TU is identified: 177 functions / 174,273 bytes, its 47 string "
     "vocabulary and its API surface are on record -- InsertAllNext (two template instantiations, "
     "0x20FE90 / 0x212D30), IntroduceNestingNodes 0x20C440, AddNodeClusterChain 0x20C2D0, "
     "CreateNestedChain 0x20C880, check_father 0x20EE50, NestingWindow 0x20CCE0, ComputeNodeIndex "
     "0x81C690 (three instantiations), AddOrReplaceEquiv 0x6C7E80 / 0x23B420, ROOT_collection "
     "0x1C5970, beam_slice_ 0x6548D0, beam_try_ 0x655A30, BestNodes 0x7B4000, GetNestableOffset "
     "0x1A89D0, NG3 0x16E140 -- plus one recovered numeric constant, the surface slack 1.05 in "
     "'eval.m_c >= 0 && eval.m_c <= max_surface * 1.05'. NOT transcribed: the bodies (0x215720 11.9 KB, "
     "the two InsertAllNext instantiations, 0x23B420 16.4 KB) and the four Equiv* comparison rules"},
    {"tu.float_filler", Status::Structural, "0x68F750 RawFillNesting (15812 B)",
     "a TU the earlier notes did not have, identified through 0x68f750, whose own inlined strings are ..\\multi\\float_filler.cpp, RawFillNesting, GetCandidates, RemoveNullPricesParts, the assertion nested_part.part(), the shared multiplicity precondition nesting.multiplicity() == 1u (the same one FillNestingAux asserts in tu.nesting_context) and part_number < m_reduced_problem.GetNumberOfParts() -- so it depends on a REDUCED problem, i.e. the equivalent-problem layer of tu.equivalent. 15,812 bytes / 3,128 instructions / 55 callees, with immediates 16 sixty times and 120 twenty times, so it steps over 16 byte records. It is the leftover-space filler (float filler): it removes parts with null prices, asks for candidates and raw-fills a nesting. NOT transcribed: the body and the reduced-problem construction"},
    {"tu.tiling_nester", Status::Structural, "0x693950 (4157 B), GetPackerParameters",
     "the tiling nester TU, identified through its largest helper 0x693950, whose own inlined strings are ..\\multi\\tiling_nester.cpp, GetPackerParameters and sheet: so the TU exists, it has a GetPackerParameters entry point (the packer parameters the pattern machinery consumes) and it works per sheet. Constants there: 0.5 and 1.0. Related structural fact recorded the same round: 0x344d0, the largest helper under Multi::NestingNester::Run, has no strings and no floating constants but calls ToNesting 0x3dbe0, ComputeGroups 0x40070 and NestedQuantities 0x3bcc0 -- the three nesting-context API functions from tu.nesting_context -- which makes it the glue between a nester and the nesting context. NOT transcribed: both bodies"},
    {"tu.packer", Status::Structural, "0x770D10 Packer::Run, ..\\tiling\\packer.cpp",
     "the tiling packer TU: 381 functions / 397,869 bytes. Its entry point is identified by its own inlined strings -- ..\\tiling\\packer.cpp, Run, and the precondition availables.size() == m_problem.GetNumberOfParts() -- at 0x770d10, 8230 bytes / 1641 instructions, with 65 callees. It consumes what the Compute*Tilings family produces (see tus.packer_cache for the 16 pattern keys) and shares the packer cache thread pool. NOT transcribed: the main loop and how it binds availables to m_problem"},
    {"tu.packer_cache", Status::Structural, "0x765460, 0x769410, 0x763ee0, 0x158810",
     "the tiling pattern computation and cache TU is identified: 276 functions / 278,386 bytes. Its "
     "16 pattern keys are on record (box, box_min_dist, cc_matrix, cc_mono, cc_specific, "
     "composite_bi, composite_box, composite_dual_bi, composite_mono, min_box_bi, mono, oblique_bi, "
     "oblique_pentagon, part, pentagon, windmill -- lcns::tiling::kPatternKeys), as are the four "
     "entry points ComputeMonoTilings 0x158810, ComputeMinBoxBiTilings / ComputePartTilings / "
     "OppositePattern 0x765460, ComputeCommonCutMonoTilings 0x769410, the getters GetPart 0x768b80 / "
     "0x76a010, GetCommonCutPart 0x764a80, SetPartAuthorizations 0xc1a0, the two per-part arrays "
     "m_tiling_parts / m_common_cut_tiling_parts, the evaluator invariant "
     "'!parameters.basic_evaluators && !parameters.quantity_evaluators', and a thread pool logging "
     "'Packer Cache max threads: ' / 'Thread <'. Cross confirmation: '!shear' appears here, "
     "independently of the shear/tooling route found in 0x2CE00. NOT transcribed: the pattern "
     "generation rules themselves, the cache key/eviction policy and the thread pool merge"},
    {"tu.nesting_context", Status::Structural, "0x41920 FillNestingAux, 0x69AA40 mapping, 0x40070 ComputeGroups",
     "the nesting context (the bridge between model and engine) is identified: 135 DIRECT functions "
     "/ 114,670 bytes. API surface on record: ComputeRealNestingWindow 0x3b2f0, GetTypicalLength "
     "0x3b5f0, NestedQuantities 0x3bcc0, SetCommonCutParameters 0x3c3f0, ComputeSheetLayers 0x3c9e0, "
     "ToNesting 0x3dbe0, GetNestingPart 0x3f070, SetMultiTorchParameters 0x3e740, ComputeGroups / "
     "FromNesting 0x40070, RenestInHoles 0x40720, FillNestingAux 0x41920, FillNesting 0x434d0, "
     "GetCluster 0x69a720, NestingPartModuleMapping 0x69aa40, GetStructureModule 0x7d3e50, "
     "IsCluster 0x7d4050. Its assertion texts give hard facts: clusters live at the TAIL of m_parts "
     "(index >= m_parts.size() - m_clusters.size()), the engine does NOT support a part gap "
     "(problem.part_gap() == 0.0), FillNestingAux only handles unit multiplicity, ComputeGroups "
     "keeps matrix_indices and group_indices the same length, boxes are non negative to 1e-6 and the "
     "first result point must sit at the origin under Utils::eps_equals. Option keys here: biggest, "
     "packer_cache, sheet, y_valid, _mod. NOT transcribed: the 12.8 KB checker 0x193420, the "
     "FillNesting/ComputeGroups bodies, the module authorization logic and the cluster construction"},
    {"tu.equivalent", Status::NotReversed, "0x4BDB70 (11150 B), 0x4BC9E0, 0x4BB040, 0x75BCC0",
     "the equivalent-problem reduction TU (..\\verify\\equivalent.cpp): 190 functions / 163,972 "
     "bytes, of which the API surface and the invariants ARE recovered -- EquivalentProblemRaw / "
     "AddEquivalentPart / IsTooBigGeometry 0x4bdb70, EquivalentSmallerDefects 0x4bc9e0, "
     "GetOriginalNesting 0x4bb040, EquivalentNestingOrigin 0x4b9fa0, "
     "EquivalentUsedSurfaceEvaluation 0x4ba110, the EquivalentEngine vtable implementation 0x75bcc0, "
     "CNS_AddDefectFromNestedPart 0x12f40 -- and the assertions give hard facts: defect_reduction > "
     "0.0, max_price_per_area != 0.0, extra_equivalent_quantity >= 0, "
     "modules_geometries.size() == nb_modules, a cache is consulted (it != cache.end()), "
     "GetOriginalNesting requires multiplicity == 1, and the original itself refuses the grain mode "
     "('internal error mode not yet supported with grain'). NOT reversed: lcns has NO equivalent "
     "problem reduction at all, and the defect-reduction and used-surface formulas are unread"},
    {"tu.border_property", Status::Structural, "0x1EE50 (15305 B), 0x1C980, 0x22E40, 0x668F20",
     "the border/structure TU cluster is identified: 196 functions / 132,394 bytes spanning THREE "
     "source files -- ../structure/border_property.hpp, internal.cpp and cns_no_fit.cpp. API on "
     "record: CreateProblem / ComputeSheetGeometryRowMode / GetCommonCutProperties / "
     "GetMultitorchProperties / GetLayerLeatherPart / GetLayerLeatherSheet / "
     "GetLayerRestrictedZonePart / GetLayerRestrictedZoneSheet at 0x1ee50 and 0x1c980, ArcToPoints "
     "and the element check at 0x22e40, ComputeNoHoleRings 0x1e900, GetLeatherLayer and IsLeather "
     "at 0x7bc180, CNS_NoFitContext 0x668f20 and DeleteNoFitContext 0x9cc0. Hard facts from the "
     "assertions: TWO quality domains in one model, 'quality >= 0 && quality < 100' for parts and "
     "'quality >= 0 && quality < 9' for leather layers (kQualityLevelsPart / "
     "kQualityLevelsLeatherLayer); external_rings.size() == 1u and poly.inners().empty() for the "
     "ring computation; two option maps named all_settings and boost keyed by "
     "common_cut_safety_preference and multitorch_cutting_preference; and cns_no_fit.cpp asserts "
     "that its equivalent problem has exactly the order's part and sheet counts, tying this TU to "
     "tu.equivalent. DOCUMENTED DIVERGENCE: lcns models leather as one bool plus Sheet::"
     "restrictedZones, while the original has layers with a per-layer quality index. NOT "
     "transcribed: the 15.3 KB CreateProblem body, the leather layer structure and the quality "
     "semantics"},
    {"module.engine", Status::Structural, "0x827F0 / 0x2DF60 / 0x2CCF0",
     "the supervisor/cascade structure and the cancel gate (elapsed / Problem[+0x408] > 1.0) are "
     "recovered; the per-strategy budget bookkeeping here is a re-implementation"},
    {"engine.error_reporter", Status::Substituted, "0x60A620 (2620 B, 680 callers)",
     "the shared error/assertion reporter, identified by its own strings: INTERNAL ERROR please contact support, : error , and (assertion failed in . With 680 callers it is among the hottest functions in the binary, and those callers are exactly the original precondition check sites (the 531 B validation helper 0xB44D0 builds its message through it). Knowing this removes most of the noise from the strategy Run bodies: a call to 0x60a620 or 0xb44d0 means precondition rejected, not an algorithm step. Substituted, not Recovered, because lcns does NOT reproduce this reporter: it throws exceptions instead, so the mechanism differs even though the identification is solid. Deliberately still unnamed: 0x62F280 (171 B, 5209 callers, immediate 1672)"},
    {"engine.strategy_methods", Status::Recovered, "vtable method tables, re/vtables.json",
     "every strategy class's METHOD TABLE is recovered data (the vtable order), so each method has a definite identity: slot k of class X, with its size. This turns the biggest behavioural debt -- the Run bodies -- into an exact work list, and it shows the layout: Multi::*Nester are 6 slots with #0/#1 tiny constructors or probes, #2 a 4-31 B identity accessor, #3/#4 parameter accessors, and #5 = Run, the largest method in every one of them (TilingNester #5 0x46940 (16258 B); NestingNester #5 0x378e0 (14374 B); RowNester #5 0x913e0 (12380 B); MultiTorchNester #5 0x7bcc0 (12232 B); CompactNester #5 0xb13d0 (9393 B); NoFillNester #5 0x7f240 (8440 B); the whole set is 11 classes / 90233 bytes, tabulated in re/STRATEGY_METHODS.md). Pack::*Nester are 3 slots with Run at #2. The *SheetSelector family is 4 slots with the choice logic at #2, and it includes Multi::AllSheetSelector 0x7d2500, which the earlier notes did not have -- they listed only Largest/Random/NoMix. All of these Run bodies are still Substituted (our own search runs instead); what is recovered here is their identity and exact size"},
    {"engine.strategy_adder", Status::Recovered, "0x2C4D0 (Multi::StrategyAdder::Add, 2072 B)",
     "the mode -> nester table and the flag driven chain, read off the dispatch AND off what each "
     "branch allocates (operator new 0x998500, size in ecx) and constructs (named through "
     "re/vtables.json): mode 0 TilingNester (0x20), 1 NestingNester (0xA40), 2 RectangleNester "
     "(0x20), 3/4 RowNester with the pipe flag false/true (0x20), >= 5 asserts; the flags append "
     "CompactNester (0x9F8) then FilterNester (0x9E8) at +0x05, FlipNester (0x28) at +0x04, "
     "MultiTorchNester (0x28) at +0x0C (the count is the torch count), LimitedNester (0x48) at "
     "+0x18/+0x1C, NoFillNester (0x60) at +0x20 == 1.0 with Pb[+0x120] > 1; and the sheet selector "
     "family Largest/Random/NoMixSheetSelector (0xB0000/0xB0040/0xAFD60) is documented for the "
     "first time here. lcns::makeStrategy/makeDefaultStrategies follow this table; test_nester and "
     "test_recovered assert it (the earlier invented modes 5..12 are gone)"},
    {"engine.mode2_shear_route", Status::Structural, "0x2CE00 (1055 B)",
     "mode 2 of the dispatcher 0x2DF60 is the SHEAR/TOOLING route: it reads Pb[+0xC8] (via the "
     "address accessor 0x4FC2C0), then Pb[+0xC9] -- the tooling switch -- and a bool from "
     "0x5223A0, and it carries an inline built assertion '!is_tooling && \"Normal shear is "
     "incompatible with ... contact ...\"' plus a string 'AddShear' and the TU ..\\multi\\... . The "
     "route, its switches and that message are recovered; the three branch bodies themselves are "
     "NOT transcribed. Also from this round: 0x2D650 is the function EPILOGUE of 0x2D330, not a "
     "gate, and the four extra schedule routes are mode 1 + the Flip flag (0x2DA32), mode 0 via "
     "0x2BE50 + cascade (0x2DAC1), mode 2 (0x2DC60) and the 0x2D7E1 branch"},
    {"engine.advanced_strategist", Status::NotReversed, "0x2DF60",
     "the DISPATCHER and the 40 B descriptor layout are fully decoded, and 0x2D330's default "
     "schedule (8 mode-1 steps differing in the six enable flags, gated by the options object) is "
     "tabulated. NOT transcribed: the three branch bodies inside 0x2CE00 and the cpuid probe branch "
     "at 0x2DA00 -- the mode/flags -> nester table is recovered in engine.strategy_adder, and the "
     "mode-2 route plus the four extra schedule routes are in engine.mode2_shear_route"},
    {"engine.beam_tree", Status::NotReversed, "0x22CCA0 / 0x1C1650 / 0x974F0",
     "tree_db preparation and node scoring (leaf value at +0x48, internal at +0x50) are located, "
     "and the TU plus its whole API surface are now on record in tu.bucket_manager; the beam tree "
     "ITSELF is still not reconstructed here"},

    // ---------------------------------------------------------------- tiling patterns
    {"module.tiling", Status::Substituted, "Tiling::BoxMultiTiler etc.",
     "class names and parameter keys are recovered; the pattern generation here is our own"},
    {"tiling.eval.density", Status::Substituted, "Tiling::DensityEvaluator", "scoring formula NOT recovered"},
    {"tiling.eval.unlimited_density", Status::Substituted, "-", "scoring formula NOT recovered"},
    {"tiling.eval.unlimited_x_density", Status::Substituted, "-", "scoring formula NOT recovered"},
    {"tiling.eval.quantity", Status::Substituted, "-", "scoring formula NOT recovered"},
    {"tiling.eval.reusable", Status::Substituted, "-", "scoring formula NOT recovered (weight 0.25 here is ours)"},
    {"tiling.eval.oblique", Status::Substituted, "-", "scoring formula NOT recovered"},
    {"tiling.eval.multitorch", Status::Substituted, "-", "scoring formula NOT recovered"},

    // ---------------------------------------------------------------- lp / pricing
    {"module.lp", Status::Structural, "Lp::LinearProgram / Coin::CoinLP",
     "the CoinLP slot structure and the 3 parallel vector + COO accumulator layout are recovered"},
    {"lp.clp_backend", Status::Recovered, "Coin::CoinLP slots 3/4/5/8; OsiClpSolverInterface",
     "the REAL COIN-OR CoinUtils/Osi/Clp is downloaded (third_party/README.md) and linked: "
     "third_party/CMakeLists.txt builds the trio with the project's own GCC 13.1, and "
     "lcns::lp::ClpLinearProgram drives OsiClpSolverInterface through the recovered contract "
     "(reset/addColumn/addRow/solve/primal/dual) with the recovered storage shape (3 parallel "
     "per-column vectors + a 16 B triplet list sorted column-major, i.e. 0x7CA830). "
     "tests/test_linear_program.cpp cross-checks it against the built-in backend on the recovered "
     "driver buildAndSolveLp (0x7D7200): objective and duals must agree, and each answer must be "
     "feasible and reproduce its own objective. VERSION IS EVIDENCED, not guessed: the dump "
     "contains '@C:\\Users\\renaud\\nest\\external\\clp-1.15.3\\Clp\\src\\ClpSimplexDual.cpp' at "
     "0x9C9E1F and 'Clp-1.15.3\\CoinUtils\\src\\CoinLpIO.cpp' at 0x9D2D30, so Clp is built from the "
     "exact releases/1.15.3 tag (its configure reports CLP_VERSION \"1.15.3\"); CoinUtils/Osi come "
     "from the matching stable/2.10 and stable/0.107 branches, whose exact patch levels are NOT "
     "string proven"},
    {"lp.simplex_fallback", Status::Substituted, "not in the binary (lcns only)",
     "the zero dependency Simplex stays as a fallback for builds configured without the COIN-OR "
     "archives (-DLCNS_WITH_CLP=OFF, or archives absent). It is NOT what the original runs, so any "
     "build using it must be described as using a substitute backend"},
    {"lp.canonicalise", Status::Recovered, "0x7CA830",
     "in-place sort of the +0x90 triplet accumulator into column-major COO order, then 3-space "
     "text rendering"},
    {"lp.pricers", Status::Structural, "0xA3B0C0 / 0xA3B100 / 0xA3B140 / 0xA3B180",
     "the four pricers and their accessors are recovered (Box area 0x7C9D90, Hull +0x48, Alpha "
     "+0x68, weighted mean); the surrounding driver is a re-implementation"},
    {"lp.column_generation_unproven", Status::NotReversed, "-",
     "whether the original's pricing layer forms a column generation loop is NOT established"},
    {"lp.column_generation", Status::NotInBinary, "-",
     "lp_column_generation.* is our own extension (file header says NOT PART OF THE BINARY) and "
     "lp.hpp does not include it"},

    // ---------------------------------------------------------------- io / cloud / licensing
    {"module.io", Status::Structural, "JsonCpp keys @0x9DA300..0x9DB010",
     "the problem/solution JSON keys are recovered from the string table; the parser/writer is "
     "self contained here"},
    {"io.dxf", Status::Structural, "GenerateDxfNesting 0xBF70 -> DrawDxf",
     "R12 DXF with SHEET/PART/HOLES layers is recovered as a structure"},
    {"module.cloud", Status::Structural, "0x26A60 (CloudEngine::Run)",
     "the HTTP shape (/pb/, /sol/, best_sol, the request headers) is recovered from literals"},
    {"cloud.payload_schema", Status::NotReversed, "-",
     "the exact JSON payload exchanged with cns1/cns2.optalog.com is NOT recovered"},
    {"module.licensing", Status::Structural, "0x14620 etc.",
     "PCId/machine binding and the HASP flags are recovered; the Sentinel API itself is loaded at "
     "runtime and is not reconstructed"},
    {"licensing.sentinel_native", Status::NotReversed, "LoadLibraryA",
     "the Sentinel HASP / Admin API calls are NOT reproduced: the original loads them dynamically"},
    {"licensing.vendor_code", Status::NotReversed, "-",
     "the vendor code needed for a genuine licence check is deliberately not embedded"},
};

inline constexpr std::size_t kGapCount = sizeof(kGaps) / sizeof(kGaps[0]);

// Counts per status -- asserted by tests/test_recovered.cpp so the inventory cannot silently shrink.
inline constexpr std::size_t countOf(Status s) {
    std::size_t n = 0;
    for (std::size_t i = 0; i < kGapCount; ++i) {
        if (kGaps[i].status == s) ++n;
    }
    return n;
}

}  // namespace recovery
}  // namespace lcns
