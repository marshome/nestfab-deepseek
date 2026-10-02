// lcns/include/lcns/parameter_report.hpp -- the 107 fields RE 0x4EC00 writes, each under a name the module uses.
//
// NAMED FOR WHAT THE EVIDENCE SUPPORTS, and renamed once already. The first version called this a configuration with "parameters", which
// was an INFERENCE: the names and the offsets are the module's, but the direction is a REPORT. RE 0x4EC00 initialises an object by
// calling RE 0x4E5B0, walks a container reached at [rdx+0x18], and for each element reads a value at [rdi+0x40] and stores it into the
// object under a name. So it records values against the module's labels rather than applying settings.
//
// The offsets and the strings stand as recorded; only the interpretation changed, and this file name says which is which.
//
// GENERATED from re/param_names.json by re/g_gen_config.py. Do not edit by hand; rerun the generator.
//
// RE 0x4EC00 (5633 bytes) fills an object in rsi by asking RE 0x82A3E0 for a parameter BY NAME and storing the value when the lookup
// succeeds. The pattern, verified at one site by hand:
//
//     0x4F496  lea rdx, [rip + 0x960a7d]      ; -> 'nesting_pow_boost'
//     0x4F4A0  call 0x82a3e0                  ; look it up
//     0x4F4A5  test eax, eax / jne <skip>
//     0x4F4A9  movsd qword ptr [rsi + 0x100], xmm6   ; THE FIELD
//
// so every entry below is a name from the module's own strings beside the instruction that writes it. The name is ORACLE grade and the
// offset is INSTRUCTION grade, which is the strongest pair this project's ledger records short of a constructor.
//
// WHAT THE NAMES SAY ABOUT THE DESIGN, which is evidence and not decoration: 33 enable_* switches against 28 nb_* counts means the engine is configured mostly by toggles, and the four
// *_price_frequency parameters plus two *_price_max_random ones describe a weighted search over several strategies.
//
// The offsets run from 0x1C to 0x34F with 20 gaps larger than eight bytes, so the struct has regions between the ones
// this parser touches -- those parameters are set elsewhere, or are not parameters at all.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

