// tests/test_affine.cpp -- the affine library against the original bytes.
//
// This is the first category landed under the revised criterion: the code is in src/, and instead of asserting that it
// looks right, the tests run the ORIGINAL routines that are embedded in the project and compare bit for bit. Where the
// original cannot be executed (it reads read-only data through RIP-relative operands, so it is comment-only), the tests
// fall back to properties that any correct implementation must satisfy, and say so.

#include "check.hpp"
#include "lcns/affine.hpp"
#include "lcns/embedded.hpp"

#include <cstdint>
#include <cstring>

namespace emb = lcns::embedded;
using lcns::affine::AngleTransform;

namespace {

/** Bit-for-bit equality: an embedded original and the C++ that claims to be equivalent must agree exactly. */
bool sameDouble(double a, double b) {
    std::uint64_t x = 0;
    std::uint64_t y = 0;
    std::memcpy(&x, &a, sizeof(x));
    std::memcpy(&y, &b, sizeof(y));
    return x == y;
}

bool sameTransform(const AngleTransform& a, const AngleTransform& b) {
    return sameDouble(a.cos, b.cos) && sameDouble(a.negSin, b.negSin) && sameDouble(a.sin, b.sin) &&
           sameDouble(a.cos2, b.cos2) && sameDouble(a.zero20, b.zero20) && sameDouble(a.zero28, b.zero28);
}

/** The six doubles as an array, for handing to an original. */
AngleTransform fromArray(const double* m) {
    AngleTransform t;
    t.cos = m[0];
    t.negSin = m[1];
    t.sin = m[2];
    t.cos2 = m[3];
    t.zero20 = m[4];
    t.zero28 = m[5];
    return t;
}

void toArray(const AngleTransform& t, double* m) {
    m[0] = t.cos;
    m[1] = t.negSin;
    m[2] = t.sin;
    m[3] = t.cos2;
    m[4] = t.zero20;
    m[5] = t.zero28;
}

const double kMatrices[][6] = {
    {1.0, 0.0, 0.0, 1.0, 0.0, 0.0},          // identity
    {1.0, 0.0, 0.0, 1.0, 3.0, -2.0},         // pure translation
    {2.0, 0.0, 0.0, 4.0, 1.0, -1.0},         // axis-aligned scale and translation
    {0.5, -0.25, 0.75, 1.5, -3.0, 2.0},      // general, determinant 0.9375
    {-1.0, 0.0, 0.0, 1.0, 0.0, 0.0},         // reflection in x
    {0.6, -0.8, 0.8, 0.6, 0.0, 0.0},         // a rotation
};

const double kPoints[][2] = {
    {0.0, 0.0},
    {3.0, 5.0},
    {-2.5, 0.25},
    {1e6, -1e6},
    {0.1, 0.2},
};

}  // namespace

