// include/lcns/steps.hpp -- the step-count formulas recovered from 0x1A1810 (goal round 165).
//
// The routine's own texts are 'p.first ', 'nb_strips ', 'nb_double_steps ', 'nb_int_steps', and it computes
// one integer count per step size with a divide, a rounding term and a truncation:
//     1A184F/1A1857/1A1881   value / 0.0001 + 0.5 -> int
//     1A1890/1A1894/1A18A9   value / (n/1e6) + 0.0003 -> int
//     1A18B2/1A18B6/1A18BA   then * 10 / (n/1e6) + 0.0039
#pragma once

#include <cstdint>

namespace lcns {

// RE 0x1A184F, 0x1A1894, 0x1A18BA: the step sizes, each with its own rounding term.
inline constexpr double kStepFine = 0.0001;     // RE 0x1A184F
inline constexpr double kStepMid = 0.0003;      // RE 0x1A1894
inline constexpr double kStepCoarse = 0.0039;   // RE 0x1A18BA
inline constexpr double kStepRoundTerm = 0.5;   // RE 0x1A1857
inline constexpr double kStepTens = 10.0;       // RE 0x1A18A1
inline constexpr double kStepTickScale = 1e6;   // RE 0x1A1878 (the same value as engine.hpp's kSeedScale)

// RE the shape shared by the three sites: divide by the step, add the rounding term, truncate toward zero.
inline std::int64_t stepCount(double value, double step, double rounding) {
    return static_cast<std::int64_t>(value / step + rounding);
}

// RE 0x1A184F..0x1A1881: the fine step, with the 0.5 term.
inline std::int64_t fineStepCount(double value) { return stepCount(value, kStepFine, kStepRoundTerm); }

// RE 0x1A1894: the mid step, whose term is the step's own size rather than a half.
inline std::int64_t midStepCount(double value, double scale) {
    return stepCount(value, scale, kStepMid);
}

// RE 0x1A1890: the scale that both later sites divide by, `n / 1e6`.
inline double stepScale(std::int64_t n) { return static_cast<double>(n) / kStepTickScale; }


// RE 0x24C4CF, 0x5C23D7 and 0x5D29D2 -- THREE independent functions (237 B, 210 B and 125 B) each do
//     divsd  by 6.283185307 ; addsd 0.5 ; cvttsd2si
// Three separate sites dividing by that value is what makes it 2*pi here, and round(value / 2pi) is a count
// of whole turns. The arithmetic is the same three-step shape as the step counts above.
inline constexpr double kTwoPiRounded = 6.283185307;    // RE 0x24C4CF / 0x5C23D7 / 0x5D29D2

inline std::int64_t turnCount(double value) {
    return stepCount(value, kTwoPiRounded, kStepRoundTerm);     // RE the three sites above
}

// RE 0x21B85F (inside 0x21B7C0, 4008 B) and 0x17E1F8 (inside 0x17E180, 752 B): the same idiom dividing by 360.
inline constexpr double kDegreesPerTurn = 360.0;        // RE 0x21B85F / 0x17E1F8

inline std::int64_t degreeTurnCount(double value) {
    return stepCount(value, kDegreesPerTurn, kStepRoundTerm);   // RE the two sites above
}

}  // namespace lcns
