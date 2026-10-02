# -*- coding: utf-8 -*-
"""Round 376: the four functions that appear only inside the box routine's loop.

0x526160 (GetLength's implementer) has 18 calls; four of them are reached only from its loop: 0x524EE0, 0x5C8C50,
0x4F9200, 0x5CD800. Those are where "container -> scalar" is actually computed, so reading them is the shortest path to
implementing GetLength and GetHeight. Recorded whole in re/EXPORT_BODIES.md for the round that implements them.
"""
import io
import os
import sys

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))
from lib import disasm, load_prof  # noqa: E402

prof = load_prof()
DOC = os.path.join(ROOT, "re", "EXPORT_BODIES.md")
TARGETS = [0x524EE0, 0x5C8C50, 0x4F9200, 0x5CD800]

md = ["", "## The four callees reached only from the box routine's loop (round 376)", "",
      "0x526160 (behind GetLength) has 18 calls, and these four are reached only from inside its loop, so they are where the",
      "container's elements are actually turned into the scalar the export returns. 0x5266A0 (behind GetHeight) shares them.",
      ""]

for fn in TARGETS:
    g = prof.get(fn) or {}
    size = g.get("size")
    ins = [x for x in disasm(fn) if not size or x.address < fn + size]
    md.append("### 0x%X -- %s bytes, %d callers, %d instructions" % (fn, size, len([c for c in (g.get("callers") or []) if c != fn]), len(ins)))
    md.append("")
    md.append("```asm")
    for x in ins[:60]:
        md.append("%08x  %s %s" % (x.address, x.mnemonic, x.op_str))
    if len(ins) > 60:
        md.append("... (%d instructions in total)" % len(ins))
    md.append("```")
    md.append("")

t = io.open(DOC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
io.open(DOC, "w", encoding="utf-8", newline="\n").write(t.rstrip("\n") + "\n" + "\n".join(md))

for fn in TARGETS:
    g = prof.get(fn) or {}
    size = g.get("size")
    ins = [x for x in disasm(fn) if not size or x.address < fn + size]
    calls = sorted({x.op_str for x in ins if x.mnemonic == "call"})
    print("=== 0x%X -- %s bytes, %d callers, %d instructions, calls: %s"
          % (fn, size, len([c for c in (g.get("callers") or []) if c != fn]), len(ins), ", ".join(calls)[:120] or "none"))
    for x in ins[:16]:
        print("   %08x  %s %s" % (x.address, x.mnemonic, x.op_str))
    print("")
print("EXPORT_BODIES.md updated")
