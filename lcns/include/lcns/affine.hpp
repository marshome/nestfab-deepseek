// lcns/affine.hpp -- the 2x3 affine operations the DLL's 0x5CE.../0x5CF... cluster performs.
//
// This header deliberately does NOT introduce a second matrix type. The project already carries the six-double record as
// AngleTransform in lcns/row.hpp, with transformX/transformY/transformDet reading it, and this work's own differential
// tests against the original bytes confirmed that layout from seven routines. What was missing there is the rest of the
// library the dump shows: building a translation, composing two transforms, inverting one, and the three apply forms
// that write into the caller's buffer. Those are added here, on the same record, so the project keeps ONE representation.
//
// Field map (the offsets are the original's; RE in re/findings_engine.md, rounds 339-348):
//     AngleTransform::cos     [+0x00]  a
//     AngleTransform::negSin  [+0x08]  b
//     AngleTransform::sin     [+0x10]  c
//     AngleTransform::cos2    [+0x18]  d
//     AngleTransform::zero20  [+0x20]  tx
//     AngleTransform::zero28  [+0x28]  ty
// and the map is  x' = a*x + b*y + tx ,  y' = c*x + d*y + ty  -- the formula that four routines read and one wrote.
//
// The names cos/negSin/sin/cos2 are the angle-transform reading of those six slots; the generic operations below use them
// positionally and say so, rather than pretending the record is a rotation when it is not (0x5CEE50's tag != 0 path
// builds a reflection through the same record, which is why the reflection bug the tests caught was possible).

#pragma once

#include "lcns/row.hpp"

namespace lcns {
namespace affine {

// The six-double record already lives in lcns::row (as the angle transform's own type). Aliased rather than redefined:
// the project keeps one representation, and the tests below hold these operations and row.hpp's readers to the same
// original bytes.
using AngleTransform = row::AngleTransform;

// RE 0x5CE7B0 (50 B, 32 callers): the identity basis with a translation taken from a point.
//     5CE7C6 [rcx]      = 1.0   ; a
//     5CE7CA [rcx+0x08] = 0.0   ; b
//     5CE7CF [rcx+0x10] = 0.0   ; c
//     5CE7D4 [rcx+0x18] = 1.0   ; d
//     5CE7D9/0x5CE7DD  [rcx+0x20] and [rcx+0x28] = the point's two doubles
AngleTransform translationTransform(double tx, double ty);

// RE 0x5CE970 (269 B, 38 callers): two transforms composed. `first` is applied to the result of `second`, which is the
// order the routine's own arithmetic produces and the order the embedded differential test checks.
AngleTransform composeTransform(const AngleTransform& first, const AngleTransform& second);

// RE 0x5CED50 (196 B, 24 callers): the inverse, by determinant, reciprocal, adjugate and negated translation.
// @returns false when the determinant is zero, in which case `out` is left as identity.
bool invertTransform(const AngleTransform& t, AngleTransform& out);

// RE 0x5CFD80 (64 B, 4 callers): apply in place to one point (two doubles at the pointer).
void transformPointInPlace(const AngleTransform& t, double* point);

// RE 0x5CFDC0 (160 B, 3 callers): apply in place to both points of a segment (four doubles at the pointer).
void transformPairInPlace(const AngleTransform& t, double* pair);

// RE 0x5CF6B0 (235 B, 6 callers): copy four doubles and apply, leaving the source alone.
void transformPairCopy(const AngleTransform& t, const double* source, double* destination);

// RE 0x24B440 (61 B, 2 callers): the orientation determinant of three points, as the routine orders its operands:
// `ac` holds A at +0x00/+0x08 and C at +0x10/+0x18, `b` holds B at +0x00/+0x08, and the result is
// (Cx-Ax)*(By-Ay) - (Bx-Ax)*(Cy-Ay). Its sign distinguishes the two turn directions.
double orientationDeterminant(const double* ac, const double* b);

}  // namespace affine
}  // namespace lcns