/** The offsets RE 0x4EC00 writes, in the module's own parameter vocabulary. */
namespace parameters {

constexpr std::size_t kenable_last_compaction                               = 0x1C;
constexpr std::size_t kenable_last_postop                                   = 0x1D;
constexpr std::size_t knb_iterations_before_postop                          = 0x24;
constexpr std::size_t knb_strips_first                                      = 0x44;
constexpr std::size_t knb_iterations_first                                  = 0x48;
constexpr std::size_t knb_strips_default                                    = 0x4C;
constexpr std::size_t knb_strips_filling_advanced                           = 0x50;
constexpr std::size_t kenable_flip                                          = 0x58;
constexpr std::size_t kenable_tiling                                        = 0x59;
constexpr std::size_t kenable_oblique_tiling                                = 0x5A;
constexpr std::size_t kenable_pentagon_tiling                               = 0x5B;
constexpr std::size_t kenable_oblique_pentagon_tiling                       = 0x5C;
constexpr std::size_t kenable_composite_tiling                              = 0x5D;
constexpr std::size_t kenable_common_cut_tiling                             = 0x5E;
constexpr std::size_t kenable_recursive_tiling                              = 0x5F;
constexpr std::size_t knb_iterations_before_tiling                          = 0x60;
constexpr std::size_t knb_iterations_before_partial_multi_fill_tiling       = 0x78;
constexpr std::size_t kenable_rectangle                                     = 0x80;
constexpr std::size_t kforce_rectangle                                      = 0x81;
constexpr std::size_t ktooling_with_rectangle                               = 0x82;
constexpr std::size_t knb_rectangle_try                                     = 0x84;
constexpr std::size_t knb_iterations_before_rectangle_advance               = 0x88;
constexpr std::size_t knb_iterations_before_rectangle_dual                  = 0x8C;
constexpr std::size_t knb_rectangle_advance_try                             = 0x90;
constexpr std::size_t knb_iterations_before_tiling_evaluated                = 0xC0;
constexpr std::size_t kenable_common_cut_filling                            = 0xD8;
constexpr std::size_t knesting_offset_ratio                                 = 0xE0;
constexpr std::size_t knb_iterations_before_advanced_nesting                = 0xE8;
constexpr std::size_t knb_iterations_before_expert_nesting                  = 0xEC;
constexpr std::size_t knb_iterations_before_small_rotation_nesting          = 0xF0;
constexpr std::size_t kenable_nesting_boost                                 = 0xF4;
constexpr std::size_t knesting_pow_boost                                    = 0x100;
constexpr std::size_t knesting_max_context_size                             = 0x108;
constexpr std::size_t kenable_enlarge_and_postop                            = 0x10D;
constexpr std::size_t kenable_rotate_compact_postop                         = 0x10E;
constexpr std::size_t knb_iterations_before_enlarge                         = 0x110;
constexpr std::size_t knb_iterations_before_enlarge_tiling                  = 0x114;
constexpr std::size_t knb_iterations_before_rotate_compact_postop           = 0x118;
constexpr std::size_t kdefault_enlarge                                      = 0x120;
constexpr std::size_t kenable_beam                                          = 0x138;
constexpr std::size_t kbeam_frequency_ratio                                 = 0x140;
constexpr std::size_t kbeam_flip_frequency_ratio                            = 0x148;
constexpr std::size_t kbeam_width                                           = 0x150;
constexpr std::size_t kbeam_buckets_per_part                                = 0x160;
constexpr std::size_t kenable_filter                                        = 0x168;
constexpr std::size_t knb_iterations_before_beam_advanced                   = 0x180;
constexpr std::size_t kbeam_advanced_width                                  = 0x184;
constexpr std::size_t knb_iterations_before_beam_expert                     = 0x190;
constexpr std::size_t kbeam_expert_width                                    = 0x194;
constexpr std::size_t kbeam_distinct_angle                                  = 0x1A8;
constexpr std::size_t knb_iterations_before_cut_nesting                     = 0x1B0;
constexpr std::size_t kcut_nesting_probabilty                               = 0x1B8;
constexpr std::size_t kenable_database_float_filler                         = 0x1C0;
constexpr std::size_t knb_iterations_before_float_filler                    = 0x1C4;
constexpr std::size_t kenable_best_float_filler                             = 0x1CC;
constexpr std::size_t knb_max_nested_parts_float_filler                     = 0x1DC;
constexpr std::size_t kfloat_filler_reduction_ratio                         = 0x1E0;
constexpr std::size_t kenable_database                                      = 0x1E8;
constexpr std::size_t kper_worker_database                                  = 0x1E9;
constexpr std::size_t kdatabase_relax_every                                 = 0x1EC;
constexpr std::size_t kadaptative_price_max_random                          = 0x200;
constexpr std::size_t kboost_price_max_random                               = 0x208;
constexpr std::size_t kcombined_price_frequency                             = 0x210;
constexpr std::size_t klinear_price_frequency                               = 0x218;
constexpr std::size_t kboost_price_frequency                                = 0x220;
constexpr std::size_t klinear_fill_frequency                                = 0x228;
constexpr std::size_t ksimple_fill_frequency                                = 0x230;
constexpr std::size_t krandom_price_frequency                               = 0x238;
constexpr std::size_t knb_iterations_before_relaxed_mono                    = 0x264;
constexpr std::size_t kmono_relaxed_frequency                               = 0x268;
constexpr std::size_t kmono_relaxed_max_bonus                               = 0x270;
constexpr std::size_t kmax_dual_ratio                                       = 0x288;
constexpr std::size_t kenable_common_cut_nesting                            = 0x298;
constexpr std::size_t kenable_common_cut_relax_objective                    = 0x2A4;
constexpr std::size_t kenable_common_cut_repair                             = 0x2A5;
constexpr std::size_t kmax_cutting_cost_ratio                               = 0x2A8;
constexpr std::size_t kmin_cutting_cost_ratio                               = 0x2B0;
constexpr std::size_t kuse_old_evaluation_ratio                             = 0x2B8;
constexpr std::size_t kenable_multi_sheet                                   = 0x2C0;
constexpr std::size_t kenable_beautifier                                    = 0x2CC;
constexpr std::size_t kenable_beautifier_optimizer                          = 0x2CD;
constexpr std::size_t kenable_beautifier_multiplicity                       = 0x2D8;
constexpr std::size_t kenable_beautifier_intermediate                       = 0x2D9;
constexpr std::size_t knb_iterations_before_intermediate_beautifier         = 0x2DC;
constexpr std::size_t kenable_beautifier_common_cut                         = 0x2E0;
constexpr std::size_t kenable_beautifier_improve_common_cut                 = 0x2E1;
constexpr std::size_t kenable_beautifier_floating                           = 0x2E2;
constexpr std::size_t kenable_beautifier_reorganizer                        = 0x2E3;
constexpr std::size_t knb_iterations_before_beautifier_advanced             = 0x31C;
constexpr std::size_t knb_iterations_before_free_parts                      = 0x320;
constexpr std::size_t ktry_fill_free_parts                                  = 0x324;
constexpr std::size_t kuse_multitorch_tiling                                = 0x330;
constexpr std::size_t kuse_clusters                                         = 0x331;
constexpr std::size_t kforce_nb_max_active_parts                            = 0x334;
constexpr std::size_t kforce_single_orientation_tiling                      = 0x338;
constexpr std::size_t kforce_single_orientation_asit                        = 0x339;
constexpr std::size_t kseed                                                 = 0x33C;
constexpr std::size_t kenable_multi_thread                                  = 0x340;
constexpr std::size_t knb_max_threads                                       = 0x344;
constexpr std::size_t kverbose                                              = 0x348;
constexpr std::size_t klimited_intermediate                                 = 0x349;
constexpr std::size_t kdetect_overlap                                       = 0x34A;
constexpr std::size_t ktrace_nesting                                        = 0x34B;
constexpr std::size_t ktrace_solution                                       = 0x34C;
constexpr std::size_t ktrace_best_solution                                  = 0x34D;
constexpr std::size_t ktrace_dxf                                            = 0x34E;
constexpr std::size_t kstable_results                                       = 0x34F;

/** The count of parameters this parser names, for a test to assert rather than repeat. */
constexpr std::size_t kParameterReportCount = 107;

}  // namespace parameters

