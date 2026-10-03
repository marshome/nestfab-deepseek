# -*- coding: utf-8 -*-
"""Name the four offsets in `Order` that a carrier had a flag for and `Order` called padding.

**THE EVIDENCE, ONE `setne` PER FIELD, EACH UNDER THE EXPORT THAT OWNS IT:**

    SetPartCommonCutMode                0xDE69   `setne byte [rsi + 0x1c]`
    CNS_SetFloatingMode                 0xDD49   `setne byte [rsi + 0x20]`
    CNS_SetOriginPackingMode            0xDD79   `setne byte [rsi + 0x21]`
    SetFillLastNestingStrategy          0xDDA9   `setne byte [rsi + 0x40]`

**and `Order` calls all four PADDING** -- `padding01b[0x2]` covers +0x20..+0x21 and `padding03` is +0x40 -- **so `OptionFlagCarrier` was describing four real bytes that the
one structure for this object had written off as gaps.**

**THE NAMES COME FROM THE EXPORT AND NOT FROM THE FLAG'S POSITION**, which is the whole point: `flag20` says where the byte is and `floatingMode` says what it is,
and the module's own function name is the witness for the second.
"""
import io
import re
import sys

MODEL = r"D:\Nesting\nestfab\lcns\include\lcns\model.hpp"

# the padding member to split, the fields to put in its place
EDITS = [
    ("    std::byte padding01b[0x2];   // +0x020..+0x021, no field here",
     "    /** +0x1C, RE 0xDE69: `setne byte [rsi + 0x1c]` in SetPartCommonCutMode (ordinal 166). **The export's name is the oracle for the field.** */\n"
     "    bool partCommonCutMode = false;\n"
     "    /** +0x20, RE 0xDD49: `setne byte [rsi + 0x20]` in CNS_SetFloatingMode (ordinal 182). */\n"
     "    bool floatingMode = false;\n"
     "    /** +0x21, RE 0xDD79: `setne byte [rsi + 0x21]` in CNS_SetOriginPackingMode (ordinal 312). */\n"
     "    bool originPackingMode = false;"),
    ("    std::byte padding03[0x1];    // +0x040..+0x040, no field here",
     "    /** +0x40, RE 0xDDA9: `setne byte [rsi + 0x40]` in SetFillLastNestingStrategy (ordinal 144). */\n"
     "    bool fillLastNestingStrategy = false;"),
]


def main(apply):
    text = io.open(MODEL, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    for old, new in EDITS:
        if new in text:
            print("   already patched: %s" % old.strip()[:44])
            continue
        if old not in text:
            print("   REFUSING: anchor not found: %s" % old.strip()[:60])
            return 2
        text = text.replace(old, new, 1)
        print("   patched: %s" % old.strip()[:60])
    if apply:
        io.open(MODEL, "w", encoding="utf-8", newline="\n").write(text)
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
