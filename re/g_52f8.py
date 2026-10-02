# -*- coding: utf-8 -*-
"""Round 375: the 0x52F8xx family -- where GetLength and GetHeight actually differ.

Round 373 established that 0x526160 (GetLength's implementer) and 0x5266A0 (GetHeight's) are otherwise identical, differing
in exactly one callee: 0x52F810 against 0x52F830. That pair is therefore where "length" and "height" are computed, and it
is the shortest path to implementing those two exports (forwardedCount 14 -> 16). This records the family whole, so the
implementing round works from listings rather than from another read.
"""
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))
from lib import disasm, load_prof  # noqa: E402

prof = load_prof()
DOC = os.path.join(ROOT, "re", "EXPORT_BODIES.md")
FAMILY = [0x52F810, 0x52F830, 0x52F8B0, 0x52F8C0, 0x52F950]

md = ["", "## The 0x52F8xx family (round 375)", "",
      "GetLength's implementer (0x526160) and GetHeight's (0x5266A0) are otherwise identical and differ in one callee each:",
      "0x52F810 against 0x52F830. That pair is where the length and the height are computed, so these listings are what an",
      "implementation of GetLength (0xB130, ord 96) and GetHeight (0xB160, ord 100) has to be written from.", ""]

for fn in FAMILY:
    g = prof.get(fn) or {}
    size = g.get("size")
    ins = [x for x in disasm(fn) if not size or x.address < fn + size]
    md.append("### 0x%X -- %s bytes, %d callers, %d instructions" % (fn, size, len([c for c in (g.get("callers") or []) if c != fn]), len(ins)))
    md.append("")
    md.append("```asm")
    for x in ins[:48]:
        md.append("%08x  %s %s" % (x.address, x.mnemonic, x.op_str))
    if len(ins) > 48:
        md.append("... (%d instructions in total; the bytes are embedded in the project)" % len(ins))
    md.append("```")
    md.append("")

t = io.open(DOC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
io.open(DOC, "w", encoding="utf-8", newline="\n").write(t.rstrip("\n") + "\n" + "\n".join(md))

for fn in FAMILY:
    g = prof.get(fn) or {}
    size = g.get("size")
    ins = [x for x in disasm(fn) if not size or x.address < fn + size]
    print("=== 0x%X -- %s bytes, %d callers, %d instructions" % (fn, size, len([c for c in (g.get("callers") or []) if c != fn]), len(ins)))
    for x in ins[:20]:
        print("   %08x  %s %s" % (x.address, x.mnemonic, x.op_str))
    text = ["%s %s" % (x.mnemonic, x.op_str) for x in ins]
    loads = [q for q in text if re.match(r"^movsd xmm[0-9], qword ptr \[rcx \+ (0x[0-9a-f]+)\]$", q)]
    load1 = [q for q in text if re.match(r"^movsd xmm[0-9], qword ptr \[rdx \+ (0x[0-9a-f]+)\]$", q)]
    subs = [q for q in text if q.startswith("subsd")]
    if len(ins) <= 12 and (loads or load1) and subs:
        print("   -> SHAPE: a difference of two doubles (%s / %s), implementable exactly"
              % (loads[:1], subs[:1]))
    else:
        print("   -> shape not deterministic from the head; recorded only")
    print("")
print("EXPORT_BODIES.md updated")
