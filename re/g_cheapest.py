# -*- coding: utf-8 -*-
"""The cheapest export to finish next, measured in BYTES to read rather than in function count.

Usage: python g_cheapest.py [--top 12]

The human's question -- why the tooling keeps moving and the C++ does not -- has an answer, and building this tool produced it.
The domain of an export was being measured as a COUNT of functions, so "the smallest domain is 75" looked like a wall. It is not:
75 functions can be 75 tiny leaves, and what decides whether an export is finishable is the BYTES of body a reader must
understand, plus whether any of it is already known.

So this ranks the unforwarded exports by

    bytes to read      the total size of the domain functions not already verified, implemented or classified
    largest function   because one 4479 byte function is a project and fifty 40 byte ones are an afternoon
    leverage           how many OTHER exports share those domain functions, since a leaf shared by five exports is worth five

and prints the bodies it would take. An export whose whole domain is a few hundred bytes of small functions is next; the report
names it instead of leaving the choice to a conversation.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_toolchain as T         # noqa: E402
from lib import load_prof       # noqa: E402


def domain_of(root, profile):
    seen = {root}
    queue = [root]
    while queue:
        address = queue.pop()
        for callee in (profile.get(address) or {}).get("callees") or []:
            if callee in profile and callee not in seen:
                seen.add(callee)
                queue.append(callee)
    return seen


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=12)
    args = parser.parse_args(argv)
    profile = load_prof()
    table = json.loads(open(os.path.join(HERE, "exports_table.json"), encoding="utf-8").read())
    forwarded = L.forwarded_ordinals()

    # how many unforwarded exports each function is in, so a shared leaf shows its leverage
    counts = {}
    rows = []
    for entry in table:
        ordinal = (entry.get("ords") or [0])[0]
        if ordinal in forwarded:
            continue
        root = entry["rva"]
        closure = domain_of(root, profile)
        domain = [a for a in closure
                  if not (a in T.BOILERPLATE or a in getattr(T, "IMPLEMENTED", ()) or a in L.VERIFIED)]
        for address in domain:
            counts[address] = counts.get(address, 0) + 1
        rows.append((ordinal, root, domain))

    ranked = []
    for ordinal, root, domain in rows:
        total = sum((profile.get(a) or {}).get("size") or 0 for a in domain)
        largest = max(((profile.get(a) or {}).get("size") or 0 for a in domain), default=0)
        shared = sum(1 for a in domain if counts.get(a, 0) > 1)
        ranked.append((total, largest, len(domain), shared, ordinal, root, domain))
    ranked.sort()

    print("the unforwarded exports ranked by BYTES of body to read:")
    print("")
    print("%-9s %-9s %-7s %-7s %-8s %s" % ("bytes", "largest", "count", "shared", "ordinal", "export"))
    for total, largest, count, shared, ordinal, root, domain in ranked[:args.top]:
        label = L.VERIFIED.get(root) or ""
        print("%-9d %-9d %-7d %-7d %-8d 0x%X %s" % (total, largest, count, shared, ordinal, root, label))
    print("")

    total, largest, count, shared, ordinal, root, domain = ranked[0]
    print("the cheapest, in detail: ordinal %d, export 0x%X, %d bytes over %d functions" % (ordinal, root, total, count))
    for address in sorted(domain, key=lambda a: -((profile.get(a) or {}).get("size") or 0)):
        size = (profile.get(address) or {}).get("size") or 0
        label = L.VERIFIED.get(address) or ""
        print("    0x%-8X %5d B  in %d exports  %s" % (address, size, counts.get(address, 0), label))
    print("")
    print("A wall of 75 FUNCTIONS is not a wall of work: rank by bytes and the question becomes which few bodies to read.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
