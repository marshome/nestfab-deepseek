# -*- coding: utf-8 -*-
"""Round 373: the call graph and the tail arithmetic of the two 171-instruction box routines.

Reading 171 instructions by hand does not fit this round, but two things about them can be established mechanically and
are what an implementation needs:

  * which functions they call, in order -- the box accumulator 0x5C8A10 among them would confirm that they build a
    bounding box over the container;
  * their last instructions before each ret -- the arithmetic that turns that box into the number they return, which is
    what distinguishes GetLength from GetHeight.
Both go into re/EXPORT_BODIES.md as the input for implementing the three exports that depend on them.
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
targets = [(0x526160, "GetLength's implementer"), (0x5266A0, "GetHeight's implementer"), (0x5297C0, "GetFillRatio's implementer")]

md = ["", "## Call graph and tail arithmetic of the box routines (round 373)", "",
      "Three exports depend on these: GetLength (0xB130) and GetHeight (0xB160) tail-call the first two with the sub-object",
      "at [order+0x08], and GetFillRatio (0xB4B0) tail-calls the third with the nesting container's address (order+0x50).",
      "The calls below are in instruction order; the tail is everything after the last branch target that is still inside",
      "the function.", ""]

for fn, who in targets:
    size = (prof.get(fn) or {}).get("size")
    ins = [x for x in disasm(fn) if not size or x.address < fn + size]
    calls = []
    for x in ins:
        if x.mnemonic == "call":
            m = re.search(r"0x([0-9a-f]+)", x.op_str)
            if m:
                calls.append((int(m.group(1), 16), x.address))
    md.append("### 0x%X -- %s (%s bytes, %d instructions)" % (fn, who, size, len(ins)))
    md.append("")
    md.append("Calls, in order:")
    md.append("")
    for t, at in calls:
        ts = (prof.get(t) or {}).get("size")
        md.append("* `0x%X` (called from 0x%X)%s" % (t, at, (", %s bytes" % ts) if ts else " -- not in the function profile"))
    md.append("")
    md.append("Last 24 instructions:")
    md.append("")
    md.append("```asm")
    for x in ins[-24:]:
        md.append("%08x  %s %s" % (x.address, x.mnemonic, x.op_str))
    md.append("```")
    md.append("")

    print("=== 0x%X (%s): %d instructions, %d calls" % (fn, who, len(ins), len(calls)))
    seen = []
    for t, at in calls:
        if t not in seen:
            seen.append(t)
    print("   distinct callees: " + ", ".join("0x%X" % t for t in seen))
    box = 0x5C8A10 in seen or 0x50FD40 in seen
    print("   builds a bounding box via the accumulator: %s" % ("YES" if box else "no"))
    print("   tail:")
    for x in ins[-12:]:
        print("      %08x  %s %s" % (x.address, x.mnemonic, x.op_str))
    print("")

t = io.open(DOC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
io.open(DOC, "w", encoding="utf-8", newline="\n").write(t.rstrip("\n") + "\n" + "\n".join(md))
print("EXPORT_BODIES.md updated with the call graphs and tails")
