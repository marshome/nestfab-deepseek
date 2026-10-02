# -*- coding: utf-8 -*-
"""Cluster member offsets by the functions that touch them: one cluster, one structure.

Usage: python g_types.py [--min-fns 8] [--iover 0.7] [--top 20] [--all]

Using the first argument as the object (rcx, or a register copied from it), every offset gets a set of functions. Two
offsets belong to the same structure when the SAME functions touch both -- not merely many functions, but many of the same
functions. This builds those pairs and joins them transitively into clusters.

The output is the shape of each cluster: the offsets in it, the widths, how many functions use it, and the recovered names
of those functions, which is what turns "+0x1C8 +0x1D0 +0x1D8 +0x1E0 used by 380 functions" into a named type.

Two offsets that co-occur in only a handful of functions are not evidence, so a pair needs `--min-fns` shared users and
`--iover` overlap (intersection over the smaller user set) before it joins a cluster.
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_toolchain as T         # noqa: E402
import g_names as N             # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]")
MOV_FROM_RCX = re.compile(r"^([a-z0-9]+), rcx$")
WIDTHS = (("xmmword", 16), ("oword", 16), ("qword", 8), ("dword", 4), ("word", 2), ("byte", 1))
STACK = ("rsp", "rbp")
MAX_OFFSET = 0x800


def width_of(text):
    for name, width in WIDTHS:
        if name in text:
            return width
    return 0


def first_arg_profile(body):
    bases = {"rcx"}
    for ins in body:
        m = MOV_FROM_RCX.match(ins.op_str)
        if ins.mnemonic == "mov" and m:
            bases.add(m.group(1))
    out = defaultdict(Counter)
    for ins in body:
        for m in ACCESS.finditer(ins.op_str):
            reg = m.group(1)
            if reg not in bases or reg in STACK:
                continue
            offset = int(m.group(2), 16) if m.group(2) else 0
            if offset > MAX_OFFSET:
                continue
            out[offset][width_of(ins.op_str)] += 1
    return out


class Union:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def join(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def main(argv):
    min_fns = int(argv[argv.index("--min-fns") + 1]) if "--min-fns" in argv else 8
    iover = float(argv[argv.index("--iover") + 1]) if "--iover" in argv else 0.7
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 20
    include_all = "--all" in argv
    profile = load_prof()

    functions = {}
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        if not include_all and (addr in T.BOILERPLATE or addr in getattr(T, "IMPLEMENTED", ()) or addr in L.VERIFIED):
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        prof = first_arg_profile(body)
        if prof:
            functions[addr] = prof

    users = defaultdict(set)
    widths = defaultdict(Counter)
    for addr, prof in functions.items():
        for offset, counter in prof.items():
            users[offset].add(addr)
            for width, count in counter.items():
                widths[offset][width] += count

    offsets = [o for o, fns in users.items() if len(fns) >= min_fns]
    offsets.sort(key=lambda o: -len(users[o]))
    union = Union()
    pairs = 0
    for i in range(len(offsets)):
        a = offsets[i]
        for j in range(i + 1, len(offsets)):
            b = offsets[j]
            inter = len(users[a] & users[b])
            if inter < min_fns:
                continue
            if inter >= iover * min(len(users[a]), len(users[b])):
                union.join(a, b)
                pairs += 1

    clusters = defaultdict(list)
    for offset in offsets:
        clusters[union.find(offset)].append(offset)

    rows = []
    for root, members in clusters.items():
        members = sorted(members)
        shared = set.intersection(*(users[o] for o in members)) if members else set()
        rows.append((len(shared), members))
    rows.sort(key=lambda r: (-len(r[1]), -r[0]))

    print("functions profiled: %d; offsets with %d+ users: %d; co-occurring pairs: %d; clusters: %d"
          % (len(functions), min_fns, len(offsets), pairs, len(rows)))
    print("")
    shown = 0
    for shared, members in rows:
        if shown >= top:
            break
        if len(members) < 2:
            continue
        shown += 1
        names = []
        for a in sorted(shared)[:200]:
            n = N.direct(a)
            if n:
                names.append(n)
        names = sorted(set(names))
        membersizes = sorted((profile.get(a) or {}).get("size") or 0 for a in shared)
        print("=== %d offsets, used together by %d functions%s"
              % (len(members), len(shared), ("  sizes %d..%d" % (membersizes[0], membersizes[-1])) if membersizes else ""))
        print("    offsets: %s" % " ".join("+0x%X" % o for o in members[:24]))
        print("    widths : %s" % " ".join("%s" % (max(widths[o].items(), key=lambda kv: kv[1])[0] if widths[o] else "?")
                                           for o in members[:24]))
        if names:
            print("    named users: %s" % ", ".join(names[:8]))
        if shared:
            print("    e.g. %s" % ", ".join("0x%X" % a for a in sorted(shared)[:6]))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
