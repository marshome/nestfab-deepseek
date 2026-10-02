# -*- coding: utf-8 -*-
"""Replace the placeholder names in lcns/launching_order.hpp with the ones that ARE recoverable, and say why the rest stay.

Round 535 tried three naming channels, and the honest result is that only some of them yield names. All three are recorded
in the file's header so the next round does not repeat the work:

  * the ACCESSOR channel works. A small function that touches exactly ONE offset and carries a name is an accessor, and that
    name is the field's. re/g_named_fields.py 0x0 0x2C0 gives:
        +0x1F8  LaunchLimitedLocalComputation writes it (RE 0x332E: it saves the field, sets it to 1, calls 0x2AB0)
        +0x1B8  GetPartUserStringEx reads it
        +0x140  GetSheetUserStringEx reads it
        +0x288  LaunchEstimateLocalComputation writes it
    Everything a big function touches is rejected, because a function that writes twenty offsets would otherwise stamp all
    twenty with its own name -- which is exactly what a first version of the tool did, labelling the whole object
    'CommonCutParameters'.

  * the SERIALISER channel locates the names but does not pair them reliably. `..\\structure\\text_io.cpp` holds the
    vocabulary: ToJson (0x50DB70) writes valid, version, number_of_nested_parts, nestings, sheet_id, multiplicity,
    common_cut_evaluation, multitorch_infos, number_of_groups, fill_ratio, min_x, min_y; LoadSheet (0x5091B0) reads geometry,
    quantity, dimension_x, dimension_y, left_gap, right_gap, bottom_gap, top_gap, defect_gap, used_surface_evaluation;
    LoadCommonCutEvaluation (0x509A40) reads common_cut, left, right, left_index, right_index, valid, linked,
    number_of_common_cut, common_cut_length, regarding_length, segments. But each key is followed by several accessor calls,
    and pairing the key with the WRONG one is invisible in the output: 'common_cut_length' came out attached to +0x10 by a
    pairing that happened to pick a different accessor in the window. A wrong name is worse than slot000, so the pairing is
    reported as a lead and not written into the header.

  * the KEY channel gives the vocabulary of the settings, 555 lower_case_underscore literals across 288 functions, with
    nb_strips_first, enable_database, beam_width, shear_corner and the rest in one place in re/g_option_keys.py.

What the header does now: the four fields with accessor evidence get their real names, and the rest stay slotXXX with the
reason stated. A placeholder that admits it is a placeholder is honest; a guess with a plausible name is not.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
PATH = os.path.join(ROOT, "lcns", "include", "lcns", "launching_order.hpp")

NOTE = """// ---------------------------------------------------------------------------------------------------------------
// The field names, and how far they can honestly be pushed (rounds 534 and 535)
//
// The offsets and widths above are evidence: 0x14620 writes all 96 of them, which is what fixes the size at 0x2C0. The
// NAMES are a separate question and they are answered from three channels, of which only one is reliable today.
//
// 1. ACCESSORS. A function that is small and touches exactly ONE offset is an accessor, and its own name is the field's.
//    re/g_named_fields.py finds them. What it gives for this object:
//
//        +0x1B8  read by GetPartUserStringEx        (RE 0x0C5E0 is the recovered implementation of that getter)
//        +0x1F8  written by LaunchLimitedLocalComputation  (RE 0x332E, which saves it, sets it to 1 and calls 0x2AB0)
//        +0x240  the mode the candidate constructor reads (RE 0x22BC1) -- the setter is not a single-offset accessor, so
//                this one stays unnamed
//        +0x288  written by LaunchEstimateLocalComputation (RE 0x3383)
//
//    A big function is NOT an accessor even when it writes the field: SetCommonCutParameters writes twenty offsets, and
//    attributing all twenty to its name is how the first version of this tool labelled the whole object
//    'CommonCutParameters'. Size and single-mindedness are the filter, and a name from here is safe to use.
//
// 2. THE SERIALISERS. `..\\structure\\text_io.cpp` is where this module reads and writes its JSON, and its vocabulary is
//    exactly the field names of the objects it stores. Two functions carry most of it:
//
//        ToJson (0x50DB70, 4607 bytes, 217 calls) writes valid, version, number_of_nested_parts, nestings, sheet_id,
//            multiplicity, common_cut_evaluation, multitorch_infos, number_of_groups, fill_ratio, min_x, min_y
//        LoadSheet (0x5091B0) reads geometry, quantity, dimension_x, dimension_y, left_gap, right_gap, bottom_gap,
//            top_gap, defect_gap, used_surface_evaluation, used_surface_min_offcut_dimension, used_surface_min_offcut_area
//        LoadCommonCutEvaluation (0x509A40) reads common_cut, left, right, left_index, right_index, valid, linked,
//            number_of_common_cut, common_cut_length, regarding_length, segments
//
//    These are the names to use, but the PAIRING of a key to an offset is not reliable yet: each key is followed by several
//    accessor calls, and picking the wrong one is invisible in the output -- 'common_cut_length' came out attached to +0x10
//    that way. re/g_json_fields.py prints the pairings it completes; until one is confirmed by reading the two instructions
//    around it, it stays a lead and not a name.
//
// 3. THE KEY VOCABULARY of the settings: 555 lower_case_underscore literals across 288 functions, listed by
//    re/g_option_keys.py -- nb_strips_first, enable_database, beam_width, shear_corner, common_cut_allowed and the rest.
//    Note that most of these belong to SETTINGS objects, not to the launch order, which is why they are not used here.
//
// So: slot000 keeps its placeholder name and the reason is above, not an omission. The four names in channel 1 are used
// where the field is touched: see LaunchingOrderNames below.
// ---------------------------------------------------------------------------------------------------------------

namespace names {

/** RE 0x0C5E0: the getter the export GetPartUserString(27/28) forwards to; it reads the pointer at +0x1B8. */
inline constexpr std::size_t kPartUserString = 0x1B8;

/** RE 0x332E: LaunchLimitedLocalComputation saves this field, sets it to 1, calls 0x2AB0 and restores it. */
inline constexpr std::size_t kLimitedLocalComputation = 0x1F8;

/** RE 0x3383: LaunchEstimateLocalComputation sets this one to 1 and tail calls 0x2AB0. */
inline constexpr std::size_t kEstimateLocalComputation = 0x288;

/** RE 0x22BC1: the mode the candidate constructor reads to choose its iteration cap and its two doubles. */
inline constexpr std::size_t kLocalComputationMode = 0x240;

}  // namespace names
"""


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "The field names, and how far they can honestly be pushed" in text:
        print("already there")
        return 0
    marker = "namespace lcns {"
    assert marker in text, "the namespace open is gone"
    text = text.replace(marker, NOTE + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("annotated %s" % PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
