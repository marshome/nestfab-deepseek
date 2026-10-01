# -*- coding: utf-8 -*-
"""Recover the SVG document schema emitted by ..\\structure\\svg_io.cpp.

Step 1: every string referenced by the TU's functions -> the element/attribute/style vocabulary.
Step 2: the main writer 0x7CCDF0 in address order -> the document skeleton.
"""
import io
import os
import struct
import sys
from collections import defaultdict

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP  # noqa: E402
from covlib import PROF, RE, cited_set, hint_of, reachable  # noqa: E402
import g_tu_list  # noqa: E402


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


reach, label, how = g_tu_list.build_labels()
sel = [a for a in reach if "svg_io" in (label.get(a) or "")]
print("svg_io TU: %d functions / %d bytes" % (len(sel), sum(PROF[a]["size"] for a in sel)))

# ---------------------------------------------------------------- vocabulary
seen = defaultdict(set)
for a in sel:
    for s in (PROF[a].get("strings") or []):
        if isinstance(s, (tuple, list)) and len(s) == 2:
            addr, text = s
            if text and len(text) < 90:
                seen[text].add(a)
print()
print("=== strings referenced by the TU (%d distinct) ===" % len(seen))
svgish = [t for t in seen if any(k in t for k in
                                 ("<", "=", "svg", "fill", "stroke", "style", "transform",
                                  "width", "height", "viewBox", "path", "circle", "rect",
                                  "line", "polygon", "text", "use", "defs", "pattern", "clip",
                                  "opacity", "rgb", "url(", "xlink", "multiplicity", "%"))]
for t in sorted(svgish):
    where = sorted(seen[t])[:2]
    print("   %-62r %s" % (t[:60], " ".join("0x%x" % w for w in where)))

# ---------------------------------------------------------------- main writer skeleton
FN = 0x7CCDF0
print()
print("=== 0x%x (size=%s) -- calls and string refs in address order ==="
      % (FN, (PROF.get(FN) or {}).get("size")))
lines = list(disasm(FN))
for ins in lines:
    ctx = []
    for o in ins.operands:
        if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + o.mem.disp
            if t in STRS:
                ctx.append("STR %r" % STRS[t][:52])
            else:
                ctx.append("d@0x%x=%r" % (t, f64(t)))
        elif o.type == X86_OP_IMM and ins.mnemonic == "call":
            ctx.append("-> 0x%x(%s)" % (o.imm, (PROF.get(o.imm) or {}).get("size")))
    if ctx:
        print("   %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))
