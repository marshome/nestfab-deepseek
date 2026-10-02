# -*- coding: utf-8 -*-
"""Where the work has actually gone: commits by area, and how much C++ moved.

Usage: python g_progress.py [--commits 60]

The human asked why `re/` keeps changing while the C++ does not. That is a fair question and it deserves a measurement rather
than an explanation, so this counts:

  * commits touching lcns/ (the deliverable), and commits touching only re/ (the tooling)
  * lines of C++ added and removed per commit, so "touched lcns/" is not confused with "advanced the implementation"
  * what is left to implement, from the export closure sizes, since that is the number that says whether the C++ COULD move

The last part is the one that answers the question. If the exports with an empty closure are exhausted and the rest need bodies
read first, then the C++ cannot move without reading, and the honest report says how much reading stands between here and the
next implementation rather than blaming the tooling.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def run(command, cwd=ROOT):
    assert not (command[0] == "git" and "push" in command), "never push"
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return result.returncode, (result.stdout or "").strip(), (result.stderr or "").strip()


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--commits", type=int, default=60)
    args = parser.parse_args(argv)

    code, out, _err = run(["git", "log", "--format=%h|%s", "-%d" % args.commits])
    rows = [line.split("|", 1) for line in out.split("\n") if "|" in line]

    lcns = []
    re_only = []
    lcns_lines = 0
    for short, subject in rows:
        _c, files, _e = run(["git", "show", "--name-only", "--format=", short])
        _c, stat, _e = run(["git", "show", "--shortstat", "--format=", short])
        names = [f for f in files.split("\n") if f.strip()]
        inserted = re.search(r"(\d+) insertion", stat)
        if any(f.startswith("lcns/") for f in names):
            lcns.append((short, subject, stat.strip()))
            if inserted:
                lcns_lines += int(inserted.group(1))
        elif names:
            re_only.append((short, subject))

    print("the last %d commits:" % len(rows))
    print("    touching lcns/ (the deliverable):  %d, %d lines inserted" % (len(lcns), lcns_lines))
    print("    touching only re/ (the tooling):   %d" % len(re_only))
    print("")
    print("the lcns commits:")
    for short, subject, stat in lcns:
        print("    %s  %-58s %s" % (short, subject[:58], stat))
    print("")

    # what is left, from the export closures: this is the number that says whether the C++ COULD move
    import g_leverage as L
    import g_toolchain as T
    from lib import load_prof
    profile = load_prof()
    table = json.loads(open(os.path.join(HERE, "exports_table.json"), encoding="utf-8").read())
    forwarded = L.forwarded_ordinals()
    ready = 0
    sizes = []
    for entry in table:
        ordinal = (entry.get("ords") or [0])[0]
        if ordinal in forwarded:
            continue
        root = entry["rva"]
        seen = {root}
        queue = [root]
        while queue:
            a = queue.pop()
            for c in (profile.get(a) or {}).get("callees") or []:
                if c in profile and c not in seen:
                    seen.add(c)
                    queue.append(c)
        domain = [a for a in seen if not (a in T.BOILERPLATE or a in getattr(T, "IMPLEMENTED", ()) or a in L.VERIFIED)]
        sizes.append((len(domain), ordinal, root))
        if len(domain) <= 1:
            ready += 1
    sizes.sort()
    total = sum(s[0] for s in sizes)
    print("what stands between here and the next export:")
    print("    exports not yet forwarded:            %d" % len(sizes))
    print("    with an EMPTY domain (writable now):  %d" % ready)
    print("    domain functions to read in total:    %d" % total)
    print("    the smallest five domains:            %s"
          % ", ".join("%d (ordinal %d)" % (n, o) for n, o, _r in sizes[:5]))
    print("")
    if ready == 0:
        print("So the C++ cannot move without reading first: no export is writable from what is already known, and the")
        print("smallest remaining domain is %d functions. That is the honest answer to \"why is re/ changing\"." % sizes[0][0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
