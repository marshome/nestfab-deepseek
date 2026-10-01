# -*- coding: utf-8 -*-
"""Honest coverage metric + a ranked work list of what is still NOT reversed.

Denominator: every function reachable from the export table (the code the library can actually run).
Numerator:   functions whose ENTRY address is cited in re/*.md or in the lcns/ sources.

This is a proxy, not a proof of equivalence: being cited means "we looked at it and wrote down what
it is", not "this project reproduces it instruction for instruction". The registry in
include/lcns/recovery.hpp is what tracks the latter.
"""
import glob
import io
import os
import re
import sys
from collections import Counter, deque

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from covlib import classify, classify_identity, has_identity_evidence  # noqa: E402

RE = r"D:\Nesting\nestfab\re"
LC = r"D:\Nesting\nestfab\lcns"
P = load_prof()
TOTAL_BYTES = sum((v.get("size") or 0) for v in P.values())
print("profile: %d functions, %d bytes" % (len(P), TOTAL_BYTES))

# ---------------------------------------------------------------- exports
exp = EXPORTS
print("EXPORTS type:", type(exp).__name__, "len:", len(exp) if hasattr(exp, "__len__") else "?")
sample = list(exp)[:2]
print("sample:", sample)
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

exports = []
for e in exp:
    a = exp_addr(e)
    if a:
        exports.append(a)
exports = sorted(set(exports))
print("export entries with an address: %d (of %d)" % (len(exports), len(exp)))

