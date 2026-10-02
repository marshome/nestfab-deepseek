// lcns/include/lcns/config_parameters.hpp -- the nesting engine's parameters, each with the name the module uses.
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
// The offsets run from 0x24 to 0x344 with 22 gaps larger than eight bytes, so the struct has regions between the ones
// this parser touches -- those parameters are set elsewhere, or are not parameters at all.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

/** The offsets RE 0x4EC00 writes, in the module's own parameter vocabulary. */
namespace config {

constexpr std::size_t knb_iterations_before_postop                          = 0x24;
constexpr std::size_t knb_strips_first                                      = 0x44;
constexpr std::size_t knb_iterations_first                                  = 0x48;
constexpr std::size_t knb_strips_default                                    = 0x4C;
constexpr std::size_t knb_strips_filling_advanced                           = 0x50;
constexpr std::size_t knb_iterations_before_tiling                          = 0x60;
constexpr std::size_t knb_iterations_before_partial_multi_fill_tiling       = 0x78;
constexpr std::size_t knb_rectangle_try                                     = 0x84;
constexpr std::size_t knb_iterations_before_rectangle_advance               = 0x88;
constexpr std::size_t knb_iterations_before_rectangle_dual                  = 0x8C;
constexpr std::size_t knb_rectangle_advance_try                             = 0x90;
constexpr std::size_t knb_iterations_before_tiling_evaluated                = 0xC0;
constexpr std::size_t knesting_offset_ratio                                 = 0xE0;
constexpr std::size_t knb_iterations_before_advanced_nesting                = 0xE8;
constexpr std::size_t knb_iterations_before_expert_nesting                  = 0xEC;
constexpr std::size_t knb_iterations_before_small_rotation_nesting          = 0xF0;
constexpr std::size_t knesting_pow_boost                                    = 0x100;
constexpr std::size_t knesting_max_context_size                             = 0x108;
constexpr std::size_t kenable_rotate_compact_postop                         = 0x10E;
constexpr std::size_t knb_iterations_before_enlarge                         = 0x110;
constexpr std::size_t knb_iterations_before_enlarge_tiling                  = 0x114;
constexpr std::size_t knb_iterations_before_rotate_compact_postop           = 0x118;
constexpr std::size_t kdefault_enlarge                                      = 0x120;
constexpr std::size_t kbeam_frequency_ratio                                 = 0x140;
constexpr std::size_t kbeam_flip_frequency_ratio                            = 0x148;
constexpr std::size_t kbeam_width                                           = 0x150;
constexpr std::size_t kbeam_buckets_per_part                                = 0x160;
constexpr std::size_t knb_iterations_before_beam_advanced                   = 0x180;
constexpr std::size_t kbeam_advanced_width                                  = 0x184;
constexpr std::size_t knb_iterations_before_beam_expert                     = 0x190;
constexpr std::size_t kbeam_expert_width                                    = 0x194;
constexpr std::size_t kbeam_distinct_angle                                  = 0x1A8;
constexpr std::size_t knb_iterations_before_cut_nesting                     = 0x1B0;
constexpr std::size_t kcut_nesting_probabilty                               = 0x1B8;
constexpr std::size_t knb_iterations_before_float_filler                    = 0x1C4;
constexpr std::size_t knb_max_nested_parts_float_filler                     = 0x1DC;
constexpr std::size_t kfloat_filler_reduction_ratio                         = 0x1E0;
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
constexpr std::size_t kmax_cutting_cost_ratio                               = 0x2A8;
constexpr std::size_t kmin_cutting_cost_ratio                               = 0x2B0;
constexpr std::size_t kuse_old_evaluation_ratio                             = 0x2B8;
constexpr std::size_t knb_iterations_before_intermediate_beautifier         = 0x2DC;
constexpr std::size_t knb_iterations_before_beautifier_advanced             = 0x31C;
constexpr std::size_t knb_iterations_before_free_parts                      = 0x320;
constexpr std::size_t kforce_nb_max_active_parts                            = 0x334;
constexpr std::size_t kseed                                                 = 0x33C;
constexpr std::size_t knb_max_threads                                       = 0x344;

/** The count of parameters this parser names, for a test to assert rather than repeat. */
constexpr std::size_t kConfigParameterCount = 59;

}  // namespace config

