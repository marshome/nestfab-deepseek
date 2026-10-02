# -*- coding: utf-8 -*-
"""Round 378: the whole body of 0x5C8C50, the box merge, which round 377 made executable.

Round 376 read its first fourteen instructions and 377 embedded it as a callable block. Its 62 instructions are what a
differential test has to be written against -- the original can now be called from the project, so the C++ model can be
compared with it bit for bit, which is the strongest evidence available here. This records the complete listing.
"""
import io
import os
import sys

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))
from lib import disasm, load_prof  # noqa: E402

prof = load_prof()
FN = 0x5C8C50
size = (prof.get(FN) or {}).get("size")
ins = [x for x in disasm(FN) if not size or x.address < FN + size]
DOC = os.path.join(ROOT, "re", "EXPORT_BODIES.md")

md = ["", "## 0x5C8C50 in full -- the box merge, now executable (round 378)", "",
      "Round 377 embedded this block and the classifier marked it callable (no calls, no RIP-relative data, 62",
      "instructions, 56 callers), so tests/test_boxacc.cpp can call the original and compare a C++ model with it bit for",
      "bit. This is the listing that model must reproduce, and it is the common step behind GetLength, GetHeight and the",
      "container construction of 0x5CD800.", "", "```asm"]
for x in ins:
    md.append("%08x  %s %s" % (x.address, x.mnemonic, x.op_str))
md += ["```", ""]

t = io.open(DOC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
io.open(DOC, "w", encoding="utf-8", newline="\n").write(t.rstrip("\n") + "\n" + "\n".join(md))

print("0x%X: %s bytes, %d instructions" % (FN, size, len(ins)))
for x in ins:
    print("   %08x  %s %s" % (x.address, x.mnemonic, x.op_str))
print("")
print("EXPORT_BODIES.md updated")