# ---------------------------------------------------------------- vtables -> virtual edges
# A direct-call graph misses every virtual dispatch, which is most of this binary's structure.
# vtables.json gives 443 (vtable_rva, slots) pairs; a function that materialises an object stores
# the ADDRESS POINT (vtable_rva + 16, see REPORT section 7.1) so both forms are matched.
vt_slots = {}
try:
    vts = json.load(io.open(os.path.join(RE, "vtables.json"), encoding="utf-8"))
    for _name, v in vts.items():
        rva = v.get("vtable_rva")
        slots = [s for s in (v.get("slots") or []) if s in P]
        if rva is None or not slots:
            continue
        vt_slots.setdefault(rva, []).extend(slots)
        vt_slots.setdefault(rva + 16, []).extend(slots)
    print("vtables with slots: %d (address points included)" % (len(vt_slots) // 2))
except Exception as e:
    print("could not load vtables.json:", e)

# ---------------------------------------------------------------- reachable set
seen = set()
q = deque()
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
reach_bytes = sum((P[a].get("size") or 0) for a in seen)
print("reachable from the exports: %d functions, %d bytes (%.1f%% of all code)"
      % (len(seen), reach_bytes, 100.0 * reach_bytes / TOTAL_BYTES))

# ---------------------------------------------------------------- cited set
# IMPORTANT: never let this metric count its own output. The raw data tables and the generated
# reports are excluded, otherwise listing a function as "not covered" would mark it as covered.
SKIP_NAMES = {"exports_table.csv", "exports_table.json", "exports_table.md",
              "UNCOVERED_RANKED.md", "RECOVERY_STATUS.md", "vtables.json", "prof2.pkl",
              "g_coverage.py", "results.csv",
              # IDENTIFIED.md is a GENERATED INVENTORY (re/g_identify.py). It records provenance and
              # shape for functions whose bodies nobody has read, and 80% of its rows carry no
              # identity at all ("shape only"). Letting it count as "cited" would move this metric
              # from ~32% to ~90% while nothing was actually reversed, so it is excluded here and
              # reported as its own, clearly weaker tier further down.
              "IDENTIFIED.md", "identified_summary.json", "g_identify.py"}
addr_re = re.compile(r"0x([0-9A-Fa-f]{3,8})")
cited = Counter()
files = []
for pat in ("*.md", "*.py"):
    files += glob.glob(os.path.join(RE, pat))
for root, _d, fs in os.walk(LC):
    if os.sep + "build" in root:
        continue
    for f in fs:
        if f.endswith((".cpp", ".hpp", ".md", ".py", ".txt", ".svg")) and f not in SKIP_NAMES:
            files.append(os.path.join(root, f))
files = [f for f in files if os.path.basename(f) not in SKIP_NAMES]
for fp in files:
    try:
        t = io.open(fp, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    for m in addr_re.finditer(t):
        v = int(m.group(1), 16)
        if v in P:
            cited[v] += 1
print("distinct function entries cited somewhere in re/ or lcns/: %d" % len(cited))

hit = sorted(set(cited) & seen)
hit_bytes = sum((P[a].get("size") or 0) for a in hit)
print()
print("=== COVERAGE over the reachable set ===")
print("   reachable functions : %6d  (%d bytes)" % (len(seen), reach_bytes))
print("   cited reachable     : %6d  (%d bytes)  -> %.1f%% of reachable bytes"
      % (len(hit), hit_bytes, 100.0 * hit_bytes / max(1, reach_bytes)))
print("   cited anywhere      : %6d" % len(cited))
exp_hit = [a for a in exports if a in cited]
print("   exports with a cited entry: %d / %d" % (len(exp_hit), len(exports)))

# ---------------------------------------------------------------- ranked work list
missing = sorted((a for a in seen if a not in cited), key=lambda a: -(P[a].get("size") or 0))


def hint_of(f):
    """The profile stores strings as (address, text) tuples."""
    for s in (f.get("strings") or []):
        if isinstance(s, (tuple, list)) and len(s) == 2:
            return str(s[1])
        if isinstance(s, str):
            return s
    if f.get("data_refs"):
        return "data@0x%x" % f["data_refs"][0]
    return ""


print()
print("=== top 35 NOT-cited reachable functions (the concrete work list) ===")
print("   %-10s %-8s %-7s %-8s %s" % ("rva", "size", "callers", "nins", "first string / hint"))
for a in missing[:35]:
    f = P[a]
    print("   0x%-8x %-8s %-7d %-8s %s" % (a, f.get("size"), len(f.get("callers") or []),
                                           f.get("nins"), hint_of(f)[:58]))
mb = sum((P[a].get("size") or 0) for a in missing)
print()
print("   not-cited reachable: %d functions, %d bytes (%.1f%% of reachable)"
      % (len(missing), mb, 100.0 * mb / max(1, reach_bytes)))

# ---------------------------------------------------------------- third party vs domain code
# Per the human instruction (goal round 2) third party libraries are DOWNLOADED AND LINKED, not
# reversed, so they are excluded -- but explicitly, via third_party/fetch.py's evidence-based
# manifest, and split from the toolchain (libstdc++/MinGW) which is excluded for the same reason.
#
# ROUND 7 CORRECTION: exclusion now needs IDENTITY evidence (see covlib.classify_identity): the
# function's own name, or all of its strings, or a third party SOURCE PATH. Before this the rule
# fired on any referenced string, including the names of functions it merely CALLS, which moved 64
# domain functions / 125,925 bytes out of the work list on no real evidence. The old loose rule is
# still computed, so the size of that bias stays visible and auditable.
buckets = {"toolchain": [], "third_party": [], "domain": []}
loose = {"toolchain": [], "third_party": [], "domain": []}
for a in missing:
    buckets[classify_identity(a)].append(a)
    loose[classify(a)].append(a)
vb = sum((P[a].get("size") or 0) for a in buckets["third_party"])
tb = sum((P[a].get("size") or 0) for a in buckets["toolchain"])
db = sum((P[a].get("size") or 0) for a in buckets["domain"])
ldb = sum((P[a].get("size") or 0) for a in loose["domain"])
print()
print("=== of the un-cited reachable code (identity evidence required, round 7) ===")
print("   third party to LINK (see third_party/README.md): %5d fns, %8d B (%.1f%% of reachable)"
      % (len(buckets["third_party"]), vb, 100.0 * vb / max(1, reach_bytes)))
print("   toolchain libstdc++/MinGW                      : %5d fns, %8d B (%.1f%%)"
      % (len(buckets["toolchain"]), tb, 100.0 * tb / max(1, reach_bytes)))
print("   libcns DOMAIN code STILL TO REVERSE            : %5d fns, %8d B (%.1f%%)"
      % (len(buckets["domain"]), db, 100.0 * db / max(1, reach_bytes)))
print("   (the previous loose rule reported %d fns / %d B of domain -- %d B of that was excluded"
      % (len(loose["domain"]), ldb, max(0, db - ldb)))
print("    merely because a CALLED function's name looked like a library symbol)")
print()
# The honest second number: within the domain bucket, how much has ANY identification channel?
# A function with no name, no string and no data reference cannot be identified by the current
# tooling at all -- that, not "cited", is the real work list.
noev = [a for a in buckets["domain"] if not has_identity_evidence(a)]
nev_b = sum((P[a].get("size") or 0) for a in noev)
print("=== the real work list inside that domain bucket ===")
print("   have NO identification evidence at all (no name, no string, no data ref):")
print("      %5d fns, %8d B (%.1f%% of reachable)" % (len(noev), nev_b, 100.0 * nev_b / max(1, reach_bytes)))
print("   have a name or a string, i.e. CAN be identified by the current tooling:")
print("      %5d fns, %8d B" % (len(buckets["domain"]) - len(noev), db - nev_b))
print()
# --- tier report (goal round 8): the metric must not conflate three very different things ---------
#   A. implemented in code   -- the address appears in lcns/**.cpp|hpp, i.e. something was written
#   B. documented            -- the address appears in a re/ findings doc (read and described)
#   C. identified by evidence-- only provenance/shape is on record (re/IDENTIFIED.md, generated)
#   D. no record at all      -- nothing anywhere
import glob as _glob  # noqa: E402
_code, _docs = set(), set()
for fp in _glob.glob(os.path.join(LC, "**", "*.cpp"), recursive=True) + \
        _glob.glob(os.path.join(LC, "**", "*.hpp"), recursive=True):
    if os.sep + "build" in fp:
        continue
    try:
        t = io.open(fp, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    for m in addr_re.finditer(t):
        v = int(m.group(1), 16)
        if v in P:
            _code.add(v)
_cited_set = set(cited)   # `cited` above is a Counter, not a set
_in_code = len(_code & seen)
_in_docs = len((_cited_set & seen) - _code)
ident = {}
try:
    ident = json.load(io.open(os.path.join(RE, "identified_summary.json"), encoding="utf-8"))
except Exception:
    pass
print("=== tiers over the reachable set (they must never be added together) ===")
print("   A implemented in lcns code (address cited in lcns/**.cpp|hpp) : %5d fns" % _in_code)
print("   B documented in re/ findings docs                            : %5d fns" % _in_docs)
print("   C identified by evidence only (re/IDENTIFIED.md, generated)   : %5d fns, %d B"
      % (ident.get("total", 0), ident.get("bytes", 0)))
if ident.get("by_evidence"):
    parts = ["%s %d" % (k, v["fns"]) for k, v in sorted(ident["by_evidence"].items(),
                                                       key=lambda kv: -kv[1]["bytes"])]
    print("        by evidence class: " + ", ".join(parts))
    print("        NOTE: 'shape only' means no identity at all is known -- size, instruction count")
    print("        and branch shape. Tier C is NOT reverse engineering; it is a worklist.")
print("   D no record at all                                          : %5d fns"
      % max(0, len(seen) - _in_code - _in_docs - ident.get("total", 0)))
print()
print("=== top 25 DOMAIN functions still not looked at ===")
for a in sorted(buckets["domain"], key=lambda x: -(P[x].get("size") or 0))[:25]:
    f = P[a]
    print("   0x%-8x %-7s %-4d %s" % (a, f.get("size"), len(f.get("callers") or []), hint_of(f)[:60]))

# ---------------------------------------------------------------- write the list
out = [u"# 未覆盖函数清单（按体积排序，来自 `re/g_coverage.py`）\n",
       u"口径：**分母** = 从导出表出发沿 `callees` 可达的全部函数（库真正能跑到的代码）；",
       u"**分子** = 其入口地址在 `re/*.md` 或 `lcns/**` 中被引用过的函数。",
       u"这是**代理指标**：被引用只说明\"看过并写下了它是什么\"，不等于逐指令复现（后者由 "
       u"`include/lcns/recovery.hpp` 的登记表跟踪）。\n",
       u"- 可达函数：**%d**（%d 字节）" % (len(seen), reach_bytes),
       u"- 已被引用：**%d**（%d 字节）= **%.1f%%**" % (len(hit), hit_bytes,
                                                     100.0 * hit_bytes / max(1, reach_bytes)),
       u"- 导出条目中有被引用入口的：**%d / %d**" % (len(exp_hit), len(exports)),
       u"- 未引用：**%d** 个函数、**%d** 字节（%.1f%%）\n"
       % (len(missing), mb, 100.0 * mb / max(1, reach_bytes)),
       u"其中：**第三方/工具链** %d 个函数、%d 字节（%.1f%% of reachable，无需逆向）；"
       u"**lcns 领域代码** %d 个函数、%d 字节（**%.1f%%**，这才是真正剩下的工作）\n"
       % (len(vendor), vb, 100.0 * vb / max(1, reach_bytes),
          len(domain), db, 100.0 * db / max(1, reach_bytes)),
       u"## 未引用里最大的 120 个\n",
       u"| RVA | 字节 | 调用者数 | 指令数 | 线索 |", u"|---|---:|---:|---:|---|"]
for a in missing[:120]:
    f = P[a]
    hint = hint_of(f)[:70].replace("|", "\\|")
    out.append(u"| `0x%x` | %s | %d | %s | %s |" % (a, f.get("size"),
                                                    len(f.get("callers") or []),
                                                    f.get("nins"), hint))
io.open(os.path.join(RE, "UNCOVERED_RANKED.md"), "w", encoding="utf-8",
        newline="\n").write("\n".join(out) + "\n")
print()
print("wrote re/UNCOVERED_RANKED.md")
