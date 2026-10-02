# -*- coding: utf-8 -*-
"""Round 370: the full bodies of the cheapest read-only exports, so the next round implements from the code, not a guess.

Round 369 established that the logger 0x64AEA0 does nothing on its default path (a global switch is off, and the function
jumps straight to its epilogue), so these exports' return values are the whole of their behaviour. This writes their
complete listings to re/EXPORT_BODIES.md and prints them, and it records for each one what the body does with the
argument -- which field it reads, through which getter -- as a claim to be checked when the implementation lands.
"""
import io
import os
import sys

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))
from lib import disasm, load_prof  # noqa: E402

TARGETS = [
    (0xB490, "GetBuildVersion", 88),
    (0xB470, "GetBuildDate", 90),
    (0xB450, "GetMajorVersion", 92),
    (0xB4B0, "GetFillRatio", 168),
    (0xB130, "GetLength", 96),
    (0xB160, "GetHeight", 100),
    (0xB4E0, "GetNestingFillRatio", 192),
    (0x107E0, "GetComputationStatus", 15),
]
prof = load_prof()

md = ["# The cheapest read-only exports, read whole (round 370)",
      "",
      "re/EXPORT_QUEUE.md ranks these first, and round 369 showed that the logger they call (0x64AEA0) does nothing on its",
      "default path, so their return value is the whole of their behaviour. The listings below are the input for",
      "implementing them, and the note under each is a claim to be checked by the test that lands with the implementation.",
      ""]

for rva, name, ord0 in TARGETS:
    size = (prof.get(rva) or {}).get("size")
    md.append("## %s (ord %d) -- 0x%X, %s bytes" % (name, ord0, rva, size))
    md.append("")
    md.append("```asm")
    for x in disasm(rva):
        if size and x.address >= rva + size:
            break
        md.append("%08x  %s %s" % (x.address, x.mnemonic, x.op_str))
    md.append("```")
    md.append("")

io.open(os.path.join(ROOT, "re", "EXPORT_BODIES.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
print("EXPORT_BODIES.md written (%d functions)" % len(TARGETS))
print("")
for rva, name, ord0 in TARGETS:
    size = (prof.get(rva) or {}).get("size")
    ins = [x for x in disasm(rva) if not size or x.address < rva + size]
    calls = [x.op_str for x in ins if x.mnemonic == "call"]
    print("=== %s 0x%X (%s bytes, %d insns, calls: %s)" % (name, rva, size, len(ins), ",".join(calls) or "none"))
    for x in ins:
        print("   %08x  %s %s" % (x.address, x.mnemonic, x.op_str))
    print("")
