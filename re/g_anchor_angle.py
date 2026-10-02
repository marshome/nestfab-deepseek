# -*- coding: utf-8 -*-
"""Disambiguate a slid embedding by looking for the PAIR of related fields, not the field.

Usage: python g_anchor_angle.py [--base 0x178] [--top 10]

The problem this solves, stated precisely. re/g_compose.py reports that `AngleTransform` fits the launch order at +0x178,
+0x180, +0x188, +0x190 and +0x198 equally well, because RE 0x14800 through 0x148A2 writes an 8-byte zero at every one of
+0x178 to +0x1F0 and six consecutive doubles therefore slide freely through that run. Arithmetic cannot pick, and the ledger
records all five as SHAPE rather than choosing.

The way out is that a slid window is not identical to the others, because the structure's FIELDS ARE RELATED TO EACH OTHER:

    double cos;        // +0x00
    double negSin;     // +0x08   -- the negative of a sine, so cos² + negSin² = 1 and the two are written together
    double sin;        // +0x10
    double cos2;       // +0x18   -- a second cos, so equal to cos
    double zero20;     // +0x20   -- a field whose name says it is zero
    double zero28;     // +0x28

so a candidate base is confirmed by finding a function that writes the PAIR: the same value to base+0x00 and its negation to
base+0x08, or minus that value. A sliding window has one such alignment and the others do not, because the relation only holds
where the two fields really are.

This searches every function for a store to base+0x00 and a store to base+0x08 within a short span, reports whether the second
is the negation of the first (an `xorpd` with a sign mask between them, or a separate `subsd` from zero), and grades the
candidate accordingly. A candidate with no such pair stays SHAPE, which is the honest outcome.
"""
import argparse
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N  # noqa: E402
from lib import disasm, load_prof  # noqa: E402

STORE = re.compile(r"^xmm[0-9]+, \[([a-z0-9]+) \+ (0x[0-9a-f]+)\]$")
NEGATE = ("xorpd", "subsd", "pxor")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=lambda v: int(v, 0), default=0x178)
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args(argv)
    profile = load_prof()

    bases = [args.base + 8 * step for step in range(0, 6)]
    print("candidate bases for the AngleTransform window: %s" % ", ".join("+0x%X" % b for b in bases))
    print("")
    found = defaultdict(list)
    for address, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(address) if i.address < address + size]
        for base in bases:
            near = {"xmm": [], "negated": False}
            writes = {}
            for index, ins in enumerate(body):
                operand = ins.op_str.replace(" ", "")
                m = re.match(r"^(xmm[0-9]+),\[([a-z0-9]+)\+(0x[0-9a-f]+)\]$", operand)
                if ins.mnemonic in ("movsd", "movupd", "movapd") and m:
                    writes.setdefault(int(m.group(3), 16), []).append((index, ins.address, m.group(1)))
                if ins.mnemonic in NEGATE and "xmm" in ins.op_str:
                    near["negated"] = True
            for offset in (0x0, 0x8):
                if base + offset in writes:
                    near["xmm"].extend(writes[base + offset])
            if 0x0 in writes and 0x8 in writes:
                # the two fields were written in the same function; the register relation decides
                first = writes[0x0][0]
                second = writes[0x8][0]
                # a negation between them in instruction order is the signature of negSin
                between = [i.mnemonic for i in body[first[0]:second[0] + 1]]
                negated_between = any(mnemonic in NEGATE for mnemonic in between)
                found[base].append((address, first, second, negated_between))

    for base in bases:
        rows = found.get(base, [])
        strong = [r for r in rows if r[3]]
        print("+0x%-5X  %2d functions write BOTH +0x0 and +0x8%s"
              % (base, len(rows), ("; %d have a negate between them" % len(strong)) if rows else ""))
        for address, first, second, negated in rows[:args.top]:
            label = N.direct(address) or ""
            print("        0x%-8X writes +0x0 at 0x%-8X (%s) and +0x8 at 0x%-8X (%s)%s  %s"
                  % (address, first[1], first[2], second[1], second[2],
                     "  NEGATION BETWEEN" if negated else "", label))
        print("")
    winner = max(bases, key=lambda b: len([r for r in found.get(b, []) if r[3]]))
    count = len([r for r in found.get(winner, []) if r[3]])
    if count:
        print("the base with a negated pair is +0x%X, in %d functions" % (winner, count))
    else:
        print("no candidate has a negation between the +0x0 and +0x8 stores, so the pair does not confirm any of them")
        print("and all five stay at SHAPE, which is what the ledger already records")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
