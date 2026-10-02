// lcns/src/segcost.cpp -- RE 0x55E190, instruction by instruction.
//
// The association and the operand order of every comparison matter here: minsd and maxsd return the SECOND operand when
// either is NaN, so each of them is written as the ternary the instruction implements rather than as std::min/std::max,
// whose NaN behaviour differs. The differential test is what keeps this honest -- it runs the original (relocated, so
// that its sqrt calls reach a stub) and requires the same answer on every input.

#include "lcns/segcost.hpp"

#include <cmath>

namespace lcns {

double segmentLength(const double* segment4) {
    // 0x55E1AB/0x55E1B0 read the end point, 0x55E1B5/0x55E1B9 subtract the start, 0x55E1C7..0x55E1CF square and add,
    // 0x55E1D7 is the sqrtsd.
    const double dx = segment4[2] - segment4[0];
    const double dy = segment4[3] - segment4[1];
    return std::sqrt(dx * dx + dy * dy);
}

bool lengthExceedsThreshold(const double* a, const double* b, const double* c, const double* p) {
    const double l1 = segmentLength(a);
    const double l2 = segmentLength(b);

    // 0x55E216 minsd xmm8, xmm6 with xmm8 = l2 and xmm6 = l1: the smaller, or l1 when either is NaN.
    const double lower = (l2 < l1) ? l2 : l1;
    // 0x55E220 maxsd xmm0, xmm6 with xmm0 = l2 and xmm6 = l1.
    const double upper = (l2 > l1) ? l2 : l1;

    // 0x55E229 multiplies the larger by p[+0x28]; 0x55E224/0x55E22E multiply the smaller by p[+0x20].
    const double weightedUpper = upper * p[5];
    const double weightedLower = lower * p[4];
    // 0x55E23C maxsd xmm0, xmm6.
    const double firstMax = (weightedUpper > weightedLower) ? weightedUpper : weightedLower;
    // 0x55E244 loads p[+0x40] into xmm0 and 0x55E249 takes maxsd xmm0, xmm6.
    const double threshold = (p[8] > firstMax) ? p[8] : firstMax;

    // 0x55E251..0x55E26B: C's length, then 0x55E272 ucomisd xmm8, xmm6 and 0x55E287 seta al.
    const double l3 = segmentLength(c);
    return l3 > threshold;
}

}  // namespace lcns
