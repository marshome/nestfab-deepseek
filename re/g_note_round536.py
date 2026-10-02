# -*- coding: utf-8 -*-
"""Annotate lcns/launching_order.hpp with each field's WITNESSES, which is what makes a name trustworthy.

Round 536. The naming work now has a rule that decides when a name may be used, and it is not "a function touched this
offset once":

    a name is accepted only when TWO INDEPENDENT single-offset accessors agree on the offset

re/g_two_witnesses.py implements it, and it is deliberately unkind. For the launch order the whole module yields:

    +0x10   GenerateDxfNesting (read) and GetNestingFillRatio (read)          two witnesses
    +0x50   GenerateHtmlSolutionReport (read) and GetFillRatio (read)         two witnesses
    +0x140  GetSheetUserStringEx (read)                                       one witness  -- a lead
    +0x1B8  GetPartUserStringEx (read)                                        one witness
    +0x1F8  LaunchLimitedLocalComputation (write)                             one witness
    +0x288  LaunchEstimateLocalComputation (write)                            one witness

So the honest position is that six names exist for regions of this object and only two of them are witnessed twice. The
header records the witness count next to each name rather than presenting all six as equally established, because that count
is exactly what a later reader needs to decide how much to rely on it.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
PATH = os.path.join(ROOT, "lcns", "include", "lcns", "launching_order.hpp")

BLOCK = """// ---------------------------------------------------------------------------------------------------------------
// Each name's WITNESSES (round 536)
//
// A name is used here only when TWO INDEPENDENT single-offset accessors agree on the offset, which is the rule
// re/g_two_witnesses.py enforces. An accessor is a function of at most 0x100 bytes that touches exactly one offset through
// its first argument: one witness can be a function whose name describes something else, two independent ones cannot both
// be wrong the same way. The count is recorded next to each name because it is what tells a later reader how much weight to
// give it.
//
//   offset   witnesses  the accessors and what they do
//   +0x0010  2          GenerateDxfNesting reads it, GetNestingFillRatio reads it
//   +0x0050  2          GenerateHtmlSolutionReport reads it, GetFillRatio reads it
//   +0x0140  1          GetSheetUserStringEx reads it                                   (a lead)
//   +0x01B8  1          GetPartUserStringEx reads it                                    (a lead)
//   +0x01F8  1          LaunchLimitedLocalComputation writes it                         (a lead)
//   +0x0288  1          LaunchEstimateLocalComputation writes it                        (a lead)
//
// Two of the six are for the objects the EXPORTS take rather than for the launch order itself: GetFillRatio and
// GetNestingFillRatio are exports over a solution, and GenerateDxfNesting and GenerateHtmlSolutionReport read the same
// object to render it. They are listed because the offsets coincide, and that coincidence is itself a fact worth knowing --
// the solution and the launch order share a layout at +0x10 and +0x50 -- but it is not evidence that a launch order field at
// +0x10 is named FillRatio.
//
// The four remaining names have one witness each and are used with that stated. Everything else keeps slotXXX.
// ---------------------------------------------------------------------------------------------------------------

"""


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "Each name's WITNESSES" in text:
        print("already there")
        return 0
    marker = "namespace names {"
    assert marker in text, "the names namespace is gone"
    text = text.replace(marker, BLOCK + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("annotated the witnesses in %s" % PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
