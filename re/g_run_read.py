# -*- coding: utf-8 -*-
"""re/g_run_read.py <addr> [--doc <findings.md> <title>] -- read one strategy Run body.

Reusable for the whole Run-body campaign: prints the call surface (annotated with recovered names
and sizes), strings, floating constants, immediates and the field-offset ladder, and with --doc
appends the same as a findings section. Nothing is claimed beyond what the dump shows: the section
lists the evidence and then an explicit "not yet understood" list.
"""
import io
import sys
from collections import Counter

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

P = load_prof()
FN = int(sys.argv[1], 16)
doc = None
if "--doc" in sys.argv:
    i = sys.argv.index("--doc")
    doc = (sys.argv[i + 1], sys.argv[i + 2], sys.argv[i + 3])   # path, title, note-line

lines = list(disasm(FN))
calls, seen = [], set()
for ins in lines:
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
        t = ins.operands[0].imm
        if t not in seen:
            seen.add(t)
            f = P.get(t) or {}
            calls.append((t, f.get("size") or 0, len(f.get("callers") or []), f.get("name") or ""))
strings, consts = [], []
for ins in lines:
    for o in ins.operands:
        if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + o.mem.disp
            if t in STRS:
                strings.append((ins.address, STRS[t][:70]))
            else:
                off = rva2off(t)
                if off is not None:
                    import struct
                    q = struct.unpack("<Q", data[off:off + 8])[0]
                    if 0x3F00000000000000 <= q <= 0x4050000000000000:
                        import math
                        consts.append((ins.address, t, struct.unpack("<d", struct.pack("<Q", q))[0]))
fields = Counter()
for ins in lines:
    for o in ins.operands:
        if o.type == X86_OP_MEM and o.mem.base != X86_REG_RIP and 0 < o.mem.disp < 0x800:
            fields[o.mem.disp] += 1
imms = Counter()
for ins in lines:
    for o in ins.operands[1:]:
        if o.type == X86_OP_IMM and 0 < o.imm < 0x4000:
            imms[o.imm] += 1

rep = [u"* 函数：`0x%x`，%d 字节 / **%d 条指令**" % (FN, (P.get(FN) or {}).get("size") or 0, len(lines)),
       u"* 被调用者（%d 个）：" % len(calls) +
       u"、".join(u"`0x%x`(%dB%s)" % (a, s, u"，%d 调用者" % c if c > 5 else u"")
                 for a, s, c, _n in calls) if calls else u"* 被调用者：无",
       u"* 字符串：**一个都没有**（纯算法体）" if not strings else
       u"* 字符串：" + u"、".join(u"`%s`" % s.replace(u"|", u"\\|")[:50] for _a, s in strings[:8]),
       u"* 浮点常量：" + (u"、".join(u"**%g**（`0x%x`）" % (v, t) for _a, t, v in consts)
                          if consts else u"无"),
       u"* 立即数：" + u", ".join(u"`%d`×%d" % (k, v) for k, v in sorted(imms.items())),
       u"* 字段偏移（%d 个）：`%s`" % (len(fields), u"`、`".join(u"+0x%x" % k for k in sorted(fields)))]
print(u"=== 0x%x ===" % FN)
for r in rep:
    print(r)

if doc:
    path, title, note = doc
    t = io.open(path, encoding="utf-8").read().rstrip() + "\n"
    S = u"\n### %s\n\n" % title + u"\n".join(rep) + u"\n\n" + note + u"\n"
    io.open(path, "w", encoding="utf-8", newline="\n").write(t + S)
    print("appended to %s" % path)
