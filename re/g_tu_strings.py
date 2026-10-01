# -*- coding: utf-8 -*-
"""Per-TU dossier tool: vocabulary (strings), call surface and entry points of one original TU.

Usage: python re/g_tu_strings.py <tu-substring> [--funcs N] [--calls]

Writes re/tu/<slug>_strings.md so each TU gets a durable dossier as the goal advances.
"""
import io
import os
import re
import struct
import sys
from collections import defaultdict

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402
from covlib import PROF, RE, cited_set, hint_of  # noqa: E402
import g_tu_list  # noqa: E402


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else "equivalent"
    n_funcs = 30
    show_calls = "--calls" in sys.argv
    if "--funcs" in sys.argv:
        n_funcs = int(sys.argv[sys.argv.index("--funcs") + 1])

    reach, label, how = g_tu_list.build_labels()
    cited = cited_set()
    sel = [a for a in reach if want.lower() in (label.get(a) or "").lower()]
    sel.sort(key=lambda a: -(PROF[a].get("size") or 0))
    tot = sum(PROF[a]["size"] for a in sel)
    cit = sum(PROF[a]["size"] for a in sel if a in cited)
    print("TU %r: %d functions / %d bytes (cited %d = %.1f%%)"
          % (want, len(sel), tot, cit, 100.0 * cit / max(1, tot)))

    # ---------------------------------------------------------------- vocabulary
    seen = defaultdict(set)
    for a in sel:
        for s in (PROF[a].get("strings") or []):
            if isinstance(s, (tuple, list)) and len(s) == 2:
                _addr, text = s
                if text and 1 < len(text) < 110:
                    seen[text].add(a)
    print()
    print("=== strings referenced by the TU (%d distinct) ===" % len(seen))
    for t in sorted(seen):
        where = sorted(seen[t])
        print("   %-72r %s" % (t[:70], " ".join("0x%x" % w for w in where[:3])))

    # ---------------------------------------------------------------- call surface
    print()
    print("=== %d largest functions ===" % min(n_funcs, len(sel)))
    for a in sel[:n_funcs]:
        f = PROF[a]
        callees = sorted({c for c in (f.get("callees") or []) if c in PROF},
                         key=lambda c: -(PROF[c].get("size") or 0))[:6]
        print("   0x%-8x %-7s callers=%-3d conf=%-12s cited=%-4s %s"
              % (a, f.get("size"), len(f.get("callers") or []), how.get(a, "?"),
                 "yes" if a in cited else "-", hint_of(f)[:44].replace("\n", " ")))
        if show_calls:
            for c in callees:
                print("        -> 0x%-8x %-7s %s" % (c, PROF[c].get("size"), hint_of(PROF[c])[:46]))

    # ---------------------------------------------------------------- dossier
    d = os.path.join(RE, "tu")
    os.makedirs(d, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9_.]+", "_", want)
    p = os.path.join(d, slug + "_strings.md")
    with io.open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(u"# TU `%s` -- vocabulary dossier\n\n" % want)
        fh.write(u"%d functions / %d bytes (cited %d = %.1f%%)\n\n"
                 % (len(sel), tot, cit, 100.0 * cit / max(1, tot)))
        fh.write(u"## strings referenced\n\n| string | referenced by |\n|---|---|\n")
        for t in sorted(seen):
            fh.write(u"| `%s` | %s |\n"
                     % (t.replace("|", "\\|").replace("`", "'"),
                        " ".join("`0x%x`" % w for w in sorted(seen[t])[:4])))
        fh.write(u"\n## functions (largest first)\n\n")
        fh.write(u"| RVA | bytes | callers | confidence | cited | hint |\n|---|---:|---:|---|---|---|\n")
        for a in sel:
            f = PROF[a]
            fh.write(u"| `0x%x` | %s | %d | %s | %s | %s |\n"
                     % (a, f.get("size"), len(f.get("callers") or []), how.get(a, "?"),
                        "yes" if a in cited else "-",
                        hint_of(f)[:70].replace("|", "\\|").replace("\n", " ")))
    print()
    print("wrote re/tu/%s_strings.md" % slug)


if __name__ == "__main__":
    main()
