// tests/test_row.cpp -- Row::Squeezer cost path (RE: 0x1380D0, 0x13A360, 0x5C22D0).
#include "check.hpp"
#include "lcns/row.hpp"

using namespace lcns;
using namespace lcns::row;

namespace {

// Builds a context whose two slots are aligned (so the 0.005 gate passes) and whose A direction
// makes the given angle with the +x axis.
SqueezeContext makeContext(double angleDegrees, double threshold, double aWidth, double bWidth) {
    SqueezeContext ctx;
    ctx.enabled = true;
    ctx.threshold = threshold;

    const double r = angleDegrees * 3.14159265358979323846 / 180.0;
    const double ux = std::cos(r);
    const double uy = std::sin(r);

    // A: from (0,0) to (ux,uy) -- v0/v1 is the start, v2/v3 the end
    ctx.loSlot.present = true;
    ctx.loSlot.value.v[0] = 0.0;
    ctx.loSlot.value.v[1] = 0.0;
    ctx.loSlot.value.v[2] = ux;
    ctx.loSlot.value.v[3] = uy;

    // B: same direction, placed one unit along +x; |B.v0-B.v2| is what the max() sees
    ctx.hiSlot.present = true;
    ctx.hiSlot.value.v[0] = bWidth;
    ctx.hiSlot.value.v[1] = 0.0;
    ctx.hiSlot.value.v[2] = bWidth + ux;
    ctx.hiSlot.value.v[3] = uy;

    // the two interval lists: equal length and element-wise aligned within 0.005
    ctx.loList.items.resize(2);
    ctx.hiList.items.resize(2);
    for (std::size_t i = 0; i < 2; ++i) {
        ctx.loList.items[i].v[0] = 10.0 * static_cast<double>(i);
        ctx.loList.items[i].v[2] = 10.0 * static_cast<double>(i) + 1.0;
        ctx.hiList.items[i].v[0] = ctx.loList.items[i].v[0] + 0.001;   // inside 0.005
        ctx.hiList.items[i].v[2] = ctx.loList.items[i].v[2] - 0.001;
    }
    (void)aWidth;
    return ctx;
}

}  // namespace

