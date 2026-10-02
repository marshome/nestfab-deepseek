# -*- coding: utf-8 -*-
"""The honest bottom line of the naming work: how many not-cited functions are now named, and from what.

Usage: python g_names_gain.py

The citation set now reads re/name_registry.json, so the naming work is part of the coverage number. That makes it easy to
fool yourself in either direction, so this tool states the two measurements separately:

  * the not-cited set as it is NOW, with the registry included as a citation source (what g_coverage.py reports), and
  * the not-cited set with the registry REMOVED, which is the work list as it stood before the harvest -- and, inside it,
    how many functions the reporter channels name directly.

The difference between the two is the naming work's contribution and nothing else.
"""
import io
import json
import os
import re
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import covlib                     # noqa: E402
from covlib import PROF, classify_identity  # noqa: E402

ADDR = re.compile(r"0x([0-9A-Fa-f]{3,8})")


def reachable():
    seen = set()
    q = deque()
    for a in covlib.EXPORT_ADDRS:
        if a in PROF and a not in seen:
            seen.add(a)
            q.append(a)
    slots = covlib._vt_slots()
    while q:
        a = q.popleft()
        info = PROF.get(a, {})
        nxt = list(info.get("callees") or [])
        for d in (info.get("data_refs") or []):
            nxt.extend(slots.get(d, ()))
        for c in nxt:
            if c in PROF and c not in seen:
                seen.add(c)
                q.append(c)
    return seen


def cited_without_registry():
    skip = set(covlib.SKIP_NAMES)
    files = [p for p in os.listdir(covlib.RE) if p.endswith((".md", ".py"))]
    files = [os.path.join(covlib.RE, f) for f in files]
    for root, _d, fs in os.walk(covlib.LC):
        if os.sep + "build" in root:
            continue
        for f in fs:
            if f.endswith((".cpp", ".hpp", ".md", ".py", ".txt", ".svg")):
                files.append(os.path.join(root, f))
    cited = set()
    for fp in files:
        if os.path.basename(fp) in skip:
            continue
        try:
            text = io.open(fp, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for m in ADDR.finditer(text):
            v = int(m.group(1), 16)
            if v in PROF:
                cited.add(v)
    return cited


def main():
    reg = json.load(io.open(os.path.join(covlib.RE, "name_registry.json"), encoding="utf-8"))

    def direct_name(a):
        value = reg.get("0x%X" % a) or {}
        own = [v for v in (value.get("via") or []) if not v.startswith("via ")]
        if value.get("methods") and own:
            return (value["methods"][0], own[0])
        return None

    seen = reachable()
    cited_now = set(covlib.cited_set())
    cited_old = cited_without_registry()
    missing_now = [a for a in seen if a not in cited_now]
    missing_old = [a for a in seen if a not in cited_old]
    named = [(a, direct_name(a)) for a in missing_old if direct_name(a)]
    dom = [(a, n) for a, n in named if classify_identity(a) == "domain"]

    size = lambda a: (PROF[a].get("size") or 0)
    print("reachable                                : %5d functions" % len(seen))
    print("not cited now (registry counted)         : %5d functions / %8d bytes" % (len(missing_now), sum(map(size, missing_now))))
    print("not cited without the registry           : %5d functions / %8d bytes" % (len(missing_old), sum(map(size, missing_old))))
    print("  of those, named from their own call site: %5d functions / %8d bytes" % (len(named), sum(size(a) for a, _ in named)))
    print("     and classified as domain            : %5d functions / %8d bytes" % (len(dom), sum(size(a) for a, _ in dom)))
    print("")
    print("the largest of them:")
    for a, (name, channel) in sorted(dom, key=lambda kv: -size(kv[0]))[:20]:
        print("    0x%-8X %6d B  %-34s (%s)" % (a, size(a), name, channel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
