# -*- coding: utf-8 -*-
"""The domain-only closure of an export: only a domain caller can reach a domain function.

Usage: python g_domain_closure.py 51 [--all] [--leaves N] [--bodies]

The plain closure answers "what does this entry point reach", and for LaunchLocalComputation the answer is dominated by
libstdc++: the label pass removed 932 functions at once, and reading the remaining leaves showed that almost every one is a
locale facet or the printf numeric layer. They are reached from the entry point because the orchestration sets up an
ostream, and they are reached from each other because `std::locale::_S_initialize` installs every facet there is.

So the plain closure is the wrong work list. The rule here is directional and deliberately conservative:

    a function is domain only if the entry point calls it directly, or a domain function calls it.

Nothing reached solely through library code can be domain: this module's own functions do not live inside libstdc++'s
locale table. That is a claim about the shape of the code rather than a proof, so it is computed forward from the entry
point with the library markings this project already has -- the VERIFIED, BOILERPLATE and IMPLEMENTED sets, the kind()
verdict for small functions, and the standard library symbols a function's own body names -- and every excluded function
is listed with the reason, so the claim can be checked rather than trusted.

`--all` lists the excluded ones, `--leaves N` prints the bodies of the smallest N leaves, and `--bodies` prints them all.
"""
import io
import json
import os
import re
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_toolchain as T         # noqa: E402
from lib import disasm, load_prof  # noqa: E402

SMALL_FOR_TOOLCHAIN = 64

LIBRARY_MARKERS = (
    "basic_string", "std::", "__cxa", "__gnu_cxx", "operator new", "operator delete", "allocator",
    "vector", "map<", "set<", "list<", "deque", "stringstream", "streambuf", "ios_base", "locale",
    "pthread", "mutex", "condition_variable", "chrono", "ratio", "codecvt", "num_put", "money_put",
    "numpunct", "moneypunct", "time_put", "terminate", "typeinfo", "dynamic_cast", "bad_alloc",
    "length_error", "out_of_range", "printf", "scanf", "malloc", "calloc", "realloc", "free(", "abort",
)


def main(argv):
    ordinal = int(argv[0])
    show_all = "--all" in argv
    want_bodies = 0
    if "--bodies" in argv:
        want_bodies = 10 ** 6
    if "--leaves" in argv:
        want_bodies = int(argv[argv.index("--leaves") + 1])
    profile = load_prof()
    reason = {}

    def excluded(addr):
        """(True, reason) when this project has established that the function is not domain code."""
        if addr in L.VERIFIED:
            return True, "verified in this project"
        if addr in T.BOILERPLATE:
            return True, "boilerplate, read whole in an earlier round"
        if addr in getattr(T, "IMPLEMENTED", ()):
            return True, "already implemented in lcns"
        if addr not in profile:
            return True, "not a known function"
        k = T.kind(addr, profile)
        size = (profile.get(addr) or {}).get("size") or 0
        if k is not None and k != "domain" and size <= SMALL_FOR_TOOLCHAIN:
            return True, "kind() says %s at %d bytes" % (k, size)
        for s in (profile[addr].get("strings") or []):
            text = s[1] if isinstance(s, (tuple, list)) and len(s) == 2 else (s if isinstance(s, str) else "")
            if text and any(m in text for m in LIBRARY_MARKERS):
                return True, "its own literal %r names a standard library symbol" % text[:48]
        return False, ""

    def callees(addr):
        out = []
        size = (profile.get(addr) or {}).get("size")
        for ins in disasm(addr):
            if size and ins.address >= addr + size:
                break
            if ins.mnemonic in ("call", "jmp"):
                m = re.search(r"0x([0-9a-f]+)", ins.op_str)
                if m:
                    out.append(int(m.group(1), 16))
        return out

    table = json.loads(io.open(os.path.join(L.ROOT, "re", "exports_table.json"), encoding="utf-8").read())
    rva = None
    for e in table:
        if (e.get("ords") or [0])[0] == ordinal:
            rva = e["rva"]
            break
    assert rva is not None

    succ = {}
    for a in profile:
        succ[a] = [t for t in callees(a) if t in profile]

    # forward walk, entry point first: a function enters the domain set only from a domain caller
    domain = {rva}
    why = {rva: "the entry point"}
    q = deque([rva])
    while q:
        a = q.popleft()
        for t in succ.get(a, ()):
            if t in domain:
                continue
            bad, r = excluded(t)
            if bad:
                why.setdefault(t, "reached from 0x%X but: %s" % (a, r))
                continue
            domain.add(t)
            why[t] = "called by the domain function 0x%X" % a
            q.append(t)

    size_of = lambda a: (profile.get(a) or {}).get("size") or 0
    dbytes = sum(size_of(a) for a in domain)
    reach = set()
    q = deque([rva])
    while q:
        a = q.popleft()
        for t in succ.get(a, ()):
            if t not in reach:
                reach.add(t)
                q.append(t)
    print("ordinal %d: %d functions reachable from it, %d of them domain (%d bytes)"
          % (ordinal, len(reach) + 1, len(domain), dbytes))
    print("")

    order = sorted(domain, key=lambda a: size_of(a))
    for a in order:
        deps = [t for t in succ.get(a, ()) if t in domain]
        print("    0x%-8X %6d B  domain deps %-3d %s"
              % (a, size_of(a), len(deps), "LEAF" if not deps else ""))
    leaves = sorted((a for a in domain if not [t for t in succ.get(a, ()) if t in domain]), key=size_of)
    print("")
    print("domain leaves: %d" % len(leaves))
    print("")

    only_library = sorted((a for a in reach if a not in domain), key=lambda a: -size_of(a))
    print("reached, but excluded because every route to it goes through library code: %d functions, %d bytes"
          % (len(only_library), sum(size_of(a) for a in only_library)))
    if show_all:
        for a in only_library:
            print("    0x%-8X %6d B  %s" % (a, size_of(a), why.get(a, "reached only through library code")))

    shown = 0
    for a in leaves:
        if shown >= want_bodies:
            break
        shown += 1
        size = size_of(a)
        print("")
        print("=== 0x%X (%d B)" % (a, size))
        for x in disasm(a):
            if x.address >= a + size:
                break
            print("    %08x %-18s %s" % (x.address, x.mnemonic, x.op_str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
