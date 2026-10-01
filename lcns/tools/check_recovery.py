# -*- coding: utf-8 -*-
"""Enforce and publish the recovery inventory.

Checks
  1. the set of ids marked in the code (LCNS_*(id)) is EXACTLY the set registered in
     include/lcns/recovery.hpp -- so a gap can never exist in only one of the two places;
  2. every gap whose `address` is a concrete RVA is mentioned in re/ (REPORT.md or findings_*.md),
     so a "not reversed" claim is always documented;
  3. ids are unique and every entry has a note.

Generates docs/RECOVERY_STATUS.md from the registry (the header is the single source of truth).
Exit code is non-zero on any violation, so this can gate a build.
"""
import glob
import io
import os
import re
import sys
from collections import Counter, defaultdict

LCNS = r"D:\Nesting\nestfab\lcns"
RE = r"D:\Nesting\nestfab\re"
HEADER = os.path.join(LCNS, "include", "lcns", "recovery.hpp")
DOCS = os.path.join(LCNS, "docs", "RECOVERY_STATUS.md")

STATUS_ORDER = ["Recovered", "Structural", "Substituted", "NotReversed", "NotInBinary"]
STATUS_LABEL = {
    "Recovered": ("已恢复", "instruction-level faithful; constants cite RVAs checked by tests"),
    "Structural": ("结构已恢复", "structure/algorithm skeleton recovered; body re-implemented"),
    "Substituted": ("替代实现", "original uses something unavailable here, or heuristic constants were NOT recovered"),
    "NotReversed": ("**未逆向**", "feature exists in the DLL but has NOT been reverse engineered"),
    "NotInBinary": ("非原库", "our own extension"),
}

# ---------------------------------------------------------------- parse the registry
# Line oriented and deliberately dumb: every entry begins a line with {"id", Status::X, "addr",
# and a note is whatever quoted strings follow until the next such line. This cannot be confused by
# braces or quotes inside a note.
txt = io.open(HEADER, encoding="utf-8", newline="").read()
txt = txt.replace("\r\n", "\n").replace("\r", "\n")   # tolerate mixed line endings
body = txt[txt.index("inline constexpr Gap kGaps[]"):]
# terminate on the closing brace that sits alone on a line -- a note may legitimately contain "};"
block = body[body.index("{") + 1: body.index("\n};")]
head_re = re.compile(r'\s*\{"([^"]+)",\s*Status::(\w+),\s*"((?:[^"\\]|\\.)*)",(.*)$')
entries = []
cur = None
for ln in block.split("\n"):
    if ln.lstrip().startswith("//"):
        continue
    m = head_re.match(ln)
    if m:
        if cur:
            entries.append(cur)
        cur = {"id": m.group(1), "status": m.group(2), "address": m.group(3),
               "raw": m.group(4)}
    elif cur is not None:
        cur["raw"] += " " + ln
if cur:
    entries.append(cur)
for e in entries:
    e["note"] = " ".join(" ".join(re.findall(r'"((?:[^"\\]|\\.)*)"', e.pop("raw"))).split())
print("registry entries: %d" % len(entries))
# anything that looks like an entry head but was not parsed must not exist
for ln in block.split("\n"):
    if re.match(r'\s*\{"', ln) and not head_re.match(ln):
        print("   !! unparsed entry head: %r" % ln)

# ---------------------------------------------------------------- parse the code marks
marked = defaultdict(list)
for root, _d, files in os.walk(LCNS):
    if os.sep + "build" in root:
        continue
    for f in files:
        if not f.endswith((".cpp", ".hpp", ".inc")):
            continue
        p = os.path.join(root, f)
        rel = os.path.relpath(p, LCNS)
        if rel.endswith("recovery.hpp"):
            continue
        for i, line in enumerate(io.open(p, encoding="utf-8").read().split("\n"), 1):
            for m in re.finditer(r"LCNS_(RECOVERED|STRUCTURAL|SUBSTITUTED|NOT_REVERSED|NOT_IN_BINARY)"
                                 r"\(([^)]+)\)", line):
                marked[m.group(2)].append((rel, i))

reg_ids = {e["id"] for e in entries}
code_ids = set(marked)
problems = []

dup = [k for k, v in Counter(e["id"] for e in entries).items() if v > 1]
if dup:
    problems.append("duplicate registry ids: %s" % dup)

for i in sorted(reg_ids - code_ids):
    problems.append("registered but NOT marked anywhere in the code: %s" % i)
for i in sorted(code_ids - reg_ids):
    problems.append("marked in the code but NOT registered: %s" % i)

# every concrete RVA must be documented in re/
docs_all = ""
for p in glob.glob(os.path.join(RE, "*.md")):
    docs_all += io.open(p, encoding="utf-8").read()
for e in entries:
    if e["status"] in ("NotReversed", "Substituted"):
        for a in re.findall(r"0x[0-9A-Fa-f]{3,}", e["address"]):
            if a.lower() not in docs_all.lower():
                problems.append("gap %s cites %s which is NOT mentioned in re/ documents"
                                % (e["id"], a))
    if not e["note"]:
        problems.append("gap %s has no note" % e["id"])

# ---------------------------------------------------------------- report + generated table
counts = Counter(e["status"] for e in entries)
print("by status: " + ", ".join("%s=%d" % (s, counts.get(s, 0)) for s in STATUS_ORDER))
print("code marks: %d sites across %d ids" % (sum(len(v) for v in marked.values()), len(code_ids)))

out = [u"# 逆向状态总表（由 `include/lcns/recovery.hpp` 生成）\n",
       u"本工程把代码分成五种状态，**每一处在源码里都有一个可 grep 的标记**，",
       u"并与 `recovery.hpp::kGaps` 登记表逐条对应；`tools/check_recovery.py` 强制"
       u"「代码标记集合 == 登记表集合」，且带具体 RVA 的缺口必须出现在 `re/` 文档中。\n",
       u"| 状态 | 含义 | 条目数 |", u"|---|---|---:|"]
for s in STATUS_ORDER:
    out.append(u"| `%s`（%s） | %s | %d |" % (s, STATUS_LABEL[s][0], STATUS_LABEL[s][1],
                                              counts.get(s, 0)))
out.append(u"\n> 未逆向 ≠ 未知：凡是标为 `NotReversed` 的，都给出了它在二进制中的地址（或明确写了\"-\"），"
           u"说明它**存在**但我们**没有译出**；凡是 `Substituted` 的，说明这里跑的是**替代实现**，"
           u"不是原库算法。\n")
for s in STATUS_ORDER:
    sel = [e for e in entries if e["status"] == s]
    if not sel:
        continue
    out.append(u"\n## %s（%s）\n" % (s, STATUS_LABEL[s][0]))
    out.append(u"| id | DLL 地址 | 说明 | 标记位置 |")
    out.append(u"|---|---|---|---|")
    for e in sel:
        where = marked.get(e["id"], [])
        loc = ", ".join("%s:%d" % (w[0].replace("\\", "/"), w[1]) for w in where[:3]) or "-"
        if len(where) > 3:
            loc += " (+%d)" % (len(where) - 3)
        out.append(u"| `%s` | `%s` | %s | %s |" % (e["id"], e["address"], e["note"], loc))
io.open(DOCS, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("wrote", DOCS)

if problems:
    print("\nPROBLEMS (%d):" % len(problems))
    for p in problems:
        print("   " + p)
    sys.exit(1)
print("\nOK: code marks == registry, and every NotReversed/Substituted RVA is documented in re/")
