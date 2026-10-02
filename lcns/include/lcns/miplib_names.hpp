// lcns/include/lcns/miplib_names.hpp -- the benchmark instance names RE 0x2A3520 loads, and what they establish.
//
// RE 0x2A3520 is 12744 bytes and 2026 instructions. The findings archive analysed it independently and reached:
//
//     "0x2a3520, 12744 bytes / 2026 instructions
//      17 callees ...
//      strings: exmip1, AUATUWVSH, p0033, flugpl, enigma, mod011, probing, mas76
//      尚未解: 身份/角色未定；不给它编名字."      (Appendix 7, marked proven + unsolved)
//
// and this project's own extraction, following every call site of the option lookup RE 0x82A3E0 and keeping the strings that are NOT
// stored into a field, found 51 such strings -- of which 49 are in this list and RE 0x2A3520 is the only function that loads any of them:
//
//     air03 air04 air05 bell3a bell5 blend2 cap6000 danoint dcmulti dsbmip egout enigma exmip1 fiber fixnet6 flugpl
//     gesa2 gesa2_o gesa3 gesa3_o khb05250 l152lav markshare1 markshare2 mas76 misc03 misc06 misc07 mitre mod008
//     mod010 mod011 modglob noswot_z p0033 p0201 p0282 p0548 p2756 pp08a pp08acuts probing qnet1 qnet1_o rentacar
//     seymour seymour_1 stein27 stein45
//
// **TWO INDEPENDENT CHARACTERISATIONS OF ONE FUNCTION.** The archive found its strings by reading rodata and named eight of them; the
// extraction found 49 by following call sites. The overlap (`exmip1`, `p0033`, `flugpl`, `enigma`, `mod011`, `probing`, `mas76`) is seven
// of the archive's eight, and the archive's eighth is `AUATUWVSH`, which the extraction did not classify as data.
//
// WHAT THE NAMES ESTABLISH, which is more than either reading alone: **these are MIPLIB benchmark instances** -- the standard test set for
// integer-programming solvers -- and a nesting engine has no reason to contain them except as TEST DATA or REFERENCE RESULTS. Combined
// with the archive's finding that the function references `mip`-shaped floating constants and calls the option lookup, the defensible
// statement is that RE 0x2A3520 is a benchmark harness rather than engine domain logic.
//
// THE ARCHIVE'S REFUSAL IS THE RIGHT ONE AND IS KEPT HERE: it declined to name the function, and this header does not name it either. What
// it records is the EVIDENCE -- 49 instance names in one function -- and the one conclusion the evidence supports, which is that the
// function is not part of the nesting pipeline.
#pragma once

#include <cstddef>

namespace lcns {

/** The 49 MIPLIB instance names RE 0x2A3520 loads, alphabetically as the module stores them. */
inline const char* const* benchmarkInstanceNames(std::size_t& count) {
    static const char* const names[] = {
        "air03", "air04", "air05", "bell3a", "bell5", "blend2", "cap6000", "danoint",
        "dcmulti", "dsbmip", "egout", "enigma", "exmip1", "fiber", "fixnet6", "flugpl",
        "gesa2", "gesa2_o", "gesa3", "gesa3_o", "khb05250", "l152lav", "markshare1", "markshare2",
        "mas76", "misc03", "misc06", "misc07", "mitre", "mod008", "mod010", "mod011",
        "modglob", "noswot_z", "p0033", "p0201", "p0282", "p0548", "p2756", "pp08a",
        "pp08acuts", "probing", "qnet1", "qnet1_o", "rentacar", "seymour", "seymour_1", "stein27",
        "stein45",
    };
    count = sizeof(names) / sizeof(names[0]);
    return names;
}

/** RE 0x2A3520, the only function that loads any of these names. */
constexpr std::uintptr_t kBenchmarkLoader = 0x2A3520;
/** And its two control strings, which are values rather than instance names. */
constexpr const char* kBenchmarkFalse = "false";
constexpr const char* kBenchmarkPlain = "plain";

static_assert(kBenchmarkLoader == 0x2A3520, "the loader, recorded once so a test can assert it");

}  // namespace lcns
