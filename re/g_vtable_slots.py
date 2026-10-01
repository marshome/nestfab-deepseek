# -*- coding: utf-8 -*-
"""re/VTABLE_SLOTS.md -- the vtable-slot identity channel, grouped by class.

Goal round 9. Round 8's inventory found 595 reachable un-cited domain functions that are slots of a
known vtable (re/vtables.json). "slot k of Multi::TilingNester" is a real identity -- not a guess --
because the vtable order is recovered data, so those functions move from "shape only" to
"identified". This script writes them out grouped by class, together with each class's full method
table, which is also the map of where the strategy Run bodies live.

Only rows with a vtable-slot identity are emitted, and the document says so. Functions whose only
record is a fingerprint stay in re/IDENTIFIED.md and are NOT claimed here.
"""
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict, deque

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from covlib import classify_identity  # noqa: E402

RE = r"D:\Nesting\nestfab\re"
LC = r"D:\Nesting\nestfab\lcns"
P = load_prof()

vts = json.load(io.open(os.path.join(RE, "vtables.json"), encoding="utf-8"))

# slot address -> (class, index); an address can appear in several classes (shared thunks)
slot_owner = defaultdict(list)
for cls, v in vts.items():
    nm = v.get("demangled") or cls
    for i, s in enumerate(v.get("slots") or []):
        if s:
            slot_owner[s].append((nm, i))

# reachable set (same construction as g_coverage.py)
vt_slots = {}
for _n, v in vts.items():
    rva = v.get("vtable_rva")
    slots = [s for s in (v.get("slots") or []) if s in P]
    if rva is None or not slots:
        continue
    vt_slots.setdefault(rva, []).extend(slots)
    vt_slots.setdefault(rva + 16, []).extend(slots)


def exp_addr(e):
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


exports = sorted({a for a in (exp_addr(e) for e in EXPORTS) if a})
seen, q = set(), deque()
for a in exports:
    if a in P and a not in seen:
        seen.add(a)
        q.append(a)
while q:
    a = q.popleft()
    f = P.get(a, {})
    nxt = list(f.get("callees") or [])
    for d in (f.get("data_refs") or []):
        nxt.extend(vt_slots.get(d, ()))
    for c in nxt:
        if c in P and c not in seen:
            seen.add(c)
            q.append(c)

SKIP = {"exports_table.csv", "exports_table.json", "exports_table.md", "UNCOVERED_RANKED.md",
        "RECOVERY_STATUS.md", "vtables.json", "prof2.pkl", "g_coverage.py", "results.csv",
        "IDENTIFIED.md", "identified_summary.json", "g_identify.py",
        "VTABLE_SLOTS.md", "g_vtable_slots.py"}
addr_re = re.compile(r"0x([0-9A-Fa-f]{3,8})")


