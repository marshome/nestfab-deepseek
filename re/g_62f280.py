# -*- coding: utf-8 -*-
"""Round 374: 0x62F280 -- the common base of 100 call sites -- read whole, and implemented only if its body allows it.

Round 373 showed that the three box routines behind GetLength, GetHeight and GetFillRatio all end by calling 0x62F280, so
it is the highest-leverage internal function left. This dumps it, records it in re/HELPERS.md, and -- only if its body is
an unambiguous fixed sequence (a load, a store, or a tail call) -- reports what an implementation would be. The script
writes no code: implementing belongs to the round that can build and test in the same breath, and this round's job is to
make that round possible.
"""
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))
from lib import disasm, load_prof  # noqa: E402

prof = load_prof()
DOC = os.path.join(ROOT, "re", "HELPERS.md")
FN = 0x62F280
size = (prof.get(FN) or {}).get("size")
callers = [c for c in ((prof.get(FN) or {}).get("callers") or []) if c != FN]
ins = [x for x in disasm(FN) if not size or x.address < FN + size]

md = ["", "## 0x%X -- %s bytes, %d callers (round 374)" % (FN, size, len(callers)), "",
      "The highest-leverage internal function left: the three box routines behind GetLength, GetHeight and GetFillRatio all",
      "end by calling it, and re/EXPORT_QUEUE.md counts it as the blocker of 100 unimplemented entries. It is not itself an",
      "export, so it is read as a part rather than as an entry point.", "", "```asm"]
for x in ins:
    md.append("%08x  %s %s" % (x.address, x.mnemonic, x.op_str))
md += ["```", ""]

t = io.open(DOC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
io.open(DOC, "w", encoding="utf-8", newline="\n").write(t.rstrip("\n") + "\n" + "\n".join(md))

print("0x%X: %s bytes, %d callers, %d instructions" % (FN, size, len(callers), len(ins)))
for x in ins:
    print("   %08x  %s %s" % (x.address, x.mnemonic, x.op_str))

text = ["%s %s" % (x.mnemonic, x.op_str) for x in ins]
calls = [x for x in ins if x.mnemonic == "call"]
print("")
print("calls: %d %s" % (len(calls), ", ".join(sorted({c.op_str for c in calls}))[:200]))
if len(ins) <= 6 and text[-1].startswith("ret"):
    m = re.match(r"^mov (rax|eax), (qword|dword) ptr \[rcx \+ (0x[0-9a-f]+)\]$", text[0])
    if m:
        print("SHAPE: a pure getter of a %s at +%s -- implementable exactly, by the same rule as the getter family"
              % ("qword" if m.group(2) == "qword" else "dword", m.group(3)))
    else:
        print("SHAPE: short but not a single field load; recorded, not implemented")
else:
    print("SHAPE: too long or not a single load -- recorded, not implemented")
print("")
print("HELPERS.md updated")
