// lcns/row.cpp -- Row::Squeezer cost path, translated from 0x1380D0 / 0x13A360.
#include "lcns/row.hpp"
#include "lcns/recovery.hpp"

#include <cmath>

LCNS_RECOVERED(module.row);
namespace lcns {
namespace row {
namespace {

constexpr double kTwoPi = 6.283185307179586;                        // 0x9DE758
constexpr double kFullTurnFixedDegrees = 3600000000000.0;           // 0x9DE740 / 0x34630B8A000

double hypot2(double x, double y) {
    // 0x138210 inlines `sqrtsd` and only falls back to libm (0x62FE20) for the edge cases
    const double s = x * x + y * y;
    return s >= 0.0 ? std::sqrt(s) : std::sqrt(s);
}

// The 0.005 gate: equal list lengths, and v0/v2 of every element pair within tolerance.
bool listsAlign(const IntervalList& a, const IntervalList& b) {
    if (a.items.size() != b.items.size()) return false;   // 0x13861C `sete al`
    for (std::size_t i = 0; i < a.items.size(); ++i) {
        if (std::fabs(a.items[i].v[0] - b.items[i].v[0]) > kSqueezeAlignmentTolerance) return false;
        if (std::fabs(a.items[i].v[2] - b.items[i].v[2]) > kSqueezeAlignmentTolerance) return false;
    }
    return true;
}

// RE: 0x134FA0 -- bool != 0 selects +0x48, bool == 0 selects +0x70.
const Slot& pickSlot(const SqueezeContext& ctx, bool upper) {
    return upper ? ctx.loSlot : ctx.hiSlot;
}

}  // namespace

double directionSine(double ux, double uy) {
    // 0x5C22D0 gives the fixed point angle, then 0x138771..0x13878F turn it back into radians and
    // take the sine, with the four cardinal angles handled by exact constants.
    const geom::fixed_t angle = geom::angleToFixedDegrees(ux, uy);
    if (angle == 0) return 0.0;                                   // 0x138736 -> sin 0
    if (angle == 0xD18C2E2800ll) return 1.0;                      // 90e10
    if (angle == 0x1A3185C5000ll) return 0.0;                     // 180e10
    if (angle == 0x274A48A7800ll) return -1.0;                    // 270e10
    return std::sin(kTwoPi * static_cast<double>(angle) / kFullTurnFixedDegrees);
}

SqueezeResult squeezeCost(const SqueezeContext& ctx) {
    SqueezeResult result;

    // 0x13810C: `cmp byte [rdx+8], 0` / jne -> the feature flag must be set
    if (!ctx.enabled) return result;

    // 0x138161 / 0x138177: the two optional slots; either being absent bails out
    const Slot& sa = pickSlot(ctx, true);    // 0x134FA0(lo, 1) -> +0x48
    const Slot& sb = pickSlot(ctx, false);   // 0x134FA0(hi, 0) -> +0x70
    if (!sa.present || !sb.present) return result;

    // 0x1385D0 / 0x1385DA then the 0x134FF0 pair and the 0.005 element-wise gate
    if (!listsAlign(ctx.loList, ctx.hiList)) return result;

    const Interval& a = sa.value;
    const Interval& b = sb.value;

    // 0x1381A6..0x138210: the direction of A and its length
    const double dax = a.v[2] - a.v[0];
    const double day = a.v[3] - a.v[1];
    const double lenA = hypot2(dax, day);
    if (lenA == 0.0) return result;          // RE: assert(lenA != 0) -- see the header note
    const double uax = dax / lenA;
    const double uay = day / lenA;

    // 0x1383C9..0x1383EF: the direction of B and its length
    const double dbx = b.v[2] - b.v[0];
    const double dby = b.v[3] - b.v[1];
    const double lenB = hypot2(dbx, dby);
    if (lenB == 0.0) return result;          // RE: assert(lenB != 0)
    const double ubx = dbx / lenB;
    const double uby = dby / lenB;

    // 0x1385A1..0x1385C9: cross product of the two unit directions. `ucomisd xmm1(1e-6), xmm0`
    // followed by `ja 0x1386F3` means: when 1e-6 > |cross| the directions are PARALLEL and the
    // code takes the angle path; otherwise it falls through to the gate block, which ends at
    // 0x1386EE `jmp 0x138121` (= *out = 0). So the squeeze cost only applies to parallel rows.
    const double cross = uax * uby - uay * ubx;
    if (std::fabs(cross) > kSqueezeParallelTolerance) return result;
    const double s = directionSine(uax, uay);   // 0x1386F3 -> 0x5C22D0 -> the sin block

    // 0x1387C5..0x1387DB: cost = threshold / sin - max(|A.v0-A.v2|, |B.v0-B.v2|)
    const double m = std::max(std::fabs(a.v[0] - a.v[2]), std::fabs(b.v[0] - b.v[2]));
    result.value = ctx.threshold / s - m;    // 0x1387D6 (divsd) + 0x1387DB (subsd)
    result.present = true;                   // 0x1387E4 / 0x1387E9
    return result;
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// RE 0x138A20: the constructor installs the vtable, ALLOCATES the 0x270 byte object and stores it at +8, and touches nothing else of the
// Squeezer object. **So the three scalars are initialised in the Impl, not in the handle** -- which is what the declaration now says and what the
// instructions at 0x138A6B, 0x138A72 and 0x138A79 do.
Squeezer::Squeezer(double twiceMaxExtent, double coeffAt0x18, double thresholdAt0x10)
    : impl_(new Impl{true, coeffAt0x18, thresholdAt0x10, twiceMaxExtent}) {}

// RE: 0x13C380 -- how the per-row extent becomes the Squeezer's first argument.
Squeezer buildSqueezer(const std::vector<RowView>& rows, double configAt0x10,
                       double configAt0x18) {
    double extent = 0.0;      // RE: xmm6 = 0 before the loop (0x13C41C `movapd xmm6, xmm7`)
    for (const RowView& r : rows) {
        // RE: 0x13C438 `movapd xmm1, xmm7` sets the contribution to 0 BEFORE the branch, so a
        // valid row contributes 0 rather than leaving the previous value in place.
        double contribution = 0.0;
        if (!r.skipExtent) {                         // RE: 0x13C43C `jne` skips the arithmetic
            // NOTE: the original takes a plain signed max -- there is no fabs anywhere here.
            const double d0 = r.v[3] - r.v[1];       // RE: [rsp+0x40] - [rsp+0x30]
            const double d1 = r.v[2] - r.v[0];       // RE: [rsp+0x38] - [rsp+0x28]
            // RE: 0x13C456 `ucomisd xmm1, xmm0` + `jbe 0x13C4FF`; the taken side doubles the
            // larger of the two, i.e. `2 * max(d0, d1)`.
            contribution = 2.0 * (d0 > d1 ? d0 : d1);
        }
        // RE: 0x13C46F `movapd xmm6, xmm1` -- this is an ASSIGNMENT, not a maximum: the value
        // ends up being the contribution of the LAST row, valid ones resetting it to 0.
        extent = contribution;
    }
    // RE: `call 0x136B80(&squeezer, xmm6, xmm8, xmm9)` with xmm8 = cfg[+0x18], xmm9 = cfg[+0x10]
    return Squeezer(extent, configAt0x18, configAt0x10);
}

double Squeezer::cost(std::uintptr_t lo, std::uintptr_t hi, const SqueezeContext& ctx) {
    // 0x13A390..0x13A3A2: hit <=> lo <= entry.keyLo && hi <= entry.keyHi
    for (const Entry& e : cache_) {
        if (lo <= e.keyLo && hi <= e.keyHi) {
            ++hits_;
            return e.value;                  // RE: [node+0x30]
        }
    }
    // 0x13A3BB..0x13A3CC: miss -> evaluate 0x1380D0
    ++misses_;
    const SqueezeResult r = squeezeCost(ctx);
    if (!r.present) return 0.0;
    // 0x13A3FD: insert into the map at +0x240, then return the node's value
    Entry e;
    e.keyLo = lo;
    e.keyHi = hi;
    e.value = r.value;
    cache_.push_back(e);
    return r.value;
}

void Squeezer::clear() {
    cache_.clear();
    hits_ = 0;
    misses_ = 0;
}

}  // namespace row
}  // namespace lcns