def cited(paths):
    got = set()
    for fp in paths:
        if os.path.basename(fp) in SKIP:
            continue
        try:
            t = io.open(fp, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for m in addr_re.finditer(t):
            v = int(m.group(1), 16)
            if v in P:
                got.add(v)
    return got


code = []
docs = [os.path.join(RE, f) for f in os.listdir(RE) if f.endswith((".md", ".py"))]
for root, _d, fs in os.walk(LC):
    if os.sep + "build" in root:
        continue
    for f in fs:
        p = os.path.join(root, f)
        (code if f.endswith((".cpp", ".hpp")) else docs).append(p)
cited_all = cited(code) | cited(docs)

rows = []
for a in sorted(seen - cited_all):
    if classify_identity(a) != "domain":
        continue
    if a in slot_owner:
        rows.append(a)

byclass = defaultdict(list)
for a in rows:
    nm, idx = min(slot_owner[a], key=lambda t: t[1])
    byclass[nm].append((idx, a, P[a].get("size") or 0))

print("vtable-slot identified: %d functions / %d bytes, across %d classes"
      % (len(rows), sum(P[a].get("size") or 0 for a in rows), len(byclass)))

shape = Counter()
for a in rows:
    f = P[a]
    n = f.get("nins") or 0
    shape["tiny (<=32B)" if (f.get("size") or 0) <= 32 else
          "small" if n < 40 else "medium" if n < 200 else "large"] += 1

out = [u"# `re/VTABLE_SLOTS.md` —— 虚表槽位身份档案（**按类分组**）", u"",
       u"由 `re/g_vtable_slots.py` 生成（goal round 9）。", u"",
       u"## 这份档案的**身份**来自哪里", u"",
       u"虚表顺序是**已恢复的数据**（`re/vtables.json`，443 个类），因此",
       u"「**`类名` 的第 k 槽**」是一个**确定的身份**，不是猜测：",
       u"它是该类第 k 个虚函数，调用点由虚表分派决定。",
       u"本轮把这类函数（此前只有结构指纹）提升为**有身份记录**。", u"",
       u"**不在此列的**：只知形态、不知所属类的函数仍留在 `re/IDENTIFIED.md`，本档**不认领**它们。", u"",
       u"## 统计", u"",
       u"| 项 | 数值 |", u"|---|---|",
       u"| 有槽位身份的函数 | **%d** |" % len(rows),
       u"| 字节 | **%d** |" % sum(P[a].get("size") or 0 for a in rows),
       u"| 涉及类数 | **%d** |" % len(byclass), u"",
       u"规模分布：" + u", ".join(u"%s %d" % (k, v) for k, v in shape.most_common()), u"",
       u"## 按类分组", u"",
       u"| 类 | 槽位身份（未引用者） |", u"|---|---|"]
for nm in sorted(byclass, key=lambda c: -sum(s for _i, _a, s in byclass[c])):
    items = sorted(byclass[nm])
    total_slots = len([s for s in (next((v.get("slots") for k, v in vts.items()
                                         if (v.get("demangled") or k) == nm), []) or []) if s])
    cells = ", ".join(u"#%d `0x%x` (%dB)" % (i, a, s) for i, a, s in items)
    out.append(u"| **%s** （%d 槽中 %d 个未引用） | %s |" % (nm, total_slots, len(items), cells))

out += [u"", u"## 每个类的完整方法表（含已引用的槽）", u"",
        u"按类的槽序排列；`*` 表示该槽的函数尚未被引用。这也是**策略 `Run` 体所在的位置**"
        u"（`Multi::NestingNester` / `TilingNester` / `FlipNester` … 的槽 0 即 `Run`）。", u""]
for nm in sorted(byclass, key=lambda c: -sum(s for _i, _a, s in byclass[c]))[:40]:
    slots = next((v.get("slots") for k, v in vts.items()
                  if (v.get("demangled") or k) == nm), None)
    if not slots:
        continue
    parts = []
    for i, s in enumerate(slots):
        if not s:
            parts.append(u"#%d -" % i)
        elif s in cited_all:
            parts.append(u"#%d `0x%x` ✓" % (i, s))
        else:
            parts.append(u"#%d `0x%x` *" % (i, s))
    out.append(u"* **%s**: %s" % (nm, u", ".join(parts)))

io.open(os.path.join(RE, "VTABLE_SLOTS.md"), "w", encoding="utf-8", newline="\n").write(
    u"\n".join(out) + u"\n")
json.dump({"fns": len(rows), "bytes": sum(P[a].get("size") or 0 for a in rows),
           "classes": len(byclass), "shapes": dict(shape)},
          io.open(os.path.join(RE, "vtable_slots_summary.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("wrote re/VTABLE_SLOTS.md")
print("top classes by identified bytes:")
for nm in sorted(byclass, key=lambda c: -sum(s for _i, _a, s in byclass[c]))[:8]:
    print("   %-42s %2d fns %7d B" % (nm, len(byclass[nm]), sum(s for _i, _a, s in byclass[nm])))
