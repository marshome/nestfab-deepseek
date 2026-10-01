# -*- coding: utf-8 -*-
"""Identification channel for reachable functions that have no name and no strings.

Goal round 8. Round 7 measured that 4,531 of the un-cited domain functions (2,308,205 bytes, 49.4%
of the reachable set) have no name, no string and no data reference -- the existing tooling gives
no identity clue at all, so picking more TUs cannot reach them.

This script builds the missing channel from evidence that DOES exist for every function:
  * vtable slot membership (re/vtables.json): 'slot k of Multi::TilingNester' is a real identity;
  * the recovered name, when there is one;
  * the function's own strings (format text, source paths, option keys);
  * its callers and callees, by name -- provenance is evidence ("called only by X");
  * a structural fingerprint: size, instruction count, thunk / accessor / loop shape.

Output: re/IDENTIFIED.md, one row per reachable not-yet-cited domain function, with the evidence
class spelled out. The document states plainly that these are IDENTIFICATIONS BY EVIDENCE, not
transcriptions: nothing here claims the body was reversed. The fidelity claim stays where it
belongs, in lcns/include/lcns/recovery.hpp.
"""
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict, deque

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from covlib import classify_identity, has_identity_evidence, hint_of  # noqa: E402

RE = r"D:\Nesting\nestfab\re"
LC = r"D:\Nesting\nestfab\lcns"
P = load_prof()

# ---- vtables: slot -> class (a slot address is the function's own vtable entry) ----------------
vt_slot_class = {}
ap_class = {}
vts = json.load(io.open(os.path.join(RE, "vtables.json"), encoding="utf-8"))
for cls, v in vts.items():
    rva = v.get("vtable_rva")
    nm = v.get("demangled") or cls
    if rva is not None:
        ap_class[rva] = nm
        ap_class[rva + 16] = nm
    for i, s in enumerate(v.get("slots") or []):
        if s:
            vt_slot_class.setdefault(s, []).append((nm, i))

# ---- reachable (same construction as g_coverage.py) -------------------------------------------
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

# ---- cited (same exclusions as g_coverage) ----------------------------------------------------
SKIP = {"exports_table.csv", "exports_table.json", "exports_table.md", "UNCOVERED_RANKED.md",
        "RECOVERY_STATUS.md", "vtables.json", "prof2.pkl", "g_coverage.py", "results.csv",
        "IDENTIFIED.md", "g_identify.py"}
addr_re = re.compile(r"0x([0-9A-Fa-f]{3,8})")


def scan(paths):
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


code_files = []
docs_files = [os.path.join(RE, f) for f in os.listdir(RE) if f.endswith((".md", ".py"))]
for root, _d, fs in os.walk(LC):
    if os.sep + "build" in root:
        continue
    for f in fs:
        p = os.path.join(root, f)
        if f.endswith((".cpp", ".hpp")):
            code_files.append(p)
        elif f.endswith((".md", ".txt", ".svg", ".py")):
            docs_files.append(p)
cited_code = scan(code_files)
cited_docs = scan(docs_files)

missing = sorted(seen - cited_code - cited_docs)

# ---- structural fingerprint -------------------------------------------------------------------
RET_RE = re.compile(r"^\s*(ret|jmp)\b")
MOV_LOAD_RET = re.compile(r"^\s*mov\s+rax,\s*(qword|dword)?\s*ptr\s*\[rcx")


def fingerprint(a):
    f = P.get(a, {})
    nins = f.get("nins") or 0
    size = f.get("size") or 0
    try:
        lines = list(disasm(a))
    except Exception:
        lines = []
    ops = [i.mnemonic for i in lines]
    if ops and ops[0] == "jmp" and len(ops) <= 2:
        return "thunk (jmp)"
    if ops and ops[-1] == "ret" and len(ops) <= 4 and any(
            i.mnemonic in ("mov", "movzx", "movsxd") and "rax" in i.op_str for i in lines):
        return "accessor (load and return)"
    if any(i.mnemonic.startswith("j") and i.operands and hasattr(i.operands[0], "imm")
           and i.operands[0].imm and i.operands[0].imm < i.address for i in lines):
        # Honest wording: a backward branch is what is OBSERVED. It usually means a loop, but
        # optimised code also jumps backwards to shared cleanup/epilogue blocks, so this must not
        # be reported as "it is a loop".
        return "has a backward branch (often a loop)"
    if size <= 32:
        return "tiny helper"
    if nins == 0:
        return "unavailable"
    return "straight line / call sequence"


def names_of(addrs, limit=3):
    out = []
    for x in addrs or []:
        nm = (P.get(x, {}) or {}).get("name")
        if nm:
            out.append("0x%x %s" % (x, nm))
        if len(out) >= limit:
            break
    return out