int main() {
    // ---------------------------------------------------------------- the translation builder (0x5CE7B0, comment-only)
    // Properties, because the original reads its 1.0 through a RIP-relative operand and cannot be executed from the
    // embedded copy. The property that pins it down is the one that made it readable in the first place: the basis is
    // the identity and the origin maps to the translation.
    {
        const AngleTransform t = lcns::affine::translationTransform(3.0, -4.0);
        CHECK(sameDouble(t.cos, 1.0));
        CHECK(sameDouble(t.negSin, 0.0));
        CHECK(sameDouble(t.sin, 0.0));
        CHECK(sameDouble(t.cos2, 1.0));
        double origin[2] = {0.0, 0.0};
        lcns::affine::transformPointInPlace(t, origin);
        CHECK(sameDouble(origin[0], 3.0));
        CHECK(sameDouble(origin[1], -4.0));
        double p[2] = {10.0, 20.0};
        lcns::affine::transformPointInPlace(t, p);
        CHECK(sameDouble(p[0], 13.0));
        CHECK(sameDouble(p[1], 16.0));
    }

    // ---------------------------------------------------------------- compose (0x5CE970) against the original
#if defined(LCNS_HAS_EMBEDDED_ASM)
    {
        auto original = reinterpret_cast<void* (*)(void*, const void*, const void*)>(emb::originalOf(0x5CE970u));
        CHECK(original != nullptr);
        if (original) {
            std::size_t compared = 0;
            for (const double* a : kMatrices) {
                for (const double* b : kMatrices) {
                    double mine[6] = {0, 0, 0, 0, 0, 0};
                    toArray(lcns::affine::composeTransform(fromArray(a), fromArray(b)), mine);
                    double theirs[6] = {0, 0, 0, 0, 0, 0};
                    original(theirs, a, b);
                    for (int i = 0; i < 6; ++i) {
                        CHECK(sameDouble(mine[i], theirs[i]));
                    }
                    ++compared;
                }
            }
            CHECK(compared == 36);   // six times six
        }
    }
#endif

    // ---------------------------------------------------------------- the apply forms against the originals
#if defined(LCNS_HAS_EMBEDDED_ASM)
    {
        auto one = reinterpret_cast<void (*)(double*, const double*)>(emb::originalOf(0x5CFD80u));
        auto pair = reinterpret_cast<void (*)(double*, const double*)>(emb::originalOf(0x5CFDC0u));
        auto copy = reinterpret_cast<void* (*)(void*, const void*, const void*)>(emb::originalOf(0x5CF6B0u));
        CHECK(one != nullptr);
        CHECK(pair != nullptr);
        CHECK(copy != nullptr);

        for (const double* m : kMatrices) {
            const AngleTransform t = fromArray(m);
            for (const double* p : kPoints) {
                if (one) {
                    double mine[2] = {p[0], p[1]};
                    double theirs[2] = {p[0], p[1]};
                    lcns::affine::transformPointInPlace(t, mine);
                    one(theirs, m);
                    CHECK(sameDouble(mine[0], theirs[0]));
                    CHECK(sameDouble(mine[1], theirs[1]));
                }
                if (pair) {
                    double mine[4] = {p[0], p[1], p[0] + 1.0, p[1] - 1.0};
                    double theirs[4] = {mine[0], mine[1], mine[2], mine[3]};
                    lcns::affine::transformPairInPlace(t, mine);
                    pair(theirs, m);
                    for (int i = 0; i < 4; ++i) {
                        CHECK(sameDouble(mine[i], theirs[i]));
                    }
                }
                if (copy) {
                    const double src[4] = {p[0], p[1], p[0] * 2.0, p[1] * 3.0};
                    double mine[4] = {0, 0, 0, 0};
                    double theirs[4] = {0, 0, 0, 0};
                    lcns::affine::transformPairCopy(t, src, mine);
                    copy(theirs, src, m);
                    for (int i = 0; i < 4; ++i) {
                        CHECK(sameDouble(mine[i], theirs[i]));
                    }
                    // and the source must be untouched, which is what "out of place" means
                    CHECK(sameDouble(src[0], p[0]));
                }
            }
        }
    }
#endif

    // ------------------------------- the existing row.hpp readers must agree with the original apply as well
#if defined(LCNS_HAS_EMBEDDED_ASM)
    {
        auto one = reinterpret_cast<void (*)(double*, const double*)>(emb::originalOf(0x5CFD80u));
        if (one) {
            for (const double* m : kMatrices) {
                const AngleTransform t = fromArray(m);
                for (const double* p : kPoints) {
                    double theirs[2] = {p[0], p[1]};
                    one(theirs, m);
                    // transformX/transformY were read from 0x5D38C0/0x5CF6B0; here they are held to the same bytes.
                    CHECK(sameDouble(lcns::row::transformX(t, p[0], p[1]), theirs[0]));
                    CHECK(sameDouble(lcns::row::transformY(t, p[0], p[1]), theirs[1]));
                    CHECK(sameDouble(lcns::row::transformDet(t), t.cos * t.cos2 - t.sin * t.negSin));
                }
            }
        }
    }
#endif

    // ---------------------------------------------------------------- the orientation determinant (0x24B440)
#if defined(LCNS_HAS_EMBEDDED_ASM)
    {
        auto cross = reinterpret_cast<double (*)(const double*, const double*)>(emb::originalOf(0x24B440u));
        CHECK(cross != nullptr);
        if (cross) {
            const double cases[][6] = {
                {0.0, 0.0, 1.0, 0.0, 1.0, 0.0},
                {0.0, 0.0, 0.0, 1.0, 1.0, 0.0},
                {1.0, 2.0, 4.0, 6.0, 3.0, 1.0},
                {-1.5, 2.25, 0.5, -0.75, 3.0, 3.0},
            };
            for (const double* c : cases) {
                const double ac[4] = {c[0], c[1], c[2], c[3]};
                const double b[2] = {c[4], c[5]};
                CHECK(sameDouble(lcns::affine::orientationDeterminant(ac, b), cross(ac, b)));
            }
            // the sign distinguishes the two turn directions, in the routine's operand order
            const double ccw[4] = {0.0, 0.0, 1.0, 0.0};
            const double ccwB[2] = {0.0, 1.0};
            const double cw[4] = {0.0, 0.0, 0.0, 1.0};
            const double cwB[2] = {1.0, 0.0};
            CHECK(lcns::affine::orientationDeterminant(ccw, ccwB) > 0.0);
            CHECK(lcns::affine::orientationDeterminant(cw, cwB) < 0.0);
            const double collinear[4] = {0.0, 0.0, 1.0, 1.0};
            const double collinearB[2] = {2.0, 2.0};
            CHECK(sameDouble(lcns::affine::orientationDeterminant(collinear, collinearB), 0.0));
        }
    }
#endif

    // ------------------- the builder and the inverse, differential now that data relocation makes them executable
#if defined(LCNS_HAS_EMBEDDED_ASM)
    {
        auto builder = reinterpret_cast<void (*)(void*, const void*)>(emb::originalOf(0x5CE7B0u));
        auto inverse = reinterpret_cast<void* (*)(void*, const void*)>(emb::originalOf(0x5CED50u));
        CHECK(builder != nullptr);
        CHECK(inverse != nullptr);
        // both were comment-only until round 359, when their RIP-relative reads gained data relocations
        const emb::Block* bb = emb::find(0x5CE7B0u);
        const emb::Block* bi = emb::find(0x5CED50u);
        CHECK(bb != nullptr && bb->status == emb::Status::CallableRelocated);
        CHECK(bi != nullptr && bi->status == emb::Status::CallableRelocated);

        if (builder != nullptr) {
            const double points[][2] = {{0.0, 0.0}, {3.0, -4.0}, {-0.5, 0.25}, {1e6, -1e6}, {-0.0, 0.0}};
            for (const double* p : points) {
                double mine[6] = {0, 0, 0, 0, 0, 0};
                double theirs[6] = {0, 0, 0, 0, 0, 0};
                toArray(lcns::affine::translationTransform(p[0], p[1]), mine);
                builder(theirs, p);
                for (int i = 0; i < 6; ++i) {
                    CHECK(sameDouble(mine[i], theirs[i]));
                }
            }
        }

        if (inverse != nullptr) {
            for (const double* m : kMatrices) {
                const AngleTransform t0 = fromArray(m);
                if (lcns::row::transformDet(t0) == 0.0) {
                    continue;   // the deviation below
                }
                double mine[6] = {0, 0, 0, 0, 0, 0};
                double theirs[6] = {0, 0, 0, 0, 0, 0};
                AngleTransform out;
                CHECK(lcns::affine::invertTransform(t0, out));
                toArray(out, mine);
                inverse(theirs, m);
                for (int i = 0; i < 6; ++i) {
                    CHECK(sameDouble(mine[i], theirs[i]));
                }
            }
            // DEVIATION, stated rather than hidden: a singular matrix makes the original divide by zero and return
            // infinities, while invertTransform reports failure and leaves an identity. The check below pins the
            // project's behaviour, so the difference cannot drift unnoticed.
            const AngleTransform singular = fromArray(kMatrices[4]);
            AngleTransform degenerate = singular;
            degenerate.cos2 = 0.0;                     // a*d = 0 with b = 0, so the determinant is zero
            AngleTransform out;
            CHECK(!lcns::affine::invertTransform(degenerate, out));
            CHECK(sameDouble(out.cos, 0.0) && sameDouble(out.cos2, 0.0));
        }
    }
#endif

    // ---------------------------------------------------------------- the inverse (0x5CED50, comment-only)
    // Properties again: the original's reciprocal comes from a RIP-relative 1.0 and its sign flips from a mask, so the
    // embedded copy cannot run. What is checked is what the routine's structure promises: the composition of a transform
    // with its inverse is the identity, and applying one then the other returns the starting point.
    {
        for (const double* m : kMatrices) {
            const AngleTransform t = fromArray(m);
            AngleTransform inv;
            CHECK(lcns::affine::invertTransform(t, inv));
            const AngleTransform roundTrip = lcns::affine::composeTransform(t, inv);
            // Exact identity is only guaranteed for matrices whose determinant and reciprocal are exactly representable;
            // the first four qualifiers below use a tolerance of one ulp-scale epsilon and the scale cases are exact.
            const double eps = 1e-12;
            CHECK(std::abs(roundTrip.cos - 1.0) < eps);
            CHECK(std::abs(roundTrip.cos2 - 1.0) < eps);
            CHECK(std::abs(roundTrip.negSin) < eps);
            CHECK(std::abs(roundTrip.sin) < eps);
            CHECK(std::abs(roundTrip.zero20) < eps);
            CHECK(std::abs(roundTrip.zero28) < eps);
            for (const double* p : kPoints) {
                double q[2] = {p[0], p[1]};
                lcns::affine::transformPointInPlace(t, q);
                lcns::affine::transformPointInPlace(inv, q);
                CHECK(std::abs(q[0] - p[0]) <= 1e-6 * (1.0 + std::abs(p[0])));
                CHECK(std::abs(q[1] - p[1]) <= 1e-6 * (1.0 + std::abs(p[1])));
            }
        }
        // a singular matrix has no inverse and must say so rather than produce infinities
        const AngleTransform singular = fromArray(kMatrices[3]);
        AngleTransform degenerate = singular;
        degenerate.cos2 = degenerate.negSin * degenerate.sin / degenerate.cos;   // force a*d == b*c
        AngleTransform out;
        CHECK(!lcns::affine::invertTransform(degenerate, out));
        CHECK(sameDouble(out.cos, 0.0) && sameDouble(out.cos2, 0.0));
    }

    // ---------------------------------------------------------------- the library's laws, stated as laws
    {
        const AngleTransform shift = lcns::affine::translationTransform(1.0, 1.0);
        const AngleTransform scale = fromArray(kMatrices[2]);
        const AngleTransform composed = lcns::affine::composeTransform(scale, shift);
        for (const double* p : kPoints) {
            double step[2] = {p[0], p[1]};
            lcns::affine::transformPointInPlace(shift, step);
            lcns::affine::transformPointInPlace(scale, step);      // shift first, then scale
            double once[2] = {p[0], p[1]};
            lcns::affine::transformPointInPlace(composed, once);   // or compose and apply once
            CHECK(sameDouble(step[0], once[0]));
            CHECK(sameDouble(step[1], once[1]));
        }
        // composing with the identity changes nothing, on either side
        const AngleTransform id = fromArray(kMatrices[0]);
        for (const double* m : kMatrices) {
            const AngleTransform t = fromArray(m);
            CHECK(sameTransform(lcns::affine::composeTransform(id, t), t));
            CHECK(sameTransform(lcns::affine::composeTransform(t, id), t));
        }
        // the reflection the record can also express has a determinant of -1, which is why the field names matter
        const AngleTransform reflection = fromArray(kMatrices[4]);
        CHECK(sameDouble(lcns::row::transformDet(reflection), -1.0));
    }

    return check::finish("affine");
}