/** A record of what each offset IS, for the reconstruction. It is deliberately not a struct with those members laid out: the point is
 *  to carry the module's names and offsets, and a laid-out struct would depend on the compiler's padding to agree with them. */
struct ParameterReportEntry {
    std::size_t offset;
    const char* name;
};

inline const ParameterReportEntry* parameterReport(std::size_t& count) {
    static const ParameterReportEntry table[] = {
        {0x1C, "enable_last_compaction"},
        {0x1D, "enable_last_postop"},
        {0x24, "nb_iterations_before_postop"},
        {0x44, "nb_strips_first"},
        {0x48, "nb_iterations_first"},
        {0x4C, "nb_strips_default"},
        {0x50, "nb_strips_filling_advanced"},
        {0x58, "enable_flip"},
        {0x59, "enable_tiling"},
        {0x5A, "enable_oblique_tiling"},
        {0x5B, "enable_pentagon_tiling"},
        {0x5C, "enable_oblique_pentagon_tiling"},
        {0x5D, "enable_composite_tiling"},
        {0x5E, "enable_common_cut_tiling"},
        {0x5F, "enable_recursive_tiling"},
        {0x60, "nb_iterations_before_tiling"},
        {0x78, "nb_iterations_before_partial_multi_fill_tiling"},
        {0x80, "enable_rectangle"},
        {0x81, "force_rectangle"},
        {0x82, "tooling_with_rectangle"},
        {0x84, "nb_rectangle_try"},
        {0x88, "nb_iterations_before_rectangle_advance"},
        {0x8C, "nb_iterations_before_rectangle_dual"},
        {0x90, "nb_rectangle_advance_try"},
        {0xC0, "nb_iterations_before_tiling_evaluated"},
        {0xD8, "enable_common_cut_filling"},
        {0xE0, "nesting_offset_ratio"},
        {0xE8, "nb_iterations_before_advanced_nesting"},
        {0xEC, "nb_iterations_before_expert_nesting"},
        {0xF0, "nb_iterations_before_small_rotation_nesting"},
        {0xF4, "enable_nesting_boost"},
        {0x100, "nesting_pow_boost"},
        {0x108, "nesting_max_context_size"},
        {0x10D, "enable_enlarge_and_postop"},
        {0x10E, "enable_rotate_compact_postop"},
        {0x110, "nb_iterations_before_enlarge"},
        {0x114, "nb_iterations_before_enlarge_tiling"},
        {0x118, "nb_iterations_before_rotate_compact_postop"},
        {0x120, "default_enlarge"},
        {0x138, "enable_beam"},
        {0x140, "beam_frequency_ratio"},
        {0x148, "beam_flip_frequency_ratio"},
        {0x150, "beam_width"},
        {0x160, "beam_buckets_per_part"},
        {0x168, "enable_filter"},
        {0x180, "nb_iterations_before_beam_advanced"},
        {0x184, "beam_advanced_width"},
        {0x190, "nb_iterations_before_beam_expert"},
        {0x194, "beam_expert_width"},
        {0x1A8, "beam_distinct_angle"},
        {0x1B0, "nb_iterations_before_cut_nesting"},
        {0x1B8, "cut_nesting_probabilty"},
        {0x1C0, "enable_database_float_filler"},
        {0x1C4, "nb_iterations_before_float_filler"},
        {0x1CC, "enable_best_float_filler"},
        {0x1DC, "nb_max_nested_parts_float_filler"},
        {0x1E0, "float_filler_reduction_ratio"},
        {0x1E8, "enable_database"},
        {0x1E9, "per_worker_database"},
        {0x1EC, "database_relax_every"},
        {0x200, "adaptative_price_max_random"},
        {0x208, "boost_price_max_random"},
        {0x210, "combined_price_frequency"},
        {0x218, "linear_price_frequency"},
        {0x220, "boost_price_frequency"},
        {0x228, "linear_fill_frequency"},
        {0x230, "simple_fill_frequency"},
        {0x238, "random_price_frequency"},
        {0x264, "nb_iterations_before_relaxed_mono"},
        {0x268, "mono_relaxed_frequency"},
        {0x270, "mono_relaxed_max_bonus"},
        {0x288, "max_dual_ratio"},
        {0x298, "enable_common_cut_nesting"},
        {0x2A4, "enable_common_cut_relax_objective"},
        {0x2A5, "enable_common_cut_repair"},
        {0x2A8, "max_cutting_cost_ratio"},
        {0x2B0, "min_cutting_cost_ratio"},
        {0x2B8, "use_old_evaluation_ratio"},
        {0x2C0, "enable_multi_sheet"},
        {0x2CC, "enable_beautifier"},
        {0x2CD, "enable_beautifier_optimizer"},
        {0x2D8, "enable_beautifier_multiplicity"},
        {0x2D9, "enable_beautifier_intermediate"},
        {0x2DC, "nb_iterations_before_intermediate_beautifier"},
        {0x2E0, "enable_beautifier_common_cut"},
        {0x2E1, "enable_beautifier_improve_common_cut"},
        {0x2E2, "enable_beautifier_floating"},
        {0x2E3, "enable_beautifier_reorganizer"},
        {0x31C, "nb_iterations_before_beautifier_advanced"},
        {0x320, "nb_iterations_before_free_parts"},
        {0x324, "try_fill_free_parts"},
        {0x330, "use_multitorch_tiling"},
        {0x331, "use_clusters"},
        {0x334, "force_nb_max_active_parts"},
        {0x338, "force_single_orientation_tiling"},
        {0x339, "force_single_orientation_asit"},
        {0x33C, "seed"},
        {0x340, "enable_multi_thread"},
        {0x344, "nb_max_threads"},
        {0x348, "verbose"},
        {0x349, "limited_intermediate"},
        {0x34A, "detect_overlap"},
        {0x34B, "trace_nesting"},
        {0x34C, "trace_solution"},
        {0x34D, "trace_best_solution"},
        {0x34E, "trace_dxf"},
        {0x34F, "stable_results"},
    };
    count = sizeof(table) / sizeof(table[0]);
    return table;
}

