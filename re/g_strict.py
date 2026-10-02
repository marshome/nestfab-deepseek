# -*- coding: utf-8 -*-
"""Strict ownership clustering: helpers whose EVERY caller is the same named function (true private
machinery), as opposed to the looser "only one caller with identity" table written earlier."""
import io
import json
import os
import sys
from collections import defaultdict, deque

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from covlib import classify_identity, cited_set  # noqa: E402

RE = r"D:\Nesting\nestfab\re"
P = load_prof()
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

cited = set(cited_set())


def label(a):
    f = P.get(a) or {}
    if f.get("name"):
        return f["name"]
    ss = f.get("strings") or []
    if ss:
        return "0x%x \u300c%s\u300d" % (a, str(ss[0][1] if isinstance(ss[0], (tuple, list)) else ss[0])[:28])
    return ""


groups = defaultdict(list)
for a in seen:
    if a in cited or classify_identity(a) != "domain":
        continue
    f = P[a]
    if f.get("strings") or f.get("name"):
        continue
    callers = [c for c in (f.get("callers") or []) if c in P]
    if not callers:
        continue
    if len(set(callers)) == 1 and label(callers[0]):
        groups[callers[0]].append(a)

rows = sorted(((k, len(v), sum((P[x].get("size") or 0) for x in v)) for k, v in groups.items()),
              key=lambda r: -r[2])
tot_f = sum(r[1] for r in rows)
tot_b = sum(r[2] for r in rows)
print("strict private machinery: %d owners, %d helpers, %d bytes" % (len(rows), tot_f, tot_b))
for k, n, b in rows[:15]:
    print("   %-52s %3d fns %8d B" % (label(k)[:52], n, b))

DOC = os.path.join(RE, "SWEEP.md")
S = (u"\n## 严格归属：真正的「私有机制」（每个调用者都等于同一个具名函数）\n\n"
     u"上文的宽松表（忽略匿名调用者）**不能**当作私有关系；这一节是严格版：\n"
     u"**%d 个具名入口共拥有 %d 个这样的匿名辅助 / %d 字节**。\n\n"
     u"| 入口 | 私有辅助 | 字节 |\n|---|---:|---:|\n") % (len(rows), tot_f, tot_b)
for k, n, b in rows[:60]:
    S += u"| `%s` | %d | %d |\n" % (label(k).replace("|", "/"), n, b)
S += (u"\n**读法**：这些函数**只**被该入口调用（调用者集合恰好是它一个，且该入口有身份证据）。这仍然只是**来源**而不是**身份**（不说明函数做什么），故留在 tier C 文件里，不计入引用。\n")
io.open(DOC, "a", encoding="utf-8", newline="\n").write(S)
print("appended the strict-ownership table to re/SWEEP.md (uncommitted)")
