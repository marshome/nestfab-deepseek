# -*- coding: utf-8 -*-
"""Cluster the un-cited, string-less domain functions by their named callers.

Provenance is evidence: if every caller of an anonymous helper is one named function, that helper is
part of that function's private machinery. This gives the shape-only bucket real (if weak) identity
and turns it into an owned work list, which is more useful than a flat size ranking.
"""
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict, deque

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from covlib import classify_identity, cited_set  # noqa: E402

RE = r"D:\Nesting\nestfab\re"
P = load_prof()

# reachable
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
anon = []
for a in seen:
    if a in cited or classify_identity(a) != "domain":
        continue
    f = P[a]
    if f.get("strings") or f.get("name"):
        continue
    anon.append(a)

# for each anonymous helper, look at its callers: a caller counts as "named" if it has strings/name
owner = defaultdict(list)
unowned = []
for a in anon:
    f = P[a]
    callers = [c for c in (f.get("callers") or []) if c in P]
    named = []
    for c in callers:
        g = P[c]
        if g.get("name"):
            named.append(g["name"])
        elif g.get("strings"):
            named.append("0x%x (has strings)" % c)
    if named and len(set(named)) == 1:
        owner[named[0]].append(a)
    elif named:
        owner["[mixed callers]"].append(a)
    else:
        unowned.append(a)

rows = []
for k, v in owner.items():
    rows.append((k, len(v), sum((P[a].get("size") or 0) for a in v)))
rows.sort(key=lambda r: -r[2])
tot = sum((P[a].get("size") or 0) for a in anon)
print("anonymous (no name, no string) un-cited domain functions: %d / %d bytes" % (len(anon), tot))
print("owned by a single named caller: %d groups covering %d bytes"
      % (len([r for r in rows if not r[0].startswith("[")]),
         sum(r[2] for r in rows if not r[0].startswith("["))))
print("mixed callers: %d bytes | no named caller at all: %d fns / %d bytes"
      % (sum(r[2] for r in rows if r[0].startswith("[")), len(unowned),
         sum((P[a].get("size") or 0) for a in unowned)))
print("top owners:")
for k, n, b in rows[:12]:
    print("   %-46s %4d fns %8d B" % (k[:46], n, b))

DOC = os.path.join(RE, "SWEEP.md")
S = u"\n## 匿名辅助的**归属聚类**（按具名调用者）\n\n"
S += (u"无名字、无字符串的未引用领域函数共 **%d 个 / %d 字节**。按「谁调用它」聚类后：\n\n"
      u"* **只被同一个具名函数调用**（⇒ 可视为该函数的私有机制）：**%d 个组 / %d 字节**\n"
      u"* 调用者混合（多个具名调用者）：%d 字节\n"
      u"* **完全没有任何具名调用者**：**%d 个 / %d 字节** ← 这批连来源都没有，是最难的一档\n\n"
      u"| 归属（具名调用者） | 函数数 | 字节 |\n|---|---:|---:|\n") % (
    len(anon), tot,
    len([r for r in rows if not r[0].startswith("[")]),
    sum(r[2] for r in rows if not r[0].startswith("[")),
    sum(r[2] for r in rows if r[0].startswith("[")),
    len(unowned), sum((P[a].get("size") or 0) for a in unowned))
for k, n, b in rows[:40]:
    S += u"| `%s` | %d | %d |\n" % (k.replace("|", "/")[:60], n, b)
S += (u"\n**口径**：这是「来源证据」，不是身份 —— 归属只说明它属于某函数的私有机制，"
      u"**不说明它做什么**。故本表仍属 tier C（`SWEEP.md` 被排除在引用扫描之外）。\n")
io.open(DOC, "a", encoding="utf-8", newline="\n").write(S)
print("appended the ownership clustering to re/SWEEP.md (not committed)")
