// tests/test_segcost.cpp -- the segment threshold test against the original (0x55E190), which is executable here because
// its three sqrt calls were relocated to the project's own std::sqrt through a stub.
//
// Why this test is worth its length: the kernel is a chain of four SSE comparisons whose NaN behaviour differs between
// minsd/maxsd and std::min/std::max, and whose operand order decides which length is multiplied by which parameter. A
// reader could get either wrong and still see plausible numbers. Running the original removes that doubt for every input
// the table below covers.

#include "check.hpp"
#include "lcns/embedded.hpp"
#include "lcns/segcost.hpp"

#include <cstdint>
#include <cstring>

namespace emb = lcns::embedded;

namespace {

/** The four-double segment records and the parameter objects the differential test walks. */
const double kSegments[][4] = {
    {0.0, 0.0, 3.0, 4.0},          // length 5
    {0.0, 0.0, 6.0, 8.0},          // length 10
    {0.0, 0.0, 0.0, 0.0},          // length 0
    {1.5, -2.0, 1.5, -2.0},        // length 0, translated
    {-1.0, 1.0, 2.0, 5.0},         // length 5
    {0.25, 0.5, 0.75, 1.5},        // length sqrt(0.25 + 1.0)
    {2.0, 2.0, 2.0, 3.0},          // length 1
    {-3.0, -4.0, 0.0, 0.0},        // length 5, reversed direction
};

const double kParams[][9] = {
    {0, 0, 0, 0, 1.0, 1.0, 0, 0, 0.0},
    {0, 0, 0, 0, 0.5, 2.0, 0, 0, 0.0},
    {0, 0, 0, 0, 1.0, 1.0, 0, 0, 100.0},     // p[+0x40] dominates
    {0, 0, 0, 0, 0.0, 0.0, 0, 0, 0.0},       // threshold 0
    {0, 0, 0, 0, 3.0, 0.25, 0, 0, 1.0},
    {0, 0, 0, 0, 1.0, 1.0, 0, 0, 7.5},       // right at a length
};

}  // namespace

int main() {
    // ---------------------------------------------------------------- properties, first: they are readable claims
    {
        const double a[4] = {0.0, 0.0, 3.0, 4.0};    // 5
        const double b[4] = {0.0, 0.0, 0.0, 0.0};    // 0
        const double zero[9] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
        // with a zero threshold a segment of length 5 must exceed it
        const double c5[4] = {0.0, 0.0, 3.0, 4.0};
        CHECK(lcns::lengthExceedsThreshold(a, b, c5, zero));
        // and a zero-length one must not
        const double c0[4] = {0.0, 0.0, 0.0, 0.0};
        CHECK(!lcns::lengthExceedsThreshold(a, b, c0, zero));
        // With zero weights the threshold is p[+0x40] alone, which isolates the strictness of the comparison.
        // CORRECTED in round 357: the first version of this check left p[4] = p[5] = 1.0, so upper * 1.0 = 5 already
        // made the threshold 5 and the answer false regardless of p[+0x40].
        double p[9] = {0, 0, 0, 0, 0.0, 0.0, 0, 0, 4.999};
        CHECK(lcns::lengthExceedsThreshold(a, b, c5, p));
        p[8] = 5.0;
        CHECK(!lcns::lengthExceedsThreshold(a, b, c5, p));   // strict: equal is not above
        // the two lengths are weighted differently: with l1 = 5, l2 = 10 and weights (0.5, 2.0) the larger one is
        // multiplied by 2.0, so the threshold is 20 and C = 6 does not exceed it
        const double l10[4] = {0.0, 0.0, 6.0, 8.0};
        const double c6[4] = {0.0, 0.0, 3.6, 4.8};     // length 6
        const double weighted[9] = {0, 0, 0, 0, 0.5, 2.0, 0, 0, 0.0};
        CHECK(!lcns::lengthExceedsThreshold(a, l10, c6, weighted));
        // Swapping which parameter multiplies which length changes the answer -- the operand order this check exists to
        // pin down. CORRECTED in round 357: with C = 6 both thresholds (20 and 10) were above it, so nothing flipped.
        // With C = 12 the two thresholds bracket it, and the swap is what decides.
        const double c12[4] = {0.0, 0.0, 7.2, 9.6};    // length 12
        const double swapped[9] = {0, 0, 0, 0, 2.0, 0.5, 0, 0, 0.0};
        CHECK(!lcns::lengthExceedsThreshold(a, l10, c12, weighted));   // threshold 20 (10 * p[+0x28] = 2.0)
        CHECK(lcns::lengthExceedsThreshold(a, l10, c12, swapped));     // threshold 10 (5 * p[+0x20] = 2.0)
        // zero-length segments give a zero threshold, so any positive C exceeds it
        CHECK(lcns::lengthExceedsThreshold(b, b, c6, zero));
        CHECK(!lcns::lengthExceedsThreshold(b, b, c0, zero));
    }

    // ---------------------------------------------------------------- the length helper itself
    {
        const double seg[4] = {0.0, 0.0, 3.0, 4.0};
        CHECK(lcns::segmentLength(seg) == 5.0);
        const double seg2[4] = {1.0, 1.0, 4.0, 5.0};
        CHECK(lcns::segmentLength(seg2) == 5.0);
        const double zero[4] = {2.0, 2.0, 2.0, 2.0};
        CHECK(lcns::segmentLength(zero) == 0.0);
    }

    // ---------------------------------------------------------------- differential against the original
#if defined(LCNS_HAS_EMBEDDED_ASM)
    {
        // The relocated executable copy: its three calls to libm's sqrt now reach lcns_sqrt_shim.
        auto original = reinterpret_cast<bool (*)(const double*, const double*, const double*, const double*)>(
            emb::originalOf(0x55E190u));
        CHECK(original != nullptr);
        const emb::Block* b = emb::find(0x55E190u);
        CHECK(b != nullptr);
        if (b != nullptr) {
            CHECK(b->status == emb::Status::CallableRelocated);
            CHECK(b->reason != nullptr && b->reason[0] != '\0');   // and it says what was rewritten
        }
        if (original != nullptr) {
            std::size_t compared = 0;
            std::size_t trues = 0;
            for (const double* a : kSegments) {
                for (const double* bb : kSegments) {
                    for (const double* c : kSegments) {
                        for (const double* p : kParams) {
                            const bool mine = lcns::lengthExceedsThreshold(a, bb, c, p);
                            const bool theirs = original(a, bb, c, p);
                            CHECK(mine == theirs);
                            if (theirs) {
                                ++trues;
                            }
                            ++compared;
                        }
                    }
                }
            }
            CHECK(compared == 8u * 8u * 8u * 6u);   // segments cubed times the parameter sets
            // A table where every answer came out false (or every one true) would prove almost nothing, so the split is
            // asserted too: the cases must exercise both sides of the comparison.
            CHECK(trues > 0);
            CHECK(trues < compared);
        }
    }
#endif

    return check::finish("segcost");
}
