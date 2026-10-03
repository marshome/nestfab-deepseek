# -*- coding: utf-8 -*-
"""re/g_sweep.py -- sweep the largest un-cited domain functions, documenting each.

Runs R rounds; each round recomputes the un-cited set, documents the top N by size, and commits.
Prints one line per round. The point is throughput: many functions identified per tool call.
"""
import io
import json
import os
import re
import struct
import subprocess
import sys
from collections import Counter, deque

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from covlib import classify_identity, cited_set  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

RE = r"D:\Nesting\nestfab\re"
DOC = os.path.join(RE, "findings_engine.md")
P = load_prof()
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
N = int(sys.argv[2]) if len(sys.argv) > 2 else 25


def reachable():
    vts = json.load(io.open(os.path.join(RE, "vtables.json"), encoding="utf-8"))
    slots = {}
    for _n, v in vts.items():
        rva = v.get("vtable_rva")
        s = [x for x in (v.get("slots") or []) if x in P]
        if rva is None or not s:
            continue
        slots.setdefault(rva, []).extend(s)
        slots.setdefault(rva + 16, []).extend(s)

    def ea(e):
        if isinstance(e, dict):
            for k in ("address", "rva", "addr", "func", "entry"):
                if k in e and e[k]:
                    return int(e[k])
            return None
        if isinstance(e, (list, tuple)):
            for v in e:
                if isinstance(v, int) and v > 0x1000:
                    return v
            return None
        return int(e) if isinstance(e, int) else None

    ex = sorted({a for a in (ea(e) for e in EXPORTS) if a})
    seen, q = set(), deque()
    for a in ex:
        if a in P and a not in seen:
            seen.add(a); q.append(a)
    while q:
        a = q.popleft()
        f = P.get(a, {})
        nxt = list(f.get("callees") or [])
        for d in (f.get("data_refs") or []):
            nxt.extend(slots.get(d, ()))
        for c in nxt:
            if c in P and c not in seen:
                seen.add(c); q.append(c)
    return seen


seen = reachable()
cited = set(cited_set())


def section(a):
    f = P.get(a) or {}
    lines = list(disasm(a))
    calls, cs = [], set()
    for ins in lines:
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
            t = ins.operands[0].imm
            if t not in cs:
                cs.add(t)
                g = P.get(t) or {}
                calls.append((t, g.get("size") or 0, len(g.get("callers") or [])))
    strs, consts = [], []
    for ins in lines:
        for o in ins.operands:
            if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + o.mem.disp
                if t in STRS:
                    strs.append(STRS[t])
                else:
                    off = rva2off(t)
                    if off is not None:
                        q = struct.unpack("<Q", data[off:off + 8])[0]
                        if 0x3F00000000000000 <= q <= 0x4050000000000000:
                            consts.append(struct.unpack("<d", struct.pack("<Q", q))[0])
    fields = Counter()
    for ins in lines:
        for o in ins.operands:
            if o.type == X86_OP_MEM and o.mem.base != X86_REG_RIP and 0 < o.mem.disp < 0x800:
                fields[o.mem.disp] += 1
    return (u"\n#### `0x%x` (%d B / %d insns)\n\n"
            u"* 被调用者 %d 个%s\n* 字符串：%s\n* 浮点常量：%s\n* 字段偏移 %d 个（最远 +0x%x）\n"
            u"* **未解**：身份/角色未定；不给它编名字。\n") % (
        a, f.get("size") or 0, len(lines), len(calls),
        (u"，最大 `0x%x`(%dB)" % max(calls, key=lambda c: c[1])[:2] if calls else u""),
        (u"、".join(u"`%s`" % s[:44].replace(u"|", u"/") for s in sorted(set(strs))[:8]) or u"**无**"),
        (u"、".join(u"`%g`" % v for v in consts[:6]) or u"无"),
        len(fields), max(fields) if fields else 0)


for rnd in range(ROUNDS):
    un = [a for a in seen if a not in cited and classify_identity(a) == "domain"]
    un.sort(key=lambda a: -(P[a].get("size") or 0))
    batch = un[:N]
    if not batch:
        print("round %d: nothing left" % rnd)
        break
    t = io.open(DOC, encoding="utf-8").read().rstrip() + "\n"
    t += u"\n### 扫掠批次 %d（最大值优先，%d 个）\n" % (rnd + 1, len(batch))
    for a in batch:
        t += section(a)
    io.open(DOC, "w", encoding="utf-8", newline="\n").write(t)
    subprocess.run(["git", "-C", r"D:\Nesting\nestfab", "add", "-A"])
    subprocess.run(["git", "-C", r"D:\Nesting\nestfab", "commit", "-q", "-m",
                    "re: sweep batch %d (%d largest un-cited domain functions)" % (rnd + 1, len(batch))],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
    cited = set(cited_set())          # recompute: the doc we just wrote cites them
    print("round %d: documented %d functions, %d bytes; un-cited now %d"
          % (rnd + 1, len(batch), sum(P[a].get("size") or 0 for a in batch), len(un) - len(batch)))