records = []
for a in missing:
    if classify_identity(a) != "domain":
        continue
    f = P.get(a, {})
    strs = [str(s[1]) if isinstance(s, (tuple, list)) and len(s) == 2 else str(s)
            for s in (f.get("strings") or [])]
    strs = [s for s in strs if s]
    name = str(f.get("name") or "")
    vt = vt_slot_class.get(a)
    callers = names_of(f.get("callers"))
    callees = names_of(f.get("callees"))
    shape = fingerprint(a)
    if vt:
        ev = "vtable"
        rec = "slot %d of %s" % (vt[0][1], vt[0][0])
    elif name:
        ev = "name"
        rec = name
    elif strs:
        ev = "strings"
        rec = " | ".join(s[:40] for s in strs[:2])
    elif callers:
        ev = "callers"
        rec = "called by " + "; ".join(callers)
    elif callees:
        ev = "callees"
        rec = "calls " + "; ".join(callees)
    else:
        ev = "shape only"
        rec = "%s, %d ins" % (shape, f.get("nins") or 0)
    records.append((a, f.get("size") or 0, ev, rec, shape, len(f.get("callers") or [])))

by_ev = Counter(r[2] for r in records)
bytes_ev = Counter()
for r in records:
    bytes_ev[r[2]] += r[1]

print("reachable: %d | cited in code: %d | cited in docs only: %d | uncited: %d"
      % (len(seen), len(cited_code & seen), len((cited_docs & seen) - cited_code), len(missing)))
print("domain records written: %d functions / %d bytes"
      % (len(records), sum(r[1] for r in records)))
print()
print("evidence class        functions      bytes")
for k in sorted(by_ev, key=lambda x: -bytes_ev[x]):
    print("  %-16s %7d %10d" % (k, by_ev[k], bytes_ev[k]))
print()
print("shape distribution (what the code looks like, when nothing else is known):")
sh = Counter(r[4] for r in records)
for k, v in sh.most_common():
    print("  %-28s %6d" % (k, v))

# ---- write the document -----------------------------------------------------------------------
out = [u"# 识别清单 `re/IDENTIFIED.md`（**按证据识别，不是逆向**）", u"",
       u"本文件由 `re/g_identify.py` 生成（goal round 8）。它对**可达、但此前从未被引用**的领域函数给出",
       u"**可复核的识别记录**，并逐条标注**证据等级**。", u"",
       u"## 重要：本文件**不**声称这些函数已逆向", u"",
       u"* 这里登记的是**来源与角色**：它属于哪张虚表的第几槽、被谁调用、结构指纹像什么。",
       u"* **没有**逐指令转写其函数体；保真度声明仍然只在 "
       u"[`lcns/include/lcns/recovery.hpp`](../lcns/include/lcns/recovery.hpp) 的登记表里。",
       u"* `g_coverage.py` 因此把指标分三档：**代码中已实现** / **仅文档引用** / **无记录**。",
       u"  本文件让第三档变小，但**不会**让第一档变大 —— 两档必须分开看。", u"",
       u"## 证据等级（由强到弱）", u"",
       u"| 等级 | 含义 |", u"|---|---|",
       u"| `vtable` | 它是某已知虚表的第 k 槽 ⇒ 类名 + 槽号即身份（最强） |",
       u"| `name` | 已有恢复出的名字 |",
       u"| `strings` | 自身引用的字符串（格式串、源码路径、选项键） |",
       u"| `callers` | 被哪些**有名字**的函数调用（来源即证据） |",
       u"| `callees` | 它调用了哪些**有名字**的函数 |",
       u"| `shape only` | 什么名字都没有：只给出结构指纹（尺寸/指令数/形态） |", u"",
       u"## 统计", u"", u"| 证据等级 | 函数数 | 字节 |", u"|---|---:|---:|"]
for k in sorted(by_ev, key=lambda x: -bytes_ev[x]):
    out.append(u"| `%s` | %d | %d |" % (k, by_ev[k], bytes_ev[k]))
out += [u"", u"## 清单", u"",
        u"| 地址 | 字节 | 调用者数 | 证据等级 | 识别记录 | 结构指纹 |",
        u"|---|---:|---:|---|---|---|"]
for a, size, ev, rec, shape, ncall in sorted(records, key=lambda r: -r[1]):
    out.append(u"| `0x%x` | %d | %d | `%s` | %s | %s |"
               % (a, size, ncall, ev, rec.replace("|", "\\|")[:110], shape))
out.append(u"")
io.open(os.path.join(RE, "IDENTIFIED.md"), "w", encoding="utf-8", newline="\n").write("\n".join(out))
json.dump({"total": len(records), "bytes": sum(r[1] for r in records),
           "by_evidence": {k: {"fns": by_ev[k], "bytes": bytes_ev[k]} for k in by_ev},
           "shapes": dict(sh)},
          io.open(os.path.join(RE, "identified_summary.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print()
print("wrote re/IDENTIFIED.md (%d rows) and re/identified_summary.json" % len(records))
