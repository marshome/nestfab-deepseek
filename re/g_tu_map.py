# -*- coding: utf-8 -*-
"""Reconstruct the ORIGINAL TRANSLATION-UNIT map of libcns, v2.

Only ~156 of the 6,181 reachable functions carry an assertion path in their OWN strings (message
builders are separate functions). So the label is propagated in three stages:

  1. DIRECT     -- the function references a `..\\dir\\file.cpp` path itself
  2. VTABLE     -- the function is a slot of a vtable whose demangled class name maps to a TU
                   (e.g. Multi::TilingNester -> ..\\multi\\tiling_nester.cpp)
  3. CALLGRAPH  -- label propagation: a function whose labelled neighbours agree is assigned their
                   label (assertion builders sit inside the TU that calls them)

Outputs re/TU_MAP.md with the per-TU work list.
"""
import io
import os
import re
from collections import Counter, defaultdict

from covlib import LC, PROF, RE, TOTAL_BYTES, cited_set, hint_of, reachable
import json

PATH_RE = re.compile(r"(\.\.[\\/][\w\\/ .+-]*?\.(?:cpp|hpp|h|cc|cxx|inl))"
                     r"|((?:[\w.+-]+[\\/])*(?:boost|libstdc\+\+|cryptopp|coin|Clp|Osi|absl|jsoncpp|"
                     r"include)[\\/][\w\\/ .+-]*?\.(?:hpp|h|ipp|cpp|tcc))", re.I)

# class name fragment -> original TU
KEY2TU = [
    ("TilingNester", r"..\multi\tiling_nester.cpp"),
    ("RowNester", r"..\multi\row_nester.cpp"),
    ("RectangleNester", r"..\multi\rectangle_nester.cpp"),
    ("FilterNester", r"..\multi\filter_nester.cpp"),
    ("FlipNester", r"..\multi\flip_nester.cpp"),
    ("LimitedNester", r"..\multi\limited_nester.cpp"),
    ("CompactNester", r"..\multi\compact_nester.cpp"),
    ("DatabaseNester", r"..\multi\database_nester.cpp"),
    ("MultiTorchNester", r"..\multi\multitorch_nester.cpp"),
    ("CompositeNester", r"..\multi\composite_nester.cpp"),
    ("NestingNester", r"..\multi\nesting_nester.cpp"),
    ("BestNester", r"..\multi\pack_nester.cpp"),
    ("KnapsackNester", r"..\multi\pack_nester.cpp"),
    ("RecursiveNester", r"..\multi\pack_nester.cpp"),
    ("BucketManager", r"..\nesting\algos\bucket_manager.hpp"),
    ("TreeDb", r"..\nesting\algos\tree_db.cpp"),
    ("tree_db", r"..\nesting\algos\tree_db.cpp"),
    ("NestingContext", r"..\multi\nesting_context.cpp"),
    ("Problem", r"..\structure\problem.cpp"),
    ("Equivalent", r"..\verify\equivalent.cpp"),
    ("FloatFiller", r"..\multi\float_filler.cpp"),
    ("Marker", r"..\multi\marker.cpp"),
    ("Stats", r"..\structure\stats.cpp"),
    ("PackerCache", r"..\tiling\packer_cache.cpp"),
    ("Optimizer", r"..\tiling\optimizer.cpp"),
    ("AutomaticCluster", r"..\structure\automatic_cluster.cpp"),
    ("TextIo", r"..\structure\text_io.cpp"),
    ("MultitorchEval", r"..\structure\multitorch_eval.cpp"),
    ("AlgoParameters", r"..\nesting\algos\algo_parameters.cpp"),
    ("MultinestingOptimizer", r"..\nesting\algos\multinesting_optimizer.cpp"),
    ("SheetOptimizer", r"..\nesting\algos\sheet_optimizer.cpp"),
    ("Svg", r"..\structure\svg_io.cpp"),
    ("RowNestCore", r"..\multi\row_nester.cpp"),
    ("Squeezer", r"..\multi\row_nester.cpp"),
    ("NoFit", r"..\nesting\algos\no_fit.cpp"),
    ("Database", r"..\multi\database.cpp"),
    ("Nesting", r"..\nesting\nesting.cpp"),
    ("Shape", r"..\structure\shape.cpp"),
    ("Sheet", r"..\structure\sheet.cpp"),
    ("Part", r"..\structure\part.cpp"),
    ("Matrix", r"..\common_cut\matrix.cpp"),
]

