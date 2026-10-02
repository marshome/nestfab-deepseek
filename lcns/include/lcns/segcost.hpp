// lcns/segcost.hpp -- the threshold test the DLL performs over three segments and a parameter object.
//
// RE 0x55E190 (258 B, 3 callers). Read whole in round 357; the shape it implements is:
//
//     l1 = length(A) ; l2 = length(B) ; l3 = length(C)          length = sqrt(dx*dx + dy*dy)
//     lower = min(l2, l1) ; upper = max(l2, l1)
//     threshold = max( max(upper * p[+0x28], lower * p[+0x20]), p[+0x40] )
//     returns l3 > threshold
//
// Every one of those steps is a single SSE instruction in the original (minsd, maxsd, mulsd, addsd, sqrtsd, ucomisd,
// seta), and the differential test in tests/test_segcost.cpp holds this implementation to the original's own answers.
//
// The three calls the original makes to 0x62FE20 are libm's sqrt on the domain-error path only (the comparison is
// skipped when the sum of squares is non-negative, which is always), so the errno side effect is not reproduced here:
// see src/embedded_shims.cpp for the same note where the relocated copy's stub is supplied.
//
// Records: A, B and C are four doubles each -- start at +0x00/+0x08, end at +0x10/+0x18 -- and p is read at +0x20, +0x28
// and +0x40, i.e. p[4], p[5] and p[8].

#pragma once

namespace lcns {

/** Length of one four-double segment record. RE 0x55E1AB..0x55E1D7 (and the same block again for C). */
double segmentLength(const double* segment4);

/**
 * Whether C's length exceeds the threshold built from A, B and the parameters.
 * @param a - first segment, four doubles.
 * @param b - second segment, four doubles.
 * @param c - third segment, four doubles.
 * @param p - parameter object; only +0x20, +0x28 and +0x40 are read.
 * @returns the original's `seta` result.
 */
bool lengthExceedsThreshold(const double* a, const double* b, const double* c, const double* p);

}  // namespace lcns
