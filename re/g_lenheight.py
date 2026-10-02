# -*- coding: utf-8 -*-
"""Round 371: read the two implementers behind GetLength/GetHeight, and implement them if the body allows it safely.

Both exports pass the SAME argument -- the sub-object at [order+8] (NestingOwner::sub) with edx = 0 -- to different
functions, 0x526160 and 0x5266A0, which is what "length" and "height" of that object should look like. If such a body
turns out to be a fixed sequence of double loads and one subtraction, it can be implemented mechanically and verified by a
test, with nothing guessed. If it is not, this round only records the listing and says so.
"""
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))
from lib import disasm, load_prof  # noqa: E402

prof = load_prof()
TARGETS = [(0x526160, "GetLength"), (0x5266A0, "GetHeight")]
DOC = os.path.join(ROOT, "re", "EXPORT_BODIES.md")

md = ["", "## The implementers behind GetLength and GetHeight (round 371)", "",
      "GetLength (0xB130) and GetHeight (0xB160) both take the sub-object at [order+0x08] with edx = 0 and tail-call one of",
      "these. Their bodies are the actual geometry, so they are what has to be read before the two exports can be",
      "implemented.", ""]

shapes = []
for fn, owner in TARGETS:
    size = (prof.get(fn) or {}).get("size")
    ins = [x for x in disasm(fn) if not size or x.address < fn + size]
    md.append("### 0x%X (%s) -- %s bytes, %d instructions" % (fn, owner, size, len(ins)))
    md.append("")
    md.append("```asm")
    for x in ins:
        md.append("%08x  %s %s" % (x.address, x.mnemonic, x.op_str))
    md.append("```")
    md.append("")
    # Recognise only a body that is unambiguously two double loads and one subtraction, and only if it is short.
    text = ["%s %s" % (x.mnemonic, x.op_str) for x in ins]
    loads = [t for t in text if re.match(r"^movsd xmm0, qword ptr \[rcx \+ (0x[0-9a-f]+)\]$", t)]
    subs = [t for t in text if re.match(r"^subsd xmm0, qword ptr \[rcx \+ (0x[0-9a-f]+)\]$", t)]
    if len(ins) <= 6 and len(loads) == 1 and len(subs) == 1 and text[-1].startswith("ret"):
        a = int(re.search(r"0x([0-9a-f]+)", loads[0]).group(1), 16)
        b = int(re.search(r"0x([0-9a-f]+)", subs[0]).group(1), 16)
        shapes.append((fn, owner, a, b))
        md.append("Shape: `*[rcx+0x%X] - *[rcx+0x%X]`, returned in xmm0 -- a difference of two doubles in the same object." % (a, b))
    else:
        md.append("Shape: NOT a simple double difference (it has calls or branches), so it is recorded, not implemented.")
    md.append("")

t = io.open(DOC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
io.open(DOC, "w", encoding="utf-8", newline="\n").write(t.rstrip("\n") + "\n" + "\n".join(md))
print("EXPORT_BODIES.md updated")
for fn, owner in TARGETS:
    size = (prof.get(fn) or {}).get("size")
    ins = [x for x in disasm(fn) if not size or x.address < fn + size]
    print("")
    print("=== 0x%X (%s) %s bytes, %d instructions ===" % (fn, owner, size, len(ins)))
    for x in ins[:24]:
        print("   %08x  %s %s" % (x.address, x.mnemonic, x.op_str))
print("")
print("recognised simple shapes: %d" % len(shapes))
for fn, owner, a, b in shapes:
    print("   0x%X (%s): [rcx+0x%X] - [rcx+0x%X]" % (fn, owner, a, b))
