# -*- coding: utf-8 -*-
"""List the reachable functions that belong to one original TU (from the propagated label map).

Usage: python re/g_tu_list.py <tu-substring> [max_rows]

Also writes re/tu/<slug>.md with the full list, so a per-TU dossier can be built round by round.
"""
import io
import os
import sys
from collections import Counter

from covlib import PROF, RE, cited_set, hint_of, reachable
import json
import re

sys.path.insert(0, RE)

PATH_RE = re.compile(r"(\.\.[\\/][\w\\/ .+-]*?\.(?:cpp|hpp|h|cc|cxx|inl))", re.I)
KEY2TU = [
    ("TilingNester", r"..\multi\tiling_nester.cpp"), ("RowNester", r"..\multi\row_nester.cpp"),
    ("RectangleNester", r"..\multi\rectangle_nester.cpp"), ("FilterNester", r"..\multi\filter_nester.cpp"),
    ("FlipNester", r"..\multi\flip_nester.cpp"), ("LimitedNester", r"..\multi\limited_nester.cpp"),
    ("CompactNester", r"..\multi\compact_nester.cpp"), ("DatabaseNester", r"..\multi\database_nester.cpp"),
    ("MultiTorchNester", r"..\multi\multitorch_nester.cpp"), ("CompositeNester", r"..\multi\composite_nester.cpp"),
    ("NestingNester", r"..\multi\nesting_nester.cpp"), ("BestNester", r"..\multi\pack_nester.cpp"),
    ("KnapsackNester", r"..\multi\pack_nester.cpp"), ("RecursiveNester", r"..\multi\pack_nester.cpp"),
    ("BucketManager", r"..\nesting\algos\bucket_manager.hpp"), ("TreeDb", r"..\nesting\algos\tree_db.cpp"),
    ("tree_db", r"..\nesting\algos\tree_db.cpp"), ("NestingContext", r"..\multi\nesting_context.cpp"),
    ("Problem", r"..\structure\problem.cpp"), ("Equivalent", r"..\verify\equivalent.cpp"),
    ("FloatFiller", r"..\multi\float_filler.cpp"), ("Marker", r"..\multi\marker.cpp"),
    ("Stats", r"..\structure\stats.cpp"), ("PackerCache", r"..\tiling\packer_cache.cpp"),
    ("Optimizer", r"..\tiling\optimizer.cpp"), ("AutomaticCluster", r"..\structure\automatic_cluster.cpp"),
    ("TextIo", r"..\structure\text_io.cpp"), ("MultitorchEval", r"..\structure\multitorch_eval.cpp"),
    ("AlgoParameters", r"..\nesting\algos\algo_parameters.cpp"),
    ("MultinestingOptimizer", r"..\nesting\algos\multinesting_optimizer.cpp"),
    ("SheetOptimizer", r"..\nesting\algos\sheet_optimizer.cpp"), ("Svg", r"..\structure\svg_io.cpp"),
    ("RowNestCore", r"..\multi\row_nester.cpp"), ("Squeezer", r"..\multi\row_nester.cpp"),
    ("NoFit", r"..\nesting\algos\no_fit.cpp"), ("Database", r"..\multi\database.cpp"),
    ("Nesting", r"..\nesting\nesting.cpp"), ("Shape", r"..\structure\shape.cpp"),
    ("Sheet", r"..\structure\sheet.cpp"), ("Part", r"..\structure\part.cpp"),
    ("Matrix", r"..\common_cut\matrix.cpp"),
]


def build_labels():
    reach = reachable()
    label, how = {}, {}
    for a in reach:
        hits = []
        for s in (PROF[a].get("strings") or []):
            text = s[1] if isinstance(s, (tuple, list)) and len(s) == 2 else str(s)
            for m in PATH_RE.finditer(text):
                hits.append(m.group(1).replace("/", "\\"))
        if hits:
            cpp = [h for h in hits if h.lower().endswith((".cpp", ".cc", ".cxx"))]
            full = sorted(hits, key=len)[-1]
            label[a] = full if full.lower().startswith("..") else sorted(cpp or hits, key=len)[-1]
            how[a] = "direct"
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
    except Exception:
        pass
    adj = {}
    for a in reach:
        f = PROF[a]
        adj[a] = ([c for c in (f.get("callees") or []) if c in reach]
                  + [c for c in (f.get("callers") or []) if c in reach])
    for _ in range(12):
        ch = 0
        for a in reach:
            if a in label:
                continue
            votes = Counter(label[n] for n in adj[a] if n in label)
            if len(votes) == 1:
                label[a] = next(iter(votes))
                how[a] = "graph-strict"
                ch += 1
        if not ch:
            break
    hub = {t for t, n in Counter(label.values()).items() if n > 300}
    for _ in range(12):
        ch = 0
        for a in reach:
            if a in label:
                continue
            votes = Counter(label[n] for n in adj[a] if n in label and label[n] not in hub)
            if not votes:
                continue
            top, n = votes.most_common(1)[0]
            if n >= 3 and n * 10 >= sum(votes.values()) * 8:
                label[a] = top
                how[a] = "graph"
                ch += 1
        if not ch:
            break
    return reach, label, how


if __name__ == "__main__":
    want = sys.argv[1] if len(sys.argv) > 1 else "svg_io"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    reach, label, how = build_labels()
    cited = cited_set()
    sel = [a for a in reach if want.lower() in (label.get(a) or "").lower()]
    sel.sort(key=lambda a: -(PROF[a].get("size") or 0))
    tot = sum(PROF[a]["size"] for a in sel)
    cit = sum(PROF[a]["size"] for a in sel if a in cited)
    print("TU match %r: %d functions, %d bytes (cited %d = %.1f%%)"
          % (want, len(sel), tot, cit, 100.0 * cit / max(1, tot)))
    print("   %-10s %-7s %-8s %-6s %-6s %s" % ("rva", "size", "callers", "conf", "cited", "hint"))
    for a in sel[:limit]:
        f = PROF[a]
        print("   0x%-8x %-7s %-8d %-6s %-6s %s"
              % (a, f.get("size"), len(f.get("callers") or []), how.get(a, "?")[:6],
                 "yes" if a in cited else "-", hint_of(f)[:56].replace("\n", " ")))
    if sel:
        d = os.path.join(RE, "tu")
        os.makedirs(d, exist_ok=True)
        slug = re.sub(r"[^A-Za-z0-9_.]+", "_", want)
        with io.open(os.path.join(d, slug + ".md"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(u"# TU `%s` -- %d functions / %d bytes\n\n" % (want, len(sel), tot))
            fh.write(u"| RVA | bytes | callers | confidence | cited | hint |\n|---|---:|---:|---|---|---|\n")
            for a in sel:
                f = PROF[a]
                fh.write(u"| `0x%x` | %s | %d | %s | %s | %s |\n"
                         % (a, f.get("size"), len(f.get("callers") or []), how.get(a, "?"),
                            "yes" if a in cited else "-",
                            hint_of(f)[:70].replace("|", "\\|").replace("\n", " ")))
        print("wrote re/tu/%s.md" % slug)