reach = reachable()
cited = cited_set()
print("reachable: %d functions / %d bytes" % (len(reach), sum(PROF[a]["size"] for a in reach)))


def is_vendor_tu(tu):
    low = tu.lower()
    return any(k in low for k in ("boost", "crypto", "coin", "clp", "osi", "absl", "jsoncpp",
                                  "libstdc++", "include\\", "/usr/", "c:\\users\\", "minGW"))


label = {}
how = {}

# ---- stage 1: direct path strings
for a in reach:
    f = PROF[a]
    hits = []
    for s in (f.get("strings") or []):
        text = s[1] if isinstance(s, (tuple, list)) and len(s) == 2 else str(s)
        for m in PATH_RE.finditer(text):
            hits.append((m.group(1) or m.group(2)).replace("/", "\\"))
    if hits:
        cpp = [h for h in hits if h.lower().endswith((".cpp", ".cc", ".cxx"))]
        full = sorted(hits, key=len)[-1]
        pick = sorted(cpp or hits, key=len)[-1]
        tu = full if full.lower().startswith("..") else pick
        label[a] = tu
        how[a] = "direct"

# ---- stage 2: vtable class names
vt_members = {}
try:
    vts = json.load(io.open(os.path.join(RE, "vtables.json"), encoding="utf-8"))
    for name, v in vts.items():
        dem = v.get("demangled") or name
        for frag, tu in KEY2TU:
            if frag in dem:
                for s in (v.get("slots") or []):
                    if s in PROF and s not in label:
                        label[s] = tu
                        how[s] = "vtable:" + frag
                break
except Exception as e:
    print("vtables:", e)
print("after stages 1+2: labelled %d / %d" % (len(label), len(reach)))

# ---- stage 3: call graph label propagation, STRICT first then loose
adj = {}
for a in reach:
    f = PROF[a]
    nb = [c for c in (f.get("callees") or []) if c in reach]
    nb += [c for c in (f.get("callers") or []) if c in reach]
    adj[a] = nb

# 3a. strict: assign only when EVERY labelled neighbour agrees (this is how a TU's private helpers
#     and its assertion builders get bound to that TU, without hub bleed)
for _round in range(12):
    changed = 0
    for a in reach:
        if a in label:
            continue
        votes = Counter(label[n] for n in adj.get(a, ()) if n in label)
        if len(votes) == 1:
            label[a] = next(iter(votes))
            how[a] = "graph-strict"
            changed += 1
    if not changed:
        break
strict_n = sum(1 for v in how.values() if v == "graph-strict")
print("after strict propagation: labelled %d (strict added %d)" % (len(label), strict_n))

# 3b. loose: a strong majority, at least 3 votes, and never from a known hub TU (a TU with a huge
#     number of functions is almost certainly bleeding, so it is not allowed to absorb more)
hub_tus = {tu for tu, n in Counter(label.values()).items() if n > 300}
for _round in range(12):
    changed = 0
    for a in reach:
        if a in label:
            continue
        votes = Counter(label[n] for n in adj.get(a, ()) if n in label and label[n] not in hub_tus)
        if not votes:
            continue
        top, n = votes.most_common(1)[0]
        total = sum(votes.values())
        if n >= 3 and n * 10 >= total * 8:
            label[a] = top
            how[a] = "graph"
            changed += 1
    if not changed:
        break
print("after strict+loose: labelled %d / %d (%.1f%% of bytes)"
      % (len(label), len(reach),
         100.0 * sum(PROF[a]["size"] for a in label) / sum(PROF[a]["size"] for a in reach)))

unl = [a for a in reach if a not in label]
unl_b = sum((PROF[a].get("size") or 0) for a in unl)

# ---- aggregate
tu_n = Counter()
tu_b = Counter()
tu_cb = Counter()
for a in reach:
    tu = label.get(a)
    if tu is None:
        continue
    tu_n[tu] += 1
    tu_b[tu] += PROF[a]["size"] or 0
    if a in cited:
        tu_cb[tu] += PROF[a]["size"] or 0

