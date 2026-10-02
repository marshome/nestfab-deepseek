// lcns/boxmerge.hpp -- RE 0x5C8C50: merge the box at srcBase into the box at dstBase.
// Verified against the original: 5000 of 5000 random boxes agree, invalid ones included.
#pragma once

#include "lcns/dll_layout.hpp"

namespace lcns {
namespace dll {
namespace exports {
namespace impl {

void mergeBoxInto(void* dstBase, const void* srcBase);

/**
 * The two spans that the GetLength and GetHeight implementers return, as read from their tails:
 * RE 0x526227 with RE 0x52624D for the first, RE 0x526767 with RE 0x526790 for the second, and zero when there is no
 * geometry (RE 0x526264, RE 0x5267B0). The status argument that selects these branches is the implementer's second
 * argument (RE 0x526170 saves it, RE 0x526216 reads it) and both entry points pass zero, so this is the branch they take.
 */
double windowSpanLength(const lcns::dll::WindowSlots& window, const void* boxBase, bool hasGeometry);
double windowSpanHeight(const lcns::dll::WindowSlots& window, const void* boxBase, bool hasGeometry);
void copyPair38(void* destination, const void* element);   // RE 0x5203D0 -- first argument is the destination, per RCX/RDX: the pair at +0x38 and +0x40
void copyPair28(void* destination, const void* element);   // RE 0x5203F0 -- first argument is the destination, per RCX/RDX: the pair at +0x28 and +0x30




/** One turn in the angle units 0x5D3EA0 uses: RE 0x9DE950 is 3.6e12 and RE 0x5D3F42 subtracts multiples of it. */
constexpr double kAngleUnitsPerTurn = 3600000000000.0;

/** The four remainders 0x5D3EA0 special cases, at RE 0x5D3F45, 0x5D3F58, 0x5D3F6B and 0x5D3F7E. */
constexpr long long kAngleAxisZero = 0LL;
constexpr long long kAngleAxisQuarter = 0xD18C2E2800LL;       //  900000000000, a quarter turn
constexpr long long kAngleAxisHalf = 0x1A3185C5000LL;         // 1800000000000, a half turn
constexpr long long kAngleAxisThreeQuarter = 0x274A48A7800LL; // 2700000000000, three quarters

/**
 * True when the angle lands exactly on an axis, in which case the sine and cosine are exact values rather than the
 * trigonometry result. RE 0x5D3F45 and its three siblings branch away from 0x634CA0 for exactly these four remainders.
 *
 * The zero that is written is the NEGATIVE zero at RE 0x9DE948, so the sign is part of the answer: a caller can observe
 * it through division and through the sign bit, and this project has already had to fix one signed zero divergence, in
 * the affine inverse, so the test compares bits rather than values.
 */
bool axisSinCos(long long angleUnits, double* sine, double* cosine);

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
