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

}  // namespace lcns
