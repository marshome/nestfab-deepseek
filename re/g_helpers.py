# -*- coding: utf-8 -*-
"""Round 369: dump the helper family the cheapest exports all call, and print 0x64AEA0's own code.

re/EXPORT_QUEUE.md shows five of the ten cheapest unimplemented exports reaching the module through 0x64AEA0, so what that
function does decides whether those exports can be implemented without reproducing it. This writes re/HELPERS.md (full
listings, caller counts) -- the artifact -- and prints 0x64AEA0 to the console so the decision can be made from the run.
"""
import io
import os
import sys

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))
from lib import disasm, load_prof  # noqa: E402

HELPERS = [0x64AEA0, 0x64E120, 0x64E630, 0x64ABF0, 0x64CA50, 0x64ACE0, 0x64B040]
prof = load_prof()

md = ["# The logging and assertion helpers the cheap exports call",
      "",
      "Read whole in round 369 because re/EXPORT_QUEUE.md shows that the cheapest unimplemented exports all reach the",
      "module through one of these: 0x64AEA0 alone is what five of the ten cheapest entries call first. Whether such a",
      "call can be left out of an implementation, or has to be reproduced, depends on what it does to memory and on what",
      "it returns -- which is what these listings answer. The bytes of every caller are already embedded in the project",
      "(re/g_embed.py embeds the whole export set), so any claim made from these listings can be checked against the",
      "module by re/check_embeddings.py.",
      ""]

for fn in HELPERS:
    g = prof.get(fn) or {}
    size = g.get("size")
    callers = len([c for c in (g.get("callers") or []) if c != fn])
    md.append("## 0x%X -- %s bytes, %d callers" % (fn, size, callers))
    md.append("")
    md.append("```asm")
    n = 0
    for x in disasm(fn):
        if size and x.address >= fn + size:
            break
        md.append("%08x  %s %s" % (x.address, x.mnemonic, x.op_str))
        n += 1
        if n >= 60:
            md.append("... (truncated in this document; the bytes are embedded in the project)")
            break
    md.append("```")
    md.append("")

io.open(os.path.join(ROOT, "re", "HELPERS.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
print("HELPERS.md written (%d helpers)" % len(HELPERS))
for fn in HELPERS:
    g = prof.get(fn) or {}
    print("  0x%-8X %-6s bytes, %d callers" % (fn, g.get("size"), len([c for c in (g.get("callers") or []) if c != fn])))

print("")
print("=== 0x64AEA0 in full (the decision input) ===")
g = prof.get(0x64AEA0) or {}
for x in disasm(0x64AEA0):
    if g.get("size") and x.address >= 0x64AEA0 + g["size"]:
        break
    print("  %08x  %s %s" % (x.address, x.mnemonic, x.op_str))