int main() {
    // --- directionSine: the four cardinal angles are exact, matching 0xD18C2E2800 etc. ---
    {
        CHECK_NEAR(directionSine(1.0, 0.0), 0.0, 1e-12);
        CHECK_NEAR(directionSine(0.0, 1.0), 1.0, 1e-12);
        CHECK_NEAR(directionSine(-1.0, 0.0), 0.0, 1e-12);
        CHECK_NEAR(directionSine(0.0, -1.0), -1.0, 1e-12);
        // a non cardinal angle is the plain sine
        CHECK_NEAR(directionSine(std::cos(0.5), std::sin(0.5)), std::sin(0.5), 1e-9);
        CHECK_NEAR(directionSine(std::cos(2.5), std::sin(2.5)), std::sin(2.5), 1e-9);
    }

    // --- cost = threshold / sin(angle) - max(|A.v0-A.v2|, |B.v0-B.v2|) ---
    // Both slots are unit segments starting at x = 0, so their x extent is |cos(angle)|.
    {
        const double deg = 3.14159265358979323846 / 180.0;

        // 90 degrees: sin = 1 and cos = 0, so the cost is exactly the threshold
        SqueezeContext ctx = makeContext(90.0, 10.0, 0.0, 3.0);
        const SqueezeResult r = squeezeCost(ctx);
        CHECK(r.present);
        CHECK_NEAR(r.value, 10.0, 1e-9);

        // 30 degrees: 10 / sin30 - |cos30|
        ctx = makeContext(30.0, 10.0, 0.0, 0.0);
        const SqueezeResult r30 = squeezeCost(ctx);
        CHECK(r30.present);
        CHECK_NEAR(r30.value, 10.0 / std::sin(30.0 * deg) - std::fabs(std::cos(30.0 * deg)), 1e-9);

        // 60 degrees, B moved to start at -4: the extent term is |cos60| = 0.5
        ctx = makeContext(60.0, 12.0, 0.0, 0.0);
        ctx.hiSlot.value.v[0] = -4.0;
        ctx.hiSlot.value.v[2] = -4.0 + std::cos(60.0 * deg);
        const SqueezeResult rb = squeezeCost(ctx);
        CHECK(rb.present);
        CHECK_NEAR(rb.value, 12.0 / std::sin(60.0 * deg) - std::fabs(std::cos(60.0 * deg)), 1e-9);

        // max() picks the WIDER of the two: make B a length 2 segment in the same direction, so
        // its x extent is 2*|cos60| = 1.0 while A's stays 0.5
        ctx = makeContext(60.0, 12.0, 0.0, 0.0);
        ctx.hiSlot.value.v[0] = -4.0;
        ctx.hiSlot.value.v[2] = -4.0 + 2.0 * std::cos(60.0 * deg);
        ctx.hiSlot.value.v[3] = 2.0 * std::sin(60.0 * deg);
        const SqueezeResult rwide = squeezeCost(ctx);
        CHECK(rwide.present);
        CHECK_NEAR(rwide.value, 12.0 / std::sin(60.0 * deg) - 1.0, 1e-9);
        // ... and the wider term really came from B
        CHECK(std::fabs(2.0 * std::cos(60.0 * deg)) >
              std::fabs(std::cos(60.0 * deg)));
    }

    // --- the parallelism gate: non parallel rows are NOT applicable ---
    {
        SqueezeContext ctx = makeContext(90.0, 10.0, 0.0, 0.0);
        // rotate B's direction by 30 degrees (its extents stay inside the 0.005 gate because
        // the gate looks at v0/v2 of the *lists*, not of the slots)
        const double deg = 3.14159265358979323846 / 180.0;
        ctx.hiSlot.value.v[0] = 0.0;
        ctx.hiSlot.value.v[2] = std::cos(120.0 * deg);
        ctx.hiSlot.value.v[3] = std::sin(120.0 * deg);
        const SqueezeResult r = squeezeCost(ctx);
        CHECK_MSG(!r.present, "0x1385C9: |cross| > 1e-6 must fall through to *out = 0");

        // parallel again -> applicable
        ctx.hiSlot.value.v[2] = std::cos(90.0 * deg);
        ctx.hiSlot.value.v[3] = std::sin(90.0 * deg);
        CHECK(squeezeCost(ctx).present);
    }

    // --- the bails: each one reports present == false, exactly like the recovered paths ---
    {
        SqueezeContext ctx = makeContext(90.0, 10.0, 0.0, 0.0);

        SqueezeContext off = ctx;
        off.enabled = false;                        // [obj+8] == 0
        CHECK(!squeezeCost(off).present);

        SqueezeContext noSlot = ctx;
        noSlot.loSlot.present = false;              // 0x134FA0 returned absent
        CHECK(!squeezeCost(noSlot).present);

        SqueezeContext noSlot2 = ctx;
        noSlot2.hiSlot.present = false;
        CHECK(!squeezeCost(noSlot2).present);

        SqueezeContext lenMismatch = ctx;           // 0x13861C: list lengths must match
        lenMismatch.hiList.items.pop_back();
        CHECK(!squeezeCost(lenMismatch).present);

        SqueezeContext misaligned = ctx;            // 0.005 gate on element v0
        misaligned.hiList.items[1].v[0] += 0.01;
        CHECK(!squeezeCost(misaligned).present);

        SqueezeContext misaligned2 = ctx;           // 0.005 gate on element v2
        misaligned2.hiList.items[0].v[2] += 0.02;
        CHECK(!squeezeCost(misaligned2).present);

        SqueezeContext zeroLen = ctx;               // RE asserts `distance != 0`
        zeroLen.loSlot.value.v[2] = zeroLen.loSlot.value.v[0];
        zeroLen.loSlot.value.v[3] = zeroLen.loSlot.value.v[1];
        CHECK(!squeezeCost(zeroLen).present);

        // alignment just inside the tolerance still passes
        SqueezeContext inside = ctx;
        inside.hiList.items[0].v[0] += 0.004;
        CHECK(squeezeCost(inside).present);
    }

    // --- Squeezer: the address-keyed memo, hit predicate lo <= keyLo && hi <= keyHi ---
    {
        Squeezer sq;
        const SqueezeContext ctx = makeContext(90.0, 8.0, 0.0, 0.0);

        CHECK(sq.entries() == 0);
        const double first = sq.cost(0x2000, 0x2100, ctx);
        CHECK_NEAR(first, 8.0, 1e-9);
        CHECK(sq.misses() == 1);
        CHECK(sq.hits() == 0);
        CHECK(sq.entries() == 1);

        // an entry with keyLo=0x2000, keyHi=0x2100 covers a query with lo<=keyLo and hi<=keyHi
        const double again = sq.cost(0x1F00, 0x2050, ctx);
        CHECK_NEAR(again, first, 1e-12);
        CHECK(sq.hits() == 1);
        CHECK(sq.entries() == 1);

        // a query to the right is not covered -> a second entry is inserted
        const double third = sq.cost(0x3000, 0x3100, ctx);
        CHECK_NEAR(third, first, 1e-12);
        CHECK(sq.entries() == 2);
        CHECK(sq.misses() == 2);

        sq.clear();
        CHECK(sq.entries() == 0);
        CHECK(sq.hits() == 0);
    }

    // --- a not-applicable evaluation is not cached (0x13A3D1 jumps out before the insert) ---
    {
        Squeezer sq;
        SqueezeContext ctx = makeContext(90.0, 8.0, 0.0, 0.0);
        ctx.hiList.items.pop_back();
        CHECK_NEAR(sq.cost(0x1000, 0x1100, ctx), 0.0, 1e-12);
        CHECK(sq.entries() == 0);
        CHECK(sq.misses() == 1);
    }

    // --- buildSqueezer: RE 0x13C380 / 0x138A20 ---
    {
        // The constructor's three scalars come straight from the recovered stores.
        const Squeezer s(3.0, 0.25, 7.5);
        CHECK(s.enabled());                    // RE: inner[+8] = 1 @0x138A6B
        CHECK_NEAR(s.threshold(), 7.5, 1e-12); // RE: inner[+0x10] = xmm3
        CHECK_NEAR(s.coeff(), 0.25, 1e-12);    // RE: inner[+0x00] = xmm2
        CHECK_NEAR(s.twiceMaxExtent(), 3.0, 1e-12);

        // A single invalid row: contribution = 2 * max(|v3-v1|, |v2-v0|) = 2 * max(4, 1) = 8
        std::vector<RowView> rows(1);
        rows[0].skipExtent = false;
        rows[0].v[0] = 0.0;
        rows[0].v[1] = 0.0;
        rows[0].v[2] = 1.0;
        rows[0].v[3] = 4.0;
        Squeezer b = buildSqueezer(rows, 7.5, 0.25);
        CHECK_NEAR(b.twiceMaxExtent(), 8.0, 1e-12);
        CHECK_NEAR(b.threshold(), 7.5, 1e-12);   // xmm9 = config[+0x10]
        CHECK_NEAR(b.coeff(), 0.25, 1e-12);      // xmm8 = config[+0x18]

        // The doubling does NOT take an absolute value: the signed max is used
        rows[0].v[2] = -1.0;
        rows[0].v[3] = -4.0;
        // d0 = -4 - 0 = -4 ; d1 = -1 - 0 = -1 ; max = -1 ; contribution = -2
        CHECK_NEAR(buildSqueezer(rows, 0.0, 0.0).twiceMaxExtent(), -2.0, 1e-12);

        // 0x13C46F is an ASSIGNMENT, not a maximum: the LAST row wins, and a valid row
        // contributes 0 (because 0x13C438 sets xmm1 = 0 before the branch).
        rows.assign(2, RowView{});
        rows[0].skipExtent = false;
        rows[0].v[3] = 100.0;                    // would dominate under a max()
        rows[1].skipExtent = false;
        rows[1].v[2] = 1.0;
        rows[1].v[3] = 2.0;                      // 2 * max(2, 1) = 4
        CHECK_NEAR(buildSqueezer(rows, 0.0, 0.0).twiceMaxExtent(), 4.0, 1e-12);

        rows[1].skipExtent = true;                    // a last row with the flag set resets the value to 0 (non zero means skip)
        CHECK_NEAR(buildSqueezer(rows, 0.0, 0.0).twiceMaxExtent(), 0.0, 1e-12);

        // an empty row set leaves the initial 0
        CHECK_NEAR(buildSqueezer(std::vector<RowView>{}, 0.0, 0.0).twiceMaxExtent(), 0.0, 1e-12);
    }

    // --- the per-candidate score (RE 0x136C00 layout, 0x134F30, 0x136CB0) ---
    {
        // 0x134F30 / 0x134F50: the node's X and Y extents; the +0x18 flag zeroes both
        ScoreNode n;
        n.minX = 3.0;
        n.maxX = 11.0;   // X extent 8
        n.minY = -1.0;
        n.maxY = 2.5;    // Y extent 3.5
        CHECK_NEAR(nodeLength(n), 8.0, 1e-12);
        CHECK_NEAR(nodeLengthY(n), 3.5, 1e-12);
        n.degenerate = true;
        CHECK_NEAR(nodeLength(n), 0.0, 1e-12);
        CHECK_NEAR(nodeLengthY(n), 0.0, 1e-12);
        n.degenerate = false;

        // 0x134F90 / 0x135010: the two flag pairs, selected by a bool
        n.flag40 = 7;
        n.flag41 = 9;
        n.flag98 = 1;
        n.flag99 = 0;
        CHECK(nodeFlag40(n, false) == 7);
        CHECK(nodeFlag40(n, true) == 9);
        CHECK(nodeFlag98(n, false) == 1);
        CHECK(nodeFlag98(n, true) == 0);

        // 0x136CB0: an empty container scores 0 ...
        CHECK_NEAR(candidateScore({}), 0.0, 1e-12);

        // ... otherwise the LAST element decides: len(last.node) + last.value
        ScoreNode first;
        first.minX = 0.0;
        first.maxX = 100.0;            // would give 100 if the first element were used
        ScoreNode last;
        last.minX = 1.0;
        last.maxX = 4.5;               // len = 3.5
        std::vector<ScoreRecord> recs;
        recs.push_back(ScoreRecord{&first, 1000.0});
        recs.push_back(ScoreRecord{&last, 2.0});   // 3.5 + 2.0 = 5.5
        CHECK_NEAR(candidateScore(recs), 5.5, 1e-12);
        // a null node counts as a zero length
        recs.back().node = nullptr;
        CHECK_NEAR(candidateScore(recs), 2.0, 1e-12);

        // the memo only recomputes while the cache is exactly kScoreUnset (-1.0)
        LazyScorer scorer;
        CHECK(!scorer.computed());
        CHECK_NEAR(scorer.cached(), kScoreUnset, 1e-12);
        recs.back().node = &last;
        CHECK_NEAR(scorer.score(recs), 5.5, 1e-12);   // computed once
        CHECK(scorer.computed());
        recs.back().value = 42.0;                     // changing the data does NOT invalidate
        CHECK_NEAR(scorer.score(recs), 5.5, 1e-12);
        scorer.invalidate();
        CHECK_NEAR(scorer.score(recs), 45.5, 1e-12);  // 3.5 + 42.0

        // RE 0x137800 "orderedAddElement": appending a record resets the cache itself (0x137877)
        ScoreNode extra;
        extra.minX = 10.0;
        extra.maxX = 13.0;             // len 3
        orderedAddElement(recs, scorer, &extra, 1.0);   // 3 + 1 = 4
        CHECK(!scorer.computed());                      // the append invalidated it
        CHECK_NEAR(scorer.score(recs), 4.0, 1e-12);     // the new LAST element decides
        CHECK(recs.size() == 3);
    }

    // --- RE 0x5C2E40: the authorisation predicate over 24 byte records ---
    {
        std::vector<AuthRecord> recs;
        AuthRecord r0;
        r0.tag = 3;
        r0.lo = 10;
        r0.hi = 20;
        recs.push_back(r0);
        AuthRecord r1;                 // a reversed interval: lo > hi
        r1.tag = 5;
        r1.lo = 90;
        r1.hi = 30;
        recs.push_back(r1);

        CHECK(authorized(recs, 3, 10));      // the inclusive lower end
        CHECK(authorized(recs, 3, 20));      // the inclusive upper end
        CHECK(authorized(recs, 3, 15));
        CHECK(!authorized(recs, 3, 9));
        CHECK(!authorized(recs, 3, 21));
        CHECK(!authorized(recs, 4, 15));     // the tag must match
        CHECK(authorized(recs, 5, 95));      // the reversed form: v >= lo
        CHECK(authorized(recs, 5, 20));      // ... or v <= hi
        CHECK(!authorized(recs, 5, 50));     // inside the gap is rejected
        CHECK(!authorized({}, 3, 15));       // the empty container (RE: 0x5C2EC0)
    }

    // --- RE 0x5CEE50 (tag == 0 path): angle -> {cos, -sin, sin, cos, 0, 0} ---
    {
        const AngleTransform z = angleTransform(0);
        CHECK_NEAR(z.cos, 1.0, 0.0);
        CHECK(z.negSin == 0.0 && std::signbit(z.negSin));   // RE: 0x9DE948 is -0.0
        CHECK_NEAR(z.sin, 0.0, 0.0);
        CHECK_NEAR(z.cos2, 1.0, 0.0);
        CHECK_NEAR(z.zero20, 0.0, 0.0);
        CHECK_NEAR(z.zero28, 0.0, 0.0);

        const AngleTransform d90 = angleTransform(0xD18C2E2800ll);
        CHECK_NEAR(d90.cos, 0.0, 0.0);
        CHECK_NEAR(d90.negSin, -1.0, 0.0);
        CHECK_NEAR(d90.sin, 1.0, 0.0);

        const AngleTransform d180 = angleTransform(0x1A3185C5000ll);
        CHECK_NEAR(d180.cos, -1.0, 0.0);
        CHECK(d180.negSin == 0.0 && std::signbit(d180.negSin));
        CHECK_NEAR(d180.sin, 0.0, 0.0);

        const AngleTransform d270 = angleTransform(0x274A48A7800ll);
        CHECK_NEAR(d270.cos, 0.0, 0.0);
        CHECK_NEAR(d270.negSin, 1.0, 0.0);
        CHECK_NEAR(d270.sin, -1.0, 0.0);

        // the general path splits the angle into radians and takes cos/sin
        const AngleTransform g = angleTransform(900000000000ll);   // 90 degrees
        CHECK_NEAR(g.sin, 1.0, 1e-12);
        CHECK_NEAR(g.cos, 0.0, 1e-12);
        CHECK_NEAR(g.negSin, -1.0, 1e-12);
        // the fixed point angle wraps (RE: the modulo magic 0x9C5FFF26ED75ED55)
        const AngleTransform wrapped = angleTransform(0xD18C2E2800ll + 3600000000000ll);
        CHECK_NEAR(wrapped.sin, 1.0, 0.0);
    }

    // --- RE 0x134470: keep the minimum score among the authorised candidates ---
    {
        std::vector<AuthRecord> recs;
        AuthRecord r;
        r.tag = 1;
        r.lo = 0;
        r.hi = 1000;
        recs.push_back(r);

        std::vector<CandidateElement> els(3);
        els[0].tag = 1;
        els[0].angle = 0;
        els[1].tag = 1;
        els[1].angle = 90;
        els[2].tag = 9;      // rejected by the predicate
        els[2].angle = 0;

        const double scores[3] = {5.0, 2.5, -100.0};
        double best = 0.0;
        const int idx = bestCandidate(els, recs,
                                      [&](const CandidateElement& e) {
                                          return scores[&e - els.data()];
                                      },
                                      &best);
        CHECK(idx == 1);           // the smallest accepted score
        CHECK_NEAR(best, 2.5, 1e-12);

        // nothing authorised -> -1, and the first best wins on a tie
        std::vector<AuthRecord> none;
        CHECK(bestCandidate(els, none, [](const CandidateElement&) { return 1.0; }, &best) == -1);
    }

    // --- RE 0x5D38C0: the affine transform and the candidate's height/width ---
    {
        // 90 degrees rotates (1,0) onto (0,1) and (0,1) onto (-1,0)
        const AngleTransform t90 = angleTransform(0xD18C2E2800ll);
        CHECK_NEAR(transformX(t90, 1.0, 0.0), 0.0, 1e-12);
        CHECK_NEAR(transformY(t90, 1.0, 0.0), 1.0, 1e-12);
        CHECK_NEAR(transformX(t90, 0.0, 1.0), -1.0, 1e-12);
        CHECK_NEAR(transformY(t90, 0.0, 1.0), 0.0, 1e-12);
        // the determinant is cos^2 + sin^2 = 1 for every recovered branch
        CHECK_NEAR(transformDet(t90), 1.0, 1e-12);
        CHECK_NEAR(transformDet(angleTransform(0)), 1.0, 1e-12);
        CHECK_NEAR(transformDet(angleTransform(0x1A3185C5000ll)), 1.0, 1e-12);
        CHECK_NEAR(transformDet(angleTransform(0x274A48A7800ll)), 1.0, 1e-12);

        // a 2 x 1 box: unrotated its height is 1, rotated by 90 degrees it becomes 2
        std::vector<geom::FPoint> box;
        const geom::fixed_t sx = geom::toFixed(1.0);
        const geom::fixed_t sy = geom::toFixed(2.0);
        box.push_back(geom::FPoint{0, 0});
        box.push_back(geom::FPoint{sx, 0});
        box.push_back(geom::FPoint{sx, sy});
        box.push_back(geom::FPoint{0, sy});
        CHECK_NEAR(transformedHeight(box, angleTransform(0)), 2.0, 1e-9);
        CHECK_NEAR(transformedWidth(box, angleTransform(0)), 1.0, 1e-9);
        const AngleTransform t90b = angleTransform(0xD18C2E2800ll);
        CHECK_NEAR(transformedHeight(box, t90b), 1.0, 1e-9);
        CHECK_NEAR(transformedWidth(box, t90b), 2.0, 1e-9);
        // ... and the value 0x133DE0 hands to the Squeezer is 20 * that height
        CHECK_NEAR(candidateSqueezerArg(transformedHeight(box, angleTransform(0))), 40.0, 1e-9);
        CHECK_NEAR(transformedHeight({}, t90b), 0.0, 0.0);
    }

    // --- RE 0x137FE0: the drain loop over source records ---
    {
        CHECK(kSourceRecordCap == 10000);   // RE 0x271000000000, the u32 at record+0x0c

        // a record with a zero count is skipped entirely (RE: 0x138013)
        std::vector<SourceRecord> recs(2);
        recs[0].count = 0;
        recs[1].count = 3;
        int calls = 0;
        drainSources(recs, [&](std::uintptr_t, unsigned char) { ++calls; return true; });
        CHECK(calls == 3);                  // only the second record drains, exactly its cap

        // a merge that reports "nothing more" stops that record early (RE: 0x13805A)
        calls = 0;
        drainSources(recs, [&](std::uintptr_t, unsigned char) { return ++calls < 2; });
        CHECK(calls == 2);

        // a count of one calls the merge exactly once
        std::vector<SourceRecord> one(1);
        one[0].count = 1;
        calls = 0;
        drainSources(one, [&](std::uintptr_t, unsigned char) { ++calls; return true; });
        CHECK(calls == 1);

        // the tag and source reach the merge unchanged
        std::vector<SourceRecord> tagged(1);
        tagged[0].source = 0x1234;
        tagged[0].tag = 7;
        tagged[0].count = 1;
        unsigned char seenTag = 0;
        std::uintptr_t seenSrc = 0;
        drainSources(tagged, [&](std::uintptr_t s, unsigned char t) {
            seenSrc = s;
            seenTag = t;
            return false;
        });
        CHECK(seenSrc == 0x1234);
        CHECK(seenTag == 7);
    }

    // --- the element/Item layout constants (RE 0x136350 / 0x1333D0 / 0x1331A0) ---
    {
        CHECK(sizeof(ScoreNode) == kScoreNodeSize);   // the 216 byte element 0x137A90 walks
        CHECK(kScoreNodeSize == 0xd8);
        CHECK(kItemSize == 0x90);
        CHECK(itemContainerOffset(false) == 0x58);    // RE: 0x1331A0 dl == 0
        CHECK(itemContainerOffset(true) == 0x70);     // RE: 0x1331A0 dl != 0
        CHECK(kItemSubObject == 0x20);                // RE: 0x1333C0
        // the constructor 0x136350 leaves the element degenerate until 0x5CD800 fills its box
        ScoreNode fresh;
        CHECK(!fresh.degenerate);                     // the field default, not the binary's init
        CHECK(fresh.sourceTagQword == 0);
        CHECK(fresh.sourceAngle == 0);
    }

    // --- RE 0x137BF0..0x137C83: the final score arithmetic ---
    {
        // the excess branch (137C40 falls through): a > b, so cost absorbs (a - b)
        // a = recordValue + prevExtent + axis = 1 + 2 + 3 = 6
        // b = lazyScore + squeezeCost      = 1 + 2     = 3
        // cost = 2 + (6 - 3) = 5 ; score = 5 - (10 / 2) = 0
        CHECK_NEAR(elementScore(/*squeezeCost*/ 2.0, /*lazy*/ 1.0, /*record*/ 1.0,
                                /*prevExtent*/ 2.0, /*axis*/ 3.0,
                                /*elementAtA0*/ 10.0, /*objAt0x08*/ 2.0),
                  0.0, 1e-12);
        // the jbe branch (a <= b): the cost is untouched
        // a = 1 + 1 + 1 = 3 ; b = 5 + 2 = 7 ; cost stays 2 ; score = 2 - 2 = 0
        CHECK_NEAR(elementScore(2.0, 5.0, 1.0, 1.0, 1.0, 4.0, 2.0), 0.0, 1e-12);
        // equal operands take the jbe branch too (the comparison is `jbe`, not `jb`)
        CHECK_NEAR(elementScore(2.0, 5.0, 1.0, 1.0, 3.0, 4.0, 2.0), 0.0, 1e-12);
    }

    // --- the score chain end to end, using only recovered primitives ---
    {
        // a 2x1 box, the 90 degree candidate: height 1 -> the Squeezer argument 20
        std::vector<geom::FPoint> box;
        const geom::fixed_t sx = geom::toFixed(1.0);
        const geom::fixed_t sy = geom::toFixed(2.0);
        box.push_back(geom::FPoint{0, 0});
        box.push_back(geom::FPoint{sx, 0});
        box.push_back(geom::FPoint{sx, sy});
        box.push_back(geom::FPoint{0, sy});
        const AngleTransform t = angleTransform(0xD18C2E2800ll);      // 90 degrees
        const double h = transformedHeight(box, t);
        CHECK_NEAR(candidateSqueezerArg(h), 20.0, 1e-9);              // 20 * 1

        // the SqueezeContext built from two ScoreNodes, with the threshold from that argument
        ScoreNode lo;
        lo.minX = 0.0; lo.maxX = 10.0; lo.minY = 0.0; lo.maxY = 1.0;
        ScoreNode hi;
        hi.minX = 0.0; hi.maxX = 10.0; hi.minY = 0.0; hi.maxY = 1.0;
        SqueezeContext ctx;
        ctx.threshold = candidateSqueezerArg(h);
        ctx.enabled = true;
        // the two slots the Squeezer reads are the nodes' +0x48 / +0x70 optionals
        ctx.loSlot.present = false;   // an absent slot makes the cost "not applicable"
        ctx.hiSlot.present = false;
        Squeezer sq;
        CHECK_NEAR(sq.cost(reinterpret_cast<std::uintptr_t>(&lo),
                           reinterpret_cast<std::uintptr_t>(&hi), ctx), 0.0, 1e-12);
        CHECK(sq.misses() == 1);      // evaluated once, not cached (not applicable)
        CHECK(sq.entries() == 0);

        // with both slots present and the lists aligned, the recovered formula applies
        ctx.loSlot.present = true;
        ctx.hiSlot.present = true;
        ctx.loSlot.value.v[0] = 0.0; ctx.loSlot.value.v[1] = 0.0;
        ctx.loSlot.value.v[2] = 0.0; ctx.loSlot.value.v[3] = 1.0;   // a vertical direction
        ctx.hiSlot.value = ctx.loSlot.value;
        Squeezer sq2;
        const double v = sq2.cost(reinterpret_cast<std::uintptr_t>(&lo),
                                  reinterpret_cast<std::uintptr_t>(&hi), ctx);
        // cost = threshold / sin(90) - max(|v0-v2|, |v0-v2|) = 20 / 1 - 0 = 20
        CHECK_NEAR(v, 20.0, 1e-9);
        CHECK(sq2.entries() == 1);    // this one IS cached
    }

    // --- RE 0x5C4C50 / 0x8BEFC0 / 0x134470's setup: where the candidate angles come from ---
    {
        // 0x5C4C50 writes exactly one element: the tag at +0x00 and the angle at +0x08
        CandidateElement e;
        writeCandidateAngle(e, 3, 12345);
        CHECK(e.tag == 3);
        CHECK(e.angle == 12345);

        // 0x8BEFC0: the source elements followed by the one appended {tag, angle}
        std::vector<CandidateElement> src(2);
        src[0].tag = 1; src[0].angle = 100;
        src[1].tag = 2; src[1].angle = 200;
        const std::vector<CandidateElement> built = candidateAngles(src, 0, 0);
        CHECK(built.size() == 3);
        CHECK(built[0].tag == 1 && built[0].angle == 100);   // the source is preserved in order
        CHECK(built[1].tag == 2 && built[1].angle == 200);
        CHECK(built[2].tag == 0 && built[2].angle == 0);     // the appended one

        // 0x134470's own setup: source angles, then 0 degrees, then 90 degrees, all tagged 0
        const std::vector<CandidateElement> cand = axisAlignedCandidates(src);
        CHECK(cand.size() == 4);
        CHECK(cand[2].tag == 0 && cand[2].angle == 0);
        CHECK(cand[3].tag == 0 && cand[3].angle == kAxisAngle90);
        CHECK(kAxisAngle90 == 0xD18C2E2800ll);
        // ... and the 90 degree entry is the one whose transform is the exact 90 degree branch
        const AngleTransform t = angleTransform(cand[3].angle);
        CHECK_NEAR(t.sin, 1.0, 0.0);
        CHECK_NEAR(t.cos, 0.0, 0.0);
    }

    // --- RE 0x1355C0 / 0x133190: the element remembers the candidate that produced it ---
    {
        ScoreNode n;
        n.owner = 0x1234;                       // [+0x00] the Item pointer (0x136371)
        n.sourceTagQword = 0x0000000000000007ull;   // [+0x08] the tag byte is the low byte
        n.sourceAngle = 0xD18C2E2800ll;             // [+0x10] 90 degrees
        CHECK(kItemGeometry == 0x08);           // RE: 0x133190 = `lea rax,[rcx+8]`
        CHECK(nodeSourceTag(n) == 7);           // RE: 0x5C4CD0(element + 8)
        CHECK(nodeSourceAngle(n) == 0xD18C2E2800ll);        // RE: 0x5C4CE0(element + 8)
        // 0x5CEE50(element + 8) is therefore the transform of the element's OWN angle
        const AngleTransform t = nodeAngleTransform(n);
        CHECK_NEAR(t.sin, 1.0, 0.0);            // the exact 90 degree branch
        CHECK_NEAR(t.cos, 0.0, 0.0);

        // a 0 degree element gives the identity rotation
        ScoreNode z;
        z.sourceAngle = 0;
        const AngleTransform tz = nodeAngleTransform(z);
        CHECK_NEAR(tz.cos, 1.0, 0.0);
        CHECK_NEAR(tz.sin, 0.0, 0.0);
    }

    // --- RE 0x5CF6B0 / 0x8C4FF0 / 0x5CE7F0: the two-point map, the strides, the half turn ---
    {
        // 0x5CF6B0 applies the same affine map as transformX/transformY
        const AngleTransform t90 = angleTransform(0xD18C2E2800ll);
        const FPoint2 a = transformPoint(t90, 1.0, 0.0);
        CHECK_NEAR(a.x, 0.0, 1e-12);
        CHECK_NEAR(a.y, 1.0, 1e-12);
        const FPoint2 b = transformPoint(t90, 0.0, 1.0);
        CHECK_NEAR(b.x, -1.0, 1e-12);
        CHECK_NEAR(b.y, 0.0, 1e-12);

        // the destructor 0x8C4FF0 walks 48 byte elements holding 24 byte records
        CHECK(kElem48Stride == 0x30);
        CHECK(kRecord18Stride == 0x18);
        CHECK(kRecord18Stride < kElem48Stride);

        // 0x5CE7F0 is the second instantiation; 0x136350 calls it with 180 degrees
        CHECK(kHalfTurn180 == 0x1A3185C5000ll);
        const AngleTransform h = halfTurn();
        CHECK_NEAR(h.cos, -1.0, 0.0);
        CHECK_NEAR(h.sin, 0.0, 0.0);
        CHECK(h.negSin == 0.0 && std::signbit(h.negSin));   // -0.0, as the branch sets it
        // so the element's stored mirror copy is the container reflected through the origin
        const FPoint2 m = transformPoint(h, 3.0, 4.0);
        CHECK_NEAR(m.x, -3.0, 1e-12);
        CHECK_NEAR(m.y, -4.0, 1e-12);
    }

    // --- RE 0x134D70: the +0x40/+0x41 flag predicate over a closed 16 byte point chain ---
    {
        CHECK(kElem16Stride == 0x10);            // RE: 0x134E57 `add rax, 0x10`
        CHECK(sizeof(Elem16) == 16);             // Elem16 is a 2D point
        CHECK_NEAR(kChainEpsilon, 1e-06, 0.0);   // RE: 0x9BCEE0

        // an empty chain returns true (RE: 0x134DEB je)
        const double node[3] = {0.0, 0.0, 0.0};
        std::vector<Elem16> empty;
        CHECK(chainMonotone(empty, node, 0.0));

        // a chain that never steps backwards is accepted
        std::vector<Elem16> flat;
        flat.push_back(Elem16{0.0, 0.0});
        flat.push_back(Elem16{1.0, 0.0});
        flat.push_back(Elem16{2.0, 0.0});
        CHECK(chainMonotone(flat, node, 0.0));

        // the false path (RE: 0x134EDD): the first point steps backwards in x with respect to the
        // LAST one while the y window is exceeded -- node = {0,1,1}, bboxMaxX = 0
        const double node2[3] = {0.0, 1.0, 1.0};
        std::vector<Elem16> back;
        back.push_back(Elem16{0.0, 5.0});
        back.push_back(Elem16{1.0, 0.0});
        back.push_back(Elem16{2.0, 0.0});
        CHECK(!chainMonotone(back, node2, 0.0));

        // chainFlags ANDs the per-chain answers (esi is never reset to 1)
        std::vector<std::vector<Elem16>> all;
        all.push_back(flat);
        CHECK(chainFlags(all, node, 0.0));
        all.push_back(back);
        CHECK(!chainFlags(all, node2, 0.0));
    }

    // --- RE 0x5CEE50's tag != 0 path (a reflection) and the +0x98/+0x99 slot flags ---
    {
        // tag 0 -> the rotation; tag != 0 -> the reflection (determinant -1)
        const AngleTransform rot = angleTransform(0xD18C2E2800ll);        // 90 degrees
        const AngleTransform mir = mirroredAngleTransform(0xD18C2E2800ll);
        CHECK_NEAR(rot.negSin, -1.0, 0.0);      // the rotation stores -sin at +0x08
        CHECK_NEAR(mir.negSin, 1.0, 0.0);       // the reflection stores +sin there
        CHECK_NEAR(mir.sin, 1.0, 0.0);          // ... and +sin at +0x10 too
        CHECK_NEAR(mir.cos, 0.0, 0.0);
        CHECK_NEAR(mir.cos2, 0.0, 0.0);         // -cos of 90 degrees
        CHECK_NEAR(transformDet(mir), -1.0, 1e-12);   // a reflection, not a rotation
        CHECK_NEAR(transformDet(rot), 1.0, 1e-12);
        // at 0 degrees the reflection is {1, 0, 0, -1}
        const AngleTransform m0 = mirroredAngleTransform(0);
        CHECK_NEAR(m0.cos, 1.0, 0.0);
        CHECK_NEAR(m0.sin, 0.0, 0.0);
        CHECK_NEAR(m0.cos2, -1.0, 0.0);

        // the dispatch inside 0x5CEE50: the element's tag picks rotation vs reflection
        ScoreNode n;
        n.sourceAngle = 0xD18C2E2800ll;
        n.sourceTagQword = 0;                          // tag 0
        CHECK_NEAR(nodeAngleTransform(n).negSin, -1.0, 0.0);
        n.sourceTagQword = 1;                          // tag != 0
        CHECK_NEAR(nodeAngleTransform(n).negSin, 1.0, 0.0);

        // +0x99: the first slot present and its outer values equal within 1e-06 (0x1366E0 setae)
        ScoreNode s;
        CHECK(!nodeSlotFlag99(s));                     // absent -> false
        s.slotAt48.present = true;
        s.slotAt48.value.v[0] = 2.0;
        s.slotAt48.value.v[2] = 2.0 + 1e-9;            // within the epsilon
        CHECK(nodeSlotFlag99(s));
        s.slotAt48.value.v[2] = 2.0 + 1e-3;            // outside it
        CHECK(!nodeSlotFlag99(s));
        // +0x98: the same shape on the second slot (0x1368A9: |[+0x88] - [+0x78]| <= 1e-06)
        CHECK(!nodeSlotFlag98(s));
        s.slotAt70.present = true;
        s.slotAt70.value.v[0] = 5.0;
        s.slotAt70.value.v[2] = 5.0 + 1e-9;            // within the epsilon
        CHECK(nodeSlotFlag98(s));
        s.slotAt70.value.v[2] = 5.0 + 1e-2;            // outside it
        CHECK(!nodeSlotFlag98(s));
        // ... and it only looks at v[0]/v[2], not at v[1]/v[3]
        s.slotAt70.value.v[2] = 5.0;
        s.slotAt70.value.v[1] = 123.0;
        s.slotAt70.value.v[3] = -456.0;
        CHECK(nodeSlotFlag98(s));
        // the two accessors resolve to *(Part+0x70) and *(Part+0x70)+0x90
        CHECK(kPartGeometryObject == 0x70);
        CHECK(kPartGeometryField == 0x90);
    }

    // --- RE 0x5C4950 / 0x4F7600 / 0x5C3F00: the auth table's units and the geometry accessor ---
    {
        // the table's lo/hi are ANGLES (0x5C4A45 / 0x5C4A4D come from 0x5C4CE0)
        CHECK(kPartGeometryVia == 0x70);            // RE: 0x4F7600 `mov rcx,[rcx+0x70]`
        CHECK(kAngleWrapMax == 0x34630B89FFFll);    // RE: 0x5C3F0A = 360e10 - 1
        std::vector<AuthRecord> table;
        table.push_back(makeAuthRecord(0, 0, 0x1A3185C5000ll));      // tag 0, [0, 180 degrees]
        // a 90 degree candidate with tag 0 is authorised, a 270 degree one is not
        CHECK(authorized(table, 0, 0xD18C2E2800ll));
        CHECK(!authorized(table, 0, 0x274A48A7800ll));
        // ... and the tag still has to match
        CHECK(!authorized(table, 1, 0xD18C2E2800ll));
        CHECK(authorized(table, 0, 0));                               // the inclusive lower end
        CHECK(authorized(table, 0, 0x1A3185C5000ll));                 // the inclusive upper end
    }

    // --- RE 0x5CC6A0 / 0x5C51A0 / 0x135C70: element+0xa0 is a ring AREA ---
    {
        CHECK_NEAR(kAreaHalf, 0.5, 0.0);          // RE: 0x9DE910
        // the shoelace closes the ring from the last point back to the first
        std::vector<Elem16> sq;
        sq.push_back(Elem16{0.0, 0.0});
        sq.push_back(Elem16{1.0, 0.0});
        sq.push_back(Elem16{1.0, 1.0});
        sq.push_back(Elem16{0.0, 1.0});
        CHECK_NEAR(dllArea(sq), 1.0, 1e-12);      // the unit square, CCW
        // reversing the order flips the sign (it is a signed area, no abs)
        std::vector<Elem16> rev(sq.rbegin(), sq.rend());
        CHECK_NEAR(dllArea(rev), -1.0, 1e-12);
        // an empty ring is 0 (RE: 0x5CC6DB je)
        CHECK_NEAR(dllArea({}), 0.0, 0.0);
        // a degenerate ring (all points equal) is 0
        std::vector<Elem16> deg(3, Elem16{2.0, 3.0});
        CHECK_NEAR(dllArea(deg), 0.0, 1e-12);
        // a triangle: (0,0),(4,0),(0,3) -> area 6
        std::vector<Elem16> tri;
        tri.push_back(Elem16{0.0, 0.0});
        tri.push_back(Elem16{4.0, 0.0});
        tri.push_back(Elem16{0.0, 3.0});
        CHECK_NEAR(dllArea(tri), 6.0, 1e-12);
        // the copy hop preserves the value (RE: 0x5C51A0 / 0x135FCE and 0x135FD6)
        CHECK_NEAR(nodeAreaValue(tri), 6.0, 1e-12);
    }

    // --- RE 0x5D3430 / 0x135040 / 0x135780: the last three sub-calls ---
    {
        // 0x5D3430 translates every 16 byte point by the displacement pair
        std::vector<Elem16> src;
        src.push_back(Elem16{1.0, 2.0});
        src.push_back(Elem16{-3.0, 4.0});
        const std::vector<Elem16> shifted = translatedCopy(src, 10.0, -1.0);
        CHECK(shifted.size() == src.size());
        CHECK_NEAR(shifted[0].x, 11.0, 1e-12);
        CHECK_NEAR(shifted[0].y, 1.0, 1e-12);
        CHECK_NEAR(shifted[1].x, 7.0, 1e-12);
        CHECK_NEAR(shifted[1].y, 3.0, 1e-12);
        // the source is untouched (0x5D3430 copies)
        CHECK_NEAR(src[0].x, 1.0, 1e-12);
        // translating by the negated box corner normalises a ring to the origin
        // (RE: 0x135620 xorpd -0.0 then 0x13562D)
        const std::vector<Elem16> norm = translatedCopy(src, -(-3.0), -(2.0));
        CHECK_NEAR(norm[0].x, 4.0, 1e-12);      // 1 - (-3)
        CHECK_NEAR(norm[0].y, 0.0, 1e-12);      // 2 - 2
        CHECK_NEAR(norm[1].x, 0.0, 1e-12);      // -3 - (-3)
        CHECK_NEAR(norm[1].y, 2.0, 1e-12);
        // a translation preserves the signed area
        CHECK_NEAR(dllArea(translatedCopy(src, 5.0, 7.0)), dllArea(src), 1e-9);

        // the two 0.005 constants are the same value at DIFFERENT rodata addresses
        CHECK_NEAR(kMergeAlignTolerance, 0.005, 0.0);        // RE: 0x9BCEE8 (0x135040)
        CHECK(kMergeAlignTolerance == kSqueezeAlignmentTolerance);
        CHECK_NEAR(kSqueezeAlignmentTolerance, 0.005, 0.0);  // RE: 0x9BCFD8 (the squeezer)
        CHECK(kTwoPointRecord == 0x20);                      // RE: 0x135A37..0x135A4B
    }

    return check::finish("test_row");
}