rows = [{"tu": tu, "n": tu_n[tu], "bytes": tu_b[tu], "cited_bytes": tu_cb[tu],
         "vendor": is_vendor_tu(tu)} for tu in tu_b]
rows.sort(key=lambda r: -(r["bytes"] - r["cited_bytes"]))
own = [r for r in rows if not r["vendor"]]
ven = [r for r in rows if r["vendor"]]
own_b = sum(r["bytes"] for r in own)
own_c = sum(r["cited_bytes"] for r in own)
print("own TUs: %d (%d B, cited %d B = %.1f%%) ; vendor TUs: %d (%d B)"
      % (len(own), own_b, own_c, 100.0 * own_c / max(1, own_b), len(ven),
         sum(r["bytes"] for r in ven)))
print("unlabelled: %d functions / %d bytes" % (len(unl), unl_b))
by_how = Counter(how.values())
print("label source:", dict(by_how))

out = [u"# 原工程 TU 地图（由断言路径 + 虚表类名 + 调用图传播重建）\n",
       u"二进制把 `..\\dir\\file.cpp` 烧进断言串；但断言串在**独立的消息构造器**里，",
       u"所以只有少数函数自带路径。本表用三级标注把它铺满可达集：\n",
       u"1. **direct** —— 函数自己引用了 `..\\dir\\file.cpp`",
       u"2. **vtable** —— 函数是某个 vtable 的 slot，而其 demangle 类名可映射到 TU",
       u"3. **graph** —— 调用图标签传播（多数已标注邻居一致时赋值）\n",
       u"- 可达 **%d** 个 / %d 字节；已归位 **%d** 个 / %.1f%% 字节"
       % (len(reach), sum(PROF[a]["size"] for a in reach), len(label),
          100.0 * sum(PROF[a]["size"] for a in label) / sum(PROF[a]["size"] for a in reach)),
       u"- 自有 TU：**%d** 个 / %d 字节，其中**已引用 %d 字节 = %.1f%%**"
       % (len(own), own_b, own_c, 100.0 * own_c / max(1, own_b)),
       u"- 第三方 TU：%d 个 / %d 字节（按已分类处理，不列入待逆向）"
       % (len(ven), sum(r["bytes"] for r in ven)),
       u"- 仍无标签：**%d** 个 / **%d** 字节（需逐个按调用者/字符串反推）\n"
       % (len(unl), unl_b),
       u"## 自有 TU：待逆向字节降序\n",
       u"| 原 TU | 函数数 | 字节 | 已引用 | 未引用 | 进度 |",
       u"|---|---:|---:|---:|---:|---:|"]
for r in own:
    pct = 100.0 * r["cited_bytes"] / max(1, r["bytes"])
    out.append(u"| `%s` | %d | %d | %d | **%d** | %.0f%% |"
               % (r["tu"], r["n"], r["bytes"], r["cited_bytes"],
                  r["bytes"] - r["cited_bytes"], pct))
out.append(u"\n## 第三方 TU（已分类）\n")
out.append(u"| TU | 函数数 | 字节 |")
out.append(u"|---|---:|---:|")
for r in sorted(ven, key=lambda x: -x["bytes"])[:30]:
    out.append(u"| `%s` | %d | %d |" % (r["tu"], r["n"], r["bytes"]))
out.append(u"\n## 仍无标签的最大 80 个（优先处理，逐个反推）\n")
out.append(u"| RVA | 字节 | 调用者 | 线索 |")
out.append(u"|---|---:|---:|---|")
for a in sorted(unl, key=lambda x: -(PROF[x].get("size") or 0))[:80]:
    f = PROF[a]
    out.append(u"| `0x%x` | %s | %d | %s |"
               % (a, f.get("size"), len(f.get("callers") or []),
                  hint_of(f)[:64].replace("|", "\\|")))
io.open(os.path.join(RE, "TU_MAP.md"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("wrote re/TU_MAP.md")
print()
print("=== own TUs, worst first (top 20) ===")
for r in own[:20]:
    print("   %-48s %4d fns %8d B  uncited %8d B  (%.0f%% cited)"
          % (r["tu"][-48:], r["n"], r["bytes"], r["bytes"] - r["cited_bytes"],
             100.0 * r["cited_bytes"] / max(1, r["bytes"])))