/** A record of what each offset IS, for the reconstruction. It is deliberately not a struct with those members laid out: the point is
 *  to carry the module's names and offsets, and a laid-out struct would depend on the compiler's padding to agree with them. */
struct ConfigParameter {
    std::size_t offset;
    const char* name;
};

inline const ConfigParameter* configParameters(std::size_t& count) {
    static const ConfigParameter table[] = {
        {0x24, "nb_iterations_before_postop"},
        {0x44, "nb_strips_first"},
        {0x48, "nb_iterations_first"},
        {0x4C, "nb_strips_default"},
        {0x50, "nb_strips_filling_advanced"},
        {0x60, "nb_iterations_before_tiling"},
        {0x78, "nb_iterations_before_partial_multi_fill_tiling"},
        {0x84, "nb_rectangle_try"},
        {0x88, "nb_iterations_before_rectangle_advance"},
        {0x8C, "nb_iterations_before_rectangle_dual"},
        {0x90, "nb_rectangle_advance_try"},
        {0xC0, "nb_iterations_before_tiling_evaluated"},
        {0xE0, "nesting_offset_ratio"},
        {0xE8, "nb_iterations_before_advanced_nesting"},
        {0xEC, "nb_iterations_before_expert_nesting"},
        {0xF0, "nb_iterations_before_small_rotation_nesting"},
        {0x100, "nesting_pow_boost"},
        {0x108, "nesting_max_context_size"},
        {0x10E, "enable_rotate_compact_postop"},
        {0x110, "nb_iterations_before_enlarge"},
        {0x114, "nb_iterations_before_enlarge_tiling"},
        {0x118, "nb_iterations_before_rotate_compact_postop"},
        {0x120, "default_enlarge"},
        {0x140, "beam_frequency_ratio"},
        {0x148, "beam_flip_frequency_ratio"},
        {0x150, "beam_width"},
        {0x160, "beam_buckets_per_part"},
        {0x180, "nb_iterations_before_beam_advanced"},
        {0x184, "beam_advanced_width"},
        {0x190, "nb_iterations_before_beam_expert"},
        {0x194, "beam_expert_width"},
        {0x1A8, "beam_distinct_angle"},
        {0x1B0, "nb_iterations_before_cut_nesting"},
        {0x1B8, "cut_nesting_probabilty"},
        {0x1C4, "nb_iterations_before_float_filler"},
        {0x1DC, "nb_max_nested_parts_float_filler"},
        {0x1E0, "float_filler_reduction_ratio"},
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
        {0x2A8, "max_cutting_cost_ratio"},
        {0x2B0, "min_cutting_cost_ratio"},
        {0x2B8, "use_old_evaluation_ratio"},
        {0x2DC, "nb_iterations_before_intermediate_beautifier"},
        {0x31C, "nb_iterations_before_beautifier_advanced"},
        {0x320, "nb_iterations_before_free_parts"},
        {0x334, "force_nb_max_active_parts"},
        {0x33C, "seed"},
        {0x344, "nb_max_threads"},
    };
    count = sizeof(table) / sizeof(table[0]);
    return table;
}

