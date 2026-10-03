# -*- coding: utf-8 -*-
"""Dump the typeinfo structures so the name pointer's location is read rather than assumed."""
import os
import sys

# **AND THE OUTPUT NEEDS THE SAME TREATMENT AS THE INPUT.** This console encodes with GBK, so printing a replacement character -- which is what a partly readable
# string produces -- raises `UnicodeEncodeError` and takes the whole tool down. **The defect this file exists to look for was on the READING side; the WRITING side
# has it too.**
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib  # noqa: E402

TARGETS = [
    (0xA17FE0, "Multi::Supervisor's typeinfo, per re/vtables.json"),
    (0xA18290, "Multi::NestingContextPool's"),
    (0xA18210, "Multi::NoFitMapCanceller's"),
    (0xA18490, "the table at 0xA3BCE0, which is NOT recorded"),
    (0xA20120, "the table at 0xA560B0, which is NOT recorded"),
]


def string_at(rva, limit=160):
    offset = lib.rva2off(rva) if 0 < rva < 0xB43000 else None
    if offset is None:
        return None
    return lib.pe.get_data(offset, limit).split(b"\x00", 1)[0].decode("utf-8", "replace")


def main():
    for rva, why in TARGETS:
        print("=== 0x%X   %s" % (rva, why))
        words = []
        for index in range(6):
            try:
                words.append(lib.u64(rva + index * 8))
            except Exception:                                      # noqa: BLE001
                words.append(None)
        for index, word in enumerate(words):
            note = ""
            if word and lib.IB <= word < lib.IB + 0xB43000:
                note = "a virtual address -> rva 0x%X" % (word - lib.IB)
                text = string_at(word - lib.IB)
                if text and text.isprintable():
                    note += "  \"%s\"" % text[:60]
            elif word and 0 < word < 0xB43000:
                note = "an rva; string here: %r" % (string_at(word) or "")[:50]
            print("   +0x%02X = 0x%X   %s" % (index * 8, word or 0, note))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