static_assert(parameters::kenable_last_compaction == 0x1C, "RE 0x4EC00 stores enable_last_compaction at +0x1C");
static_assert(parameters::kenable_last_postop == 0x1D, "RE 0x4EC00 stores enable_last_postop at +0x1D");
static_assert(parameters::knb_iterations_before_postop == 0x24, "RE 0x4EC00 stores nb_iterations_before_postop at +0x24");
static_assert(parameters::knb_strips_first == 0x44, "RE 0x4EC00 stores nb_strips_first at +0x44");
static_assert(parameters::knb_iterations_first == 0x48, "RE 0x4EC00 stores nb_iterations_first at +0x48");
static_assert(parameters::knb_strips_default == 0x4C, "RE 0x4EC00 stores nb_strips_default at +0x4C");
static_assert(parameters::knb_strips_filling_advanced == 0x50, "RE 0x4EC00 stores nb_strips_filling_advanced at +0x50");
static_assert(parameters::kenable_flip == 0x58, "RE 0x4EC00 stores enable_flip at +0x58");
static_assert(parameters::kenable_tiling == 0x59, "RE 0x4EC00 stores enable_tiling at +0x59");
static_assert(parameters::kenable_oblique_tiling == 0x5A, "RE 0x4EC00 stores enable_oblique_tiling at +0x5A");
static_assert(parameters::kenable_pentagon_tiling == 0x5B, "RE 0x4EC00 stores enable_pentagon_tiling at +0x5B");
static_assert(parameters::kenable_oblique_pentagon_tiling == 0x5C, "RE 0x4EC00 stores enable_oblique_pentagon_tiling at +0x5C");
static_assert(parameters::kenable_composite_tiling == 0x5D, "RE 0x4EC00 stores enable_composite_tiling at +0x5D");
static_assert(parameters::kenable_common_cut_tiling == 0x5E, "RE 0x4EC00 stores enable_common_cut_tiling at +0x5E");
static_assert(parameters::kenable_recursive_tiling == 0x5F, "RE 0x4EC00 stores enable_recursive_tiling at +0x5F");
static_assert(parameters::knb_iterations_before_tiling == 0x60, "RE 0x4EC00 stores nb_iterations_before_tiling at +0x60");
static_assert(parameters::knb_iterations_before_partial_multi_fill_tiling == 0x78, "RE 0x4EC00 stores nb_iterations_before_partial_multi_fill_tiling at +0x78");
static_assert(parameters::kenable_rectangle == 0x80, "RE 0x4EC00 stores enable_rectangle at +0x80");
static_assert(parameters::kforce_rectangle == 0x81, "RE 0x4EC00 stores force_rectangle at +0x81");
static_assert(parameters::ktooling_with_rectangle == 0x82, "RE 0x4EC00 stores tooling_with_rectangle at +0x82");
static_assert(parameters::knb_rectangle_try == 0x84, "RE 0x4EC00 stores nb_rectangle_try at +0x84");
static_assert(parameters::knb_iterations_before_rectangle_advance == 0x88, "RE 0x4EC00 stores nb_iterations_before_rectangle_advance at +0x88");
static_assert(parameters::knb_iterations_before_rectangle_dual == 0x8C, "RE 0x4EC00 stores nb_iterations_before_rectangle_dual at +0x8C");
static_assert(parameters::knb_rectangle_advance_try == 0x90, "RE 0x4EC00 stores nb_rectangle_advance_try at +0x90");
static_assert(parameters::knb_iterations_before_tiling_evaluated == 0xC0, "RE 0x4EC00 stores nb_iterations_before_tiling_evaluated at +0xC0");
static_assert(parameters::kenable_common_cut_filling == 0xD8, "RE 0x4EC00 stores enable_common_cut_filling at +0xD8");
static_assert(parameters::knesting_offset_ratio == 0xE0, "RE 0x4EC00 stores nesting_offset_ratio at +0xE0");
static_assert(parameters::knb_iterations_before_advanced_nesting == 0xE8, "RE 0x4EC00 stores nb_iterations_before_advanced_nesting at +0xE8");
static_assert(parameters::knb_iterations_before_expert_nesting == 0xEC, "RE 0x4EC00 stores nb_iterations_before_expert_nesting at +0xEC");
static_assert(parameters::knb_iterations_before_small_rotation_nesting == 0xF0, "RE 0x4EC00 stores nb_iterations_before_small_rotation_nesting at +0xF0");
static_assert(parameters::kenable_nesting_boost == 0xF4, "RE 0x4EC00 stores enable_nesting_boost at +0xF4");
static_assert(parameters::knesting_pow_boost == 0x100, "RE 0x4EC00 stores nesting_pow_boost at +0x100");
static_assert(parameters::knesting_max_context_size == 0x108, "RE 0x4EC00 stores nesting_max_context_size at +0x108");
static_assert(parameters::kenable_enlarge_and_postop == 0x10D, "RE 0x4EC00 stores enable_enlarge_and_postop at +0x10D");
static_assert(parameters::kenable_rotate_compact_postop == 0x10E, "RE 0x4EC00 stores enable_rotate_compact_postop at +0x10E");
static_assert(parameters::knb_iterations_before_enlarge == 0x110, "RE 0x4EC00 stores nb_iterations_before_enlarge at +0x110");
static_assert(parameters::knb_iterations_before_enlarge_tiling == 0x114, "RE 0x4EC00 stores nb_iterations_before_enlarge_tiling at +0x114");
static_assert(parameters::knb_iterations_before_rotate_compact_postop == 0x118, "RE 0x4EC00 stores nb_iterations_before_rotate_compact_postop at +0x118");
static_assert(parameters::kdefault_enlarge == 0x120, "RE 0x4EC00 stores default_enlarge at +0x120");
static_assert(parameters::kenable_beam == 0x138, "RE 0x4EC00 stores enable_beam at +0x138");
static_assert(parameters::kbeam_frequency_ratio == 0x140, "RE 0x4EC00 stores beam_frequency_ratio at +0x140");
static_assert(parameters::kbeam_flip_frequency_ratio == 0x148, "RE 0x4EC00 stores beam_flip_frequency_ratio at +0x148");
static_assert(parameters::kbeam_width == 0x150, "RE 0x4EC00 stores beam_width at +0x150");
static_assert(parameters::kbeam_buckets_per_part == 0x160, "RE 0x4EC00 stores beam_buckets_per_part at +0x160");
static_assert(parameters::kenable_filter == 0x168, "RE 0x4EC00 stores enable_filter at +0x168");
static_assert(parameters::knb_iterations_before_beam_advanced == 0x180, "RE 0x4EC00 stores nb_iterations_before_beam_advanced at +0x180");
static_assert(parameters::kbeam_advanced_width == 0x184, "RE 0x4EC00 stores beam_advanced_width at +0x184");
static_assert(parameters::knb_iterations_before_beam_expert == 0x190, "RE 0x4EC00 stores nb_iterations_before_beam_expert at +0x190");
static_assert(parameters::kbeam_expert_width == 0x194, "RE 0x4EC00 stores beam_expert_width at +0x194");
static_assert(parameters::kbeam_distinct_angle == 0x1A8, "RE 0x4EC00 stores beam_distinct_angle at +0x1A8");
static_assert(parameters::knb_iterations_before_cut_nesting == 0x1B0, "RE 0x4EC00 stores nb_iterations_before_cut_nesting at +0x1B0");
static_assert(parameters::kcut_nesting_probabilty == 0x1B8, "RE 0x4EC00 stores cut_nesting_probabilty at +0x1B8");
static_assert(parameters::kenable_database_float_filler == 0x1C0, "RE 0x4EC00 stores enable_database_float_filler at +0x1C0");
static_assert(parameters::knb_iterations_before_float_filler == 0x1C4, "RE 0x4EC00 stores nb_iterations_before_float_filler at +0x1C4");
static_assert(parameters::kenable_best_float_filler == 0x1CC, "RE 0x4EC00 stores enable_best_float_filler at +0x1CC");
static_assert(parameters::knb_max_nested_parts_float_filler == 0x1DC, "RE 0x4EC00 stores nb_max_nested_parts_float_filler at +0x1DC");
static_assert(parameters::kfloat_filler_reduction_ratio == 0x1E0, "RE 0x4EC00 stores float_filler_reduction_ratio at +0x1E0");
static_assert(parameters::kenable_database == 0x1E8, "RE 0x4EC00 stores enable_database at +0x1E8");
static_assert(parameters::kper_worker_database == 0x1E9, "RE 0x4EC00 stores per_worker_database at +0x1E9");
static_assert(parameters::kdatabase_relax_every == 0x1EC, "RE 0x4EC00 stores database_relax_every at +0x1EC");
static_assert(parameters::kadaptative_price_max_random == 0x200, "RE 0x4EC00 stores adaptative_price_max_random at +0x200");
static_assert(parameters::kboost_price_max_random == 0x208, "RE 0x4EC00 stores boost_price_max_random at +0x208");
static_assert(parameters::kcombined_price_frequency == 0x210, "RE 0x4EC00 stores combined_price_frequency at +0x210");
static_assert(parameters::klinear_price_frequency == 0x218, "RE 0x4EC00 stores linear_price_frequency at +0x218");
static_assert(parameters::kboost_price_frequency == 0x220, "RE 0x4EC00 stores boost_price_frequency at +0x220");
static_assert(parameters::klinear_fill_frequency == 0x228, "RE 0x4EC00 stores linear_fill_frequency at +0x228");
static_assert(parameters::ksimple_fill_frequency == 0x230, "RE 0x4EC00 stores simple_fill_frequency at +0x230");
static_assert(parameters::krandom_price_frequency == 0x238, "RE 0x4EC00 stores random_price_frequency at +0x238");
static_assert(parameters::knb_iterations_before_relaxed_mono == 0x264, "RE 0x4EC00 stores nb_iterations_before_relaxed_mono at +0x264");
static_assert(parameters::kmono_relaxed_frequency == 0x268, "RE 0x4EC00 stores mono_relaxed_frequency at +0x268");
static_assert(parameters::kmono_relaxed_max_bonus == 0x270, "RE 0x4EC00 stores mono_relaxed_max_bonus at +0x270");
static_assert(parameters::kmax_dual_ratio == 0x288, "RE 0x4EC00 stores max_dual_ratio at +0x288");
static_assert(parameters::kenable_common_cut_nesting == 0x298, "RE 0x4EC00 stores enable_common_cut_nesting at +0x298");
static_assert(parameters::kenable_common_cut_relax_objective == 0x2A4, "RE 0x4EC00 stores enable_common_cut_relax_objective at +0x2A4");
static_assert(parameters::kenable_common_cut_repair == 0x2A5, "RE 0x4EC00 stores enable_common_cut_repair at +0x2A5");
static_assert(parameters::kmax_cutting_cost_ratio == 0x2A8, "RE 0x4EC00 stores max_cutting_cost_ratio at +0x2A8");
static_assert(parameters::kmin_cutting_cost_ratio == 0x2B0, "RE 0x4EC00 stores min_cutting_cost_ratio at +0x2B0");
static_assert(parameters::kuse_old_evaluation_ratio == 0x2B8, "RE 0x4EC00 stores use_old_evaluation_ratio at +0x2B8");
static_assert(parameters::kenable_multi_sheet == 0x2C0, "RE 0x4EC00 stores enable_multi_sheet at +0x2C0");
static_assert(parameters::kenable_beautifier == 0x2CC, "RE 0x4EC00 stores enable_beautifier at +0x2CC");
static_assert(parameters::kenable_beautifier_optimizer == 0x2CD, "RE 0x4EC00 stores enable_beautifier_optimizer at +0x2CD");
static_assert(parameters::kenable_beautifier_multiplicity == 0x2D8, "RE 0x4EC00 stores enable_beautifier_multiplicity at +0x2D8");
static_assert(parameters::kenable_beautifier_intermediate == 0x2D9, "RE 0x4EC00 stores enable_beautifier_intermediate at +0x2D9");
static_assert(parameters::knb_iterations_before_intermediate_beautifier == 0x2DC, "RE 0x4EC00 stores nb_iterations_before_intermediate_beautifier at +0x2DC");
static_assert(parameters::kenable_beautifier_common_cut == 0x2E0, "RE 0x4EC00 stores enable_beautifier_common_cut at +0x2E0");
static_assert(parameters::kenable_beautifier_improve_common_cut == 0x2E1, "RE 0x4EC00 stores enable_beautifier_improve_common_cut at +0x2E1");
static_assert(parameters::kenable_beautifier_floating == 0x2E2, "RE 0x4EC00 stores enable_beautifier_floating at +0x2E2");
static_assert(parameters::kenable_beautifier_reorganizer == 0x2E3, "RE 0x4EC00 stores enable_beautifier_reorganizer at +0x2E3");
static_assert(parameters::knb_iterations_before_beautifier_advanced == 0x31C, "RE 0x4EC00 stores nb_iterations_before_beautifier_advanced at +0x31C");
static_assert(parameters::knb_iterations_before_free_parts == 0x320, "RE 0x4EC00 stores nb_iterations_before_free_parts at +0x320");
static_assert(parameters::ktry_fill_free_parts == 0x324, "RE 0x4EC00 stores try_fill_free_parts at +0x324");
static_assert(parameters::kuse_multitorch_tiling == 0x330, "RE 0x4EC00 stores use_multitorch_tiling at +0x330");
static_assert(parameters::kuse_clusters == 0x331, "RE 0x4EC00 stores use_clusters at +0x331");
static_assert(parameters::kforce_nb_max_active_parts == 0x334, "RE 0x4EC00 stores force_nb_max_active_parts at +0x334");
static_assert(parameters::kforce_single_orientation_tiling == 0x338, "RE 0x4EC00 stores force_single_orientation_tiling at +0x338");
static_assert(parameters::kforce_single_orientation_asit == 0x339, "RE 0x4EC00 stores force_single_orientation_asit at +0x339");
static_assert(parameters::kseed == 0x33C, "RE 0x4EC00 stores seed at +0x33C");
static_assert(parameters::kenable_multi_thread == 0x340, "RE 0x4EC00 stores enable_multi_thread at +0x340");
static_assert(parameters::knb_max_threads == 0x344, "RE 0x4EC00 stores nb_max_threads at +0x344");
static_assert(parameters::kverbose == 0x348, "RE 0x4EC00 stores verbose at +0x348");
static_assert(parameters::klimited_intermediate == 0x349, "RE 0x4EC00 stores limited_intermediate at +0x349");
static_assert(parameters::kdetect_overlap == 0x34A, "RE 0x4EC00 stores detect_overlap at +0x34A");
static_assert(parameters::ktrace_nesting == 0x34B, "RE 0x4EC00 stores trace_nesting at +0x34B");
static_assert(parameters::ktrace_solution == 0x34C, "RE 0x4EC00 stores trace_solution at +0x34C");
static_assert(parameters::ktrace_best_solution == 0x34D, "RE 0x4EC00 stores trace_best_solution at +0x34D");
static_assert(parameters::ktrace_dxf == 0x34E, "RE 0x4EC00 stores trace_dxf at +0x34E");
static_assert(parameters::kstable_results == 0x34F, "RE 0x4EC00 stores stable_results at +0x34F");

}  // namespace lcns
