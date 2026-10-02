// lcns/src/affine.cpp -- the affine operations of the DLL's 0x5CE.../0x5CF... cluster, recovered from the routines the
// registry records. See lcns/affine.hpp for the field map and the reasoning about the single representation.
//
// Two habits are deliberate here, because the differential tests compare against the original bytes bit for bit:
//   * the association order of every sum follows the instructions (product, product, then the translation), since
//     (p1 + p2) + t and p1 + (p2 + t) are not the same double in general;
//   * each coordinate is computed from the ORIGINAL x and y -- the originals read both before storing either, and a
//     transform is not a two-step update.

#include "lcns/affine.hpp"

namespace lcns {
namespace affine {

AngleTransform translationTransform(double tx, double ty) {
    AngleTransform t;
    t.cos = 1.0;     // RE: 0x5CE7C6
    t.negSin = 0.0;  // RE: 0x5CE7CA
    t.sin = 0.0;     // RE: 0x5CE7CF
    t.cos2 = 1.0;    // RE: 0x5CE7D4
    t.zero20 = tx;   // RE: 0x5CE7D9
    t.zero28 = ty;   // RE: 0x5CE7DD
    return t;
}

AngleTransform composeTransform(const AngleTransform& first, const AngleTransform& second) {
    // Positions: first = (a1 b1 c1 d1 tx1 ty1) in the struct's field order, second likewise.
    AngleTransform out;
    // The 2x2 part multiplies; each entry is the sum of two products, and the summation order cannot matter because
    // IEEE addition of two products is commutative even though it is not associative.
    out.cos = first.cos * second.cos + first.negSin * second.sin;              // a = a1*a2 + b1*c2
    out.negSin = first.cos * second.negSin + first.negSin * second.cos2;       // b = a1*b2 + b1*d2
    out.sin = first.sin * second.cos + first.cos2 * second.sin;                // c = c1*a2 + d1*c2
    out.cos2 = first.sin * second.negSin + first.cos2 * second.cos2;           // d = c1*b2 + d1*d2
    // The translation is carried through the first transform, then added: (p + p) + t, the order the routine uses.
    out.zero20 = first.cos * second.zero20 + first.negSin * second.zero28 + first.zero20;
    out.zero28 = first.sin * second.zero20 + first.cos2 * second.zero28 + first.zero28;
    return out;
}

bool invertTransform(const AngleTransform& t, AngleTransform& out) {
    // RE 0x5CED50: the determinant a*d - b*c, its reciprocal, the adjugate, and the negated translation.
    const double det = t.cos * t.cos2 - t.negSin * t.sin;   // RE: 0x5CED8B
    if (det == 0.0) {
        out = AngleTransform{};
        return false;
    }
    const double r = 1.0 / det;   // RE: 0x5CED97 (the one at rva 0x9DE930)
    AngleTransform inv;
    inv.cos = t.cos2 * r;      // d/det
    inv.negSin = -t.negSin * r;  // -b/det
    inv.sin = -t.sin * r;      // -c/det
    inv.cos2 = t.cos * r;      // a/det
    // The translation of the inverse is minus the inverse basis applied to the original translation -- and the negation
    // belongs to the OPERANDS, not to the sum. 0x5CEDB3 loads the translation pair, 0x5CEDBC flips its sign with xorpd,
    // and only then are the products formed and added. For a zero translation the two orders differ in the SIGN OF ZERO:
    // (-a) + (-b) can be +0.0 where -(a + b) is -0.0. The differential test in tests/test_affine.cpp caught exactly
    // that, which is why this is written the long way.
    const double negTx = -t.zero20;
    const double negTy = -t.zero28;
    inv.zero20 = inv.cos * negTx + inv.negSin * negTy;
    inv.zero28 = inv.sin * negTx + inv.cos2 * negTy;
    out = inv;
    return true;
}

void transformPointInPlace(const AngleTransform& t, double* point) {
    const double x = point[0];
    const double y = point[1];
    point[0] = t.cos * x + t.negSin * y + t.zero20;   // RE: 0x5CFDB1 (product, product, then tx)
    point[1] = t.sin * x + t.cos2 * y + t.zero28;     // RE: 0x5CFDA8
}

void transformPairInPlace(const AngleTransform& t, double* pair) {
    // RE 0x5CFDC0: the same arithmetic twice, each from its own original coordinates.
    for (int i = 0; i < 4; i += 2) {
        const double x = pair[i];
        const double y = pair[i + 1];
        pair[i] = t.cos * x + t.negSin * y + t.zero20;
        pair[i + 1] = t.sin * x + t.cos2 * y + t.zero28;
    }
}

void transformPairCopy(const AngleTransform& t, const double* source, double* destination) {
    // RE 0x5CF6B0: the four doubles are copied across first, then transformed in place.
    for (int i = 0; i < 4; ++i) {
        destination[i] = source[i];
    }
    transformPairInPlace(t, destination);
}

double orientationDeterminant(const double* ac, const double* b) {
    // RE 0x24B440, in the routine's own operand order: (Cx-Ax)*(By-Ay) - (Bx-Ax)*(Cy-Ay).
    return (ac[2] - ac[0]) * (b[1] - ac[1]) - (b[0] - ac[0]) * (ac[3] - ac[1]);
}

}  // namespace affine
}  // namespace lcns