static_assert(config::knb_iterations_before_postop == 0x24, "RE 0x4EC00 stores nb_iterations_before_postop at +0x24");
static_assert(config::knb_strips_first == 0x44, "RE 0x4EC00 stores nb_strips_first at +0x44");
static_assert(config::knb_iterations_first == 0x48, "RE 0x4EC00 stores nb_iterations_first at +0x48");
static_assert(config::knb_strips_default == 0x4C, "RE 0x4EC00 stores nb_strips_default at +0x4C");
static_assert(config::knb_strips_filling_advanced == 0x50, "RE 0x4EC00 stores nb_strips_filling_advanced at +0x50");
static_assert(config::knb_iterations_before_tiling == 0x60, "RE 0x4EC00 stores nb_iterations_before_tiling at +0x60");
static_assert(config::knb_iterations_before_partial_multi_fill_tiling == 0x78, "RE 0x4EC00 stores nb_iterations_before_partial_multi_fill_tiling at +0x78");
static_assert(config::knb_rectangle_try == 0x84, "RE 0x4EC00 stores nb_rectangle_try at +0x84");
static_assert(config::knb_iterations_before_rectangle_advance == 0x88, "RE 0x4EC00 stores nb_iterations_before_rectangle_advance at +0x88");
static_assert(config::knb_iterations_before_rectangle_dual == 0x8C, "RE 0x4EC00 stores nb_iterations_before_rectangle_dual at +0x8C");
static_assert(config::knb_rectangle_advance_try == 0x90, "RE 0x4EC00 stores nb_rectangle_advance_try at +0x90");
static_assert(config::knb_iterations_before_tiling_evaluated == 0xC0, "RE 0x4EC00 stores nb_iterations_before_tiling_evaluated at +0xC0");
static_assert(config::knesting_offset_ratio == 0xE0, "RE 0x4EC00 stores nesting_offset_ratio at +0xE0");
static_assert(config::knb_iterations_before_advanced_nesting == 0xE8, "RE 0x4EC00 stores nb_iterations_before_advanced_nesting at +0xE8");
static_assert(config::knb_iterations_before_expert_nesting == 0xEC, "RE 0x4EC00 stores nb_iterations_before_expert_nesting at +0xEC");
static_assert(config::knb_iterations_before_small_rotation_nesting == 0xF0, "RE 0x4EC00 stores nb_iterations_before_small_rotation_nesting at +0xF0");
static_assert(config::knesting_pow_boost == 0x100, "RE 0x4EC00 stores nesting_pow_boost at +0x100");
static_assert(config::knesting_max_context_size == 0x108, "RE 0x4EC00 stores nesting_max_context_size at +0x108");
static_assert(config::kenable_rotate_compact_postop == 0x10E, "RE 0x4EC00 stores enable_rotate_compact_postop at +0x10E");
static_assert(config::knb_iterations_before_enlarge == 0x110, "RE 0x4EC00 stores nb_iterations_before_enlarge at +0x110");
static_assert(config::knb_iterations_before_enlarge_tiling == 0x114, "RE 0x4EC00 stores nb_iterations_before_enlarge_tiling at +0x114");
static_assert(config::knb_iterations_before_rotate_compact_postop == 0x118, "RE 0x4EC00 stores nb_iterations_before_rotate_compact_postop at +0x118");
static_assert(config::kdefault_enlarge == 0x120, "RE 0x4EC00 stores default_enlarge at +0x120");
static_assert(config::kbeam_frequency_ratio == 0x140, "RE 0x4EC00 stores beam_frequency_ratio at +0x140");
static_assert(config::kbeam_flip_frequency_ratio == 0x148, "RE 0x4EC00 stores beam_flip_frequency_ratio at +0x148");
static_assert(config::kbeam_width == 0x150, "RE 0x4EC00 stores beam_width at +0x150");
static_assert(config::kbeam_buckets_per_part == 0x160, "RE 0x4EC00 stores beam_buckets_per_part at +0x160");
static_assert(config::knb_iterations_before_beam_advanced == 0x180, "RE 0x4EC00 stores nb_iterations_before_beam_advanced at +0x180");
static_assert(config::kbeam_advanced_width == 0x184, "RE 0x4EC00 stores beam_advanced_width at +0x184");
static_assert(config::knb_iterations_before_beam_expert == 0x190, "RE 0x4EC00 stores nb_iterations_before_beam_expert at +0x190");
static_assert(config::kbeam_expert_width == 0x194, "RE 0x4EC00 stores beam_expert_width at +0x194");
static_assert(config::kbeam_distinct_angle == 0x1A8, "RE 0x4EC00 stores beam_distinct_angle at +0x1A8");
static_assert(config::knb_iterations_before_cut_nesting == 0x1B0, "RE 0x4EC00 stores nb_iterations_before_cut_nesting at +0x1B0");
static_assert(config::kcut_nesting_probabilty == 0x1B8, "RE 0x4EC00 stores cut_nesting_probabilty at +0x1B8");
static_assert(config::knb_iterations_before_float_filler == 0x1C4, "RE 0x4EC00 stores nb_iterations_before_float_filler at +0x1C4");
static_assert(config::knb_max_nested_parts_float_filler == 0x1DC, "RE 0x4EC00 stores nb_max_nested_parts_float_filler at +0x1DC");
static_assert(config::kfloat_filler_reduction_ratio == 0x1E0, "RE 0x4EC00 stores float_filler_reduction_ratio at +0x1E0");
static_assert(config::kdatabase_relax_every == 0x1EC, "RE 0x4EC00 stores database_relax_every at +0x1EC");
static_assert(config::kadaptative_price_max_random == 0x200, "RE 0x4EC00 stores adaptative_price_max_random at +0x200");
static_assert(config::kboost_price_max_random == 0x208, "RE 0x4EC00 stores boost_price_max_random at +0x208");
static_assert(config::kcombined_price_frequency == 0x210, "RE 0x4EC00 stores combined_price_frequency at +0x210");
static_assert(config::klinear_price_frequency == 0x218, "RE 0x4EC00 stores linear_price_frequency at +0x218");
static_assert(config::kboost_price_frequency == 0x220, "RE 0x4EC00 stores boost_price_frequency at +0x220");
static_assert(config::klinear_fill_frequency == 0x228, "RE 0x4EC00 stores linear_fill_frequency at +0x228");
static_assert(config::ksimple_fill_frequency == 0x230, "RE 0x4EC00 stores simple_fill_frequency at +0x230");
static_assert(config::krandom_price_frequency == 0x238, "RE 0x4EC00 stores random_price_frequency at +0x238");
static_assert(config::knb_iterations_before_relaxed_mono == 0x264, "RE 0x4EC00 stores nb_iterations_before_relaxed_mono at +0x264");
static_assert(config::kmono_relaxed_frequency == 0x268, "RE 0x4EC00 stores mono_relaxed_frequency at +0x268");
static_assert(config::kmono_relaxed_max_bonus == 0x270, "RE 0x4EC00 stores mono_relaxed_max_bonus at +0x270");
static_assert(config::kmax_dual_ratio == 0x288, "RE 0x4EC00 stores max_dual_ratio at +0x288");
static_assert(config::kmax_cutting_cost_ratio == 0x2A8, "RE 0x4EC00 stores max_cutting_cost_ratio at +0x2A8");
static_assert(config::kmin_cutting_cost_ratio == 0x2B0, "RE 0x4EC00 stores min_cutting_cost_ratio at +0x2B0");
static_assert(config::kuse_old_evaluation_ratio == 0x2B8, "RE 0x4EC00 stores use_old_evaluation_ratio at +0x2B8");
static_assert(config::knb_iterations_before_intermediate_beautifier == 0x2DC, "RE 0x4EC00 stores nb_iterations_before_intermediate_beautifier at +0x2DC");
static_assert(config::knb_iterations_before_beautifier_advanced == 0x31C, "RE 0x4EC00 stores nb_iterations_before_beautifier_advanced at +0x31C");
static_assert(config::knb_iterations_before_free_parts == 0x320, "RE 0x4EC00 stores nb_iterations_before_free_parts at +0x320");
static_assert(config::kforce_nb_max_active_parts == 0x334, "RE 0x4EC00 stores force_nb_max_active_parts at +0x334");
static_assert(config::kseed == 0x33C, "RE 0x4EC00 stores seed at +0x33C");
static_assert(config::knb_max_threads == 0x344, "RE 0x4EC00 stores nb_max_threads at +0x344");

}  // namespace lcns
