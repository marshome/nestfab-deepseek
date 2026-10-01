// include/lcns/budget.hpp -- the budget formulas recovered from 0x1B33B0 (goal round 151).
//
// They are kept in their own header because engine.hpp's committed state carries a cosmetic join from an
// earlier patch, and further in-place edits there proved fragile. Everything here is read from instructions
// and carries the address of each fragment.
#pragma once

#include "lcns/engine.hpp"

namespace lcns {

//     1B4FE5  movsd xmm1,[r13] ; 1B4FEB mulsd xmm1,[r13+8] ; 1B4FF1 mulsd xmm1,[1.5] ; 1B4FF9 ucomisd
// a threshold of 1.5 * (a * b), compared against another value.
inline constexpr double kPairLimitWeight = 1.5;      // RE 0x1B4FF1

inline double limitFromPair(double first, double second) {          // RE 0x1B4FEB/0x1B4FF1
    return kPairLimitWeight * (first * second);
}

//     1B5113  movsd xmm0,[0.03] ; 1B511B mulsd xmm0,[rsi+0x18]      -> 0.03 * base
//     1B5153  movsd xmm2,[30] ; 1B515B movsd xmm1,[0.25] ; 1B5169 mulsd xmm1,[rsi+0x18]
//     1B5182  cvtsi2sd xmm0,rax ; 1B5187 divsd xmm0,[1000] ; 1B518F mulsd xmm2,xmm0
//     1B5193  subsd xmm1,xmm2 ; 1B519D cvttsd2si r12d,xmm1
// The truncated result goes into r12d, and round 147 read
//     1B4B95  cvtsi2sd xmm0,r12d ; 1B4B9E addsd xmm1,xmm0
// ADDING r12d to 0.5 * (0.7 * base): the two fragments are one expression. The divisor here is the CONSTANT
// 1000, unlike round 148's magic-multiply 1e6, so the count is named for its position only.
inline constexpr double kBudgetWeightExtra = 0.03;    // RE 0x1B5113
inline constexpr double kCountWeight = 30.0;          // RE 0x1B5153
inline constexpr double kBudgetWeightQuarter = 0.25;  // RE 0x1B515B

inline double countBudgetLimit(double base, std::int64_t count) {   // RE 0x1B5182..0x1B5193
    const double scaled = static_cast<double>(count) / kMsPerSecond;   // RE 0x1B5187
    return kBudgetWeightQuarter * base - kCountWeight * scaled;
}

inline double extraWeightedBudget(double base) { return kBudgetWeightExtra * base; }   // RE 0x1B5113/1B511B

//     1B535D  cvtsi2sd xmm0,rax ; 1B536A divsd xmm0,xmm6 ; 1B5373 subsd xmm7,xmm0 ; 1B5377 mulsd xmm7,[0.9]
inline constexpr double kBudgetWeightNine = 0.9;      // RE 0x1B5377

inline double decayedBudget(double base, std::int64_t count) {      // RE 0x1B536A..0x1B5377
    const double elapsed = static_cast<double>(count) / kMsPerSecond;   // RE 0x1B536A
    return kBudgetWeightNine * (weightedBudget(base) - elapsed);        // RE 0x1B5373/0x1B5377
}

}  // namespace lcns
