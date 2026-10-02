# -*- coding: utf-8 -*-
"""Write the export-derived field names into lcns/launching_order.hpp.

Round 537. The offset-frequency work could not name fields and said so. The exports can, and the method is the one an earlier
round had already confirmed by hand -- SetPipeMode writes the gate byte at +0x170 and SetCommonCutParameters writes +0x1A0,
+0x1A8, +0x1B0, +0x1B8 and +0x1C0, which are exactly the fields Multi::RowNester's core reads. An export that ends by
writing a field of the order IS that field's name.

Nine exports need no reading at all (re/g_ready.py) and each one names a field:

    0xD050   SetOrigin                        writes +0x00C  dword  <- the second argument
    0xEC90   SetCommonCutCuttingPreference    writes +0x08C  dword
    0xD1A0   CNS_SetMultiplicityPreference    writes +0x010  double (one of four constants, by the argument)
    0xE010   SetAutomaticStop                 writes +0x240  dword   <- the mode 0x22A20 reads
    0xE940   SetCommonCutSafetyPreference     writes +0x06C  dword
    0xF130   SetMultiTorchCuttingPreference   writes +0x09C  dword
    0x13E30  SetSpecificSheetOrigin           writes +0x124 byte = 1 and +0x128 dword <- the argument
    0x13FE0  SetSpecificSheetObjective        writes +0x12C byte = 1 and +0x130 dword <- the argument
    0x188D0  SetMarkMode                      writes +0x0E8 double and +0x0F0 double <- xmm2 and xmm3

Two of those are landmarks. SetAutomaticStop writing +0x240 is independent confirmation that the mode 0x22A20 reads is the
automatic-stop mode, and SetSpecificSheetOrigin/Objective writing a flag byte next to their value is this module's
"an explicit value was given" marker, which is how those two differ from a plain setter.

The table goes in as a namespace of named constants with the export, its ordinal, and the store address, so a reader can go
from a field to the entry point that sets it and back.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
PATH = os.path.join(ROOT, "lcns", "include", "lcns", "launching_order.hpp")

BLOCK = """
/** The fields the EXPORTS name.
 *
 * An export that ends by writing a field of the order gives that field its name, and this table is read out of the nine
 * entries re/g_ready.py reports as needing no reading at all. Each line carries the export, its ordinal, the store address,
 * and the width, so the name can be checked against the instruction that produced it.
 *
 * This is a different kind of evidence from the accessor witnesses above: there, a function that touches one offset is
 * named; here, the entry point that a caller uses IS the name of the field it sets. Both are direct, and neither is a
 * guess about what a number means.
 */
namespace exported_fields {

inline constexpr std::size_t kOrigin = 0x00C;                    // RE 0xD119: SetOrigin (86) writes a dword
inline constexpr std::size_t kCommonCutCuttingPreference = 0x08C;   // RE 0xED60: SetCommonCutCuttingPreference (154)
inline constexpr std::size_t kMultiplicityPreference = 0x010;    // RE 0xD255: CNS_SetMultiplicityPreference (128), a double
inline constexpr std::size_t kAutomaticStop = 0x240;             // RE 0xE0D9: SetAutomaticStop (140)
inline constexpr std::size_t kCommonCutSafetyPreference = 0x06C; // RE 0xEA0D: SetCommonCutSafetyPreference (150)
inline constexpr std::size_t kMultiTorchCuttingPreference = 0x09C;   // RE 0xF233: SetMultiTorchCuttingPreference (176)
inline constexpr std::size_t kSpecificSheetOriginGiven = 0x124;  // RE 0x13F02: SetSpecificSheetOrigin (298), byte = 1
inline constexpr std::size_t kSpecificSheetOrigin = 0x128;       // RE 0x13F09: the value that flag qualifies
inline constexpr std::size_t kSpecificSheetObjectiveGiven = 0x12C;   // RE 0x140B2: SetSpecificSheetObjective (300)
inline constexpr std::size_t kSpecificSheetObjective = 0x130;    // RE 0x140B9
inline constexpr std::size_t kMarkModeFirst = 0x0E8;             // RE 0x189FA: SetMarkMode (246), a double from xmm2
inline constexpr std::size_t kMarkModeSecond = 0x0F0;            // RE 0x18A10: the second double, from xmm3

// Confirmed by hand in an earlier round and kept because it is the same kind of evidence:
//   SetPipeMode (0xFCF0) writes the gate byte at +0x170, and SetCommonCutParameters (0x3C3F0) writes +0x1A0, +0x1A8,
//   +0x1B0, +0x1B8 and +0x1C0 -- exactly the fields Multi::RowNester's core reads through 0x4FC2F0, 0x4FC300 and 0x4FC3C0.
inline constexpr std::size_t kPipeMode = 0x170;                  // RE round before 537
inline constexpr std::size_t kCommonCutParameterA = 0x1A0;
inline constexpr std::size_t kCommonCutParameterB = 0x1A8;
inline constexpr std::size_t kCommonCutParameterC = 0x1B0;
inline constexpr std::size_t kCommonCutParameterD = 0x1B8;
inline constexpr std::size_t kCommonCutParameterE = 0x1C0;

}  // namespace exported_fields
"""


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "exported_fields" in text:
        print("already there")
        return 0
    marker = "}  // namespace dll"
    assert marker in text, "the dll namespace close is gone"
    text = text.replace(marker, BLOCK.rstrip("\n") + "\n\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote the exported_fields table into %s" % PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
