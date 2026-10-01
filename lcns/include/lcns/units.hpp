// include/lcns/units.hpp -- the micro-scale convention recovered from two independent functions.
//
// 0x19F1F0 (257 instructions):  19F25F cvtsi2sd xmm1,[rbx] ; 19F269 divsd xmm1,[1e6]
// 0x19F8F0 (251 instructions):  19FA0E cvtsi2sd xmm2,[rdi] ; 19FA25 divsd xmm2,[1e6]
// Both take an integer out of the object and divide it by 1e6, and both take their constants from the SAME
// read-only block:
//     1e-06   rva 0x9BE4F0   loaded at 0x19F246 and 0x19FA1D
//     0.0001  rva 0x9BE4F8   loaded at 0x19F2CC and 0x19FA89
//     1e+06   rva 0x9BE508   loaded at 0x19F269 and 0x19FA25
// Two independent functions, one divisor, one shared constants block: a convention, not a local choice.
#pragma once

#include <cstdint>

namespace lcns {

inline constexpr double kMicroScale = 1e6;          // RE rva 0x9BE508, used at 0x19F269 / 0x19FA25
inline constexpr double kMicroInverse = 1e-6;       // RE rva 0x9BE4F0, used at 0x19F246 / 0x19FA1D
inline constexpr double kTenThousandth = 0.0001;    // RE rva 0x9BE4F8, used at 0x19F2CC / 0x19FA89

// RE the two sites above: an integer held at the micro scale, expressed as a double in base units.
inline double microToUnit(std::int64_t micro) {
    return static_cast<double>(micro) / kMicroScale;
}

// RE the reverse direction, which the same constants block expresses as kMicroInverse.
inline double unitToMicro(double value) { return value * kMicroScale; }


// --- the shared constant block (round 172) -------------------------------------------------------
// Scanning un-cited functions for double slots reached from three or more of them found 33 such slots. Six of
// them lie in one contiguous read-only block used by a family of functions (597 to 3850 bytes):
//     0x9DFB98  1e+06        5 functions
//     0x9DFBA0  2.22045e-16  9 functions   <- 2**-52, the machine epsilon
//     0x9DFBC8  1             16 functions
//     0x9DFBD0  0.5           11 functions
//     0x9DFBD8  -1            7 functions
//     0x9DFC20  50            14 functions
// The epsilon is the one value here that can be confirmed by COMPUTATION instead of recognition: the test
// compares it against std::numeric_limits<double>::epsilon(), so the claim does not rest on remembering the
// constant. The others are recorded with their slots and left unnamed, because 50 and 1 are not names.
inline constexpr double kSharedEpsilon = 2.220446049250313e-16;   // RE rva 0x9DFBA0, 9 functions
inline constexpr double kSharedHalf = 0.5;                        // RE rva 0x9DFBD0, 11 functions
inline constexpr double kSharedMicroScale = 1e6;                  // RE rva 0x9DFB98, 5 functions
inline constexpr double kSharedNegativeOne = -1.0;                // RE rva 0x9DFBD8, 7 functions
inline constexpr double kSharedFifty = 50.0;                      // RE rva 0x9DFC20, 14 functions

}  // namespace lcns
