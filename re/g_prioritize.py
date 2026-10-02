# -*- coding: utf-8 -*-
"""The prioritizer: read the ledger and the binary, choose the next task, and say WHY.

Usage: python g_prioritize.py [--top 12] [--explain]

This is the component that makes an autonomous round possible, and the reason it exists is the failure mode this repository
keeps meeting: a session chooses its next task from the conversation, so a new idea displaces the worklist and the earlier
instructions become noise. Here the choice is COMPUTED from state that lives in files, and every task carries the reason it
outranks the others. A round takes its task from this list or it does not take one.

The four kinds of task, and how they are ranked. The weights are stated rather than hidden, and they encode what this project
has learned rather than a preference:

  PROMOTE   a SHAPE claim in the ledger whose verifier exists. High, because a promoted claim is at most one read away and it
            unblocks naming or a layout. Four of these are open: the sub-object at parent +0x40, the 0x50 byte element, the
            ToJson key pairing, and the strategy Run bodies.
  CONTRADICT  two claims that cannot both hold. Highest, because a contradiction means something already believed is wrong and
            everything downstream of it is suspect. Nothing checks for these yet, which is itself the finding.
  IMPLEMENT an export whose closure is empty. Carries the most evidence of value -- it moves forwardedCount -- but there are
            none left, so this list is usually empty and the fact that it is empty is the point.
  READ      the leaves and shallowest functions of the largest remaining closure, in the order the closure reports.

The reason string is the contract: it names the claim, the address or the closure, so a reader can check the choice instead of
trusting it.
"""
import argparse
import glob
import io
import json
import os
import re
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import ledger            # noqa: E402
import g_leverage as L   # noqa: E402
import g_toolchain as T  # noqa: E402
from lib import disasm, load_prof  # noqa: E402

# Which verifier promotes which SHAPE claim. A SHAPE with no verifier named here is not a task, it is a note: the prioritizer
# will not send a round at something that cannot be concluded.
VERIFIERS = {
    "parent+0x40.subobject": "re/g_ctor_fields.py on the constructor of the class that owns +0x40",
    "element50.layout": "re/g_element_50.py with per-register attribution",
    "ToJson.keys": "read the value flow at each key: key -> accessor -> JSON constructor argument",
    "Multi::Run bodies": "re/STRATEGIES.md gives each class's members; read one Run against them",
    "Multi::RowNester.vtable": "re/g_strategy_vtables.py joined it by slot 5",
}

WEIGHTS = {
    "CONTRADICT": 1000,
    "PROMOTE": 500,
    "IMPLEMENT": 400,
    "GATE": 300,
    "READ": 100,
}


def closure_size(ordinal, profile):
    table = json.loads(io.open(os.path.join(HERE, "exports_table.json"), encoding="utf-8").read())
    root = None
    for entry in table:
        if (entry.get("ords") or [0])[0] == ordinal:
            root = entry["rva"]
            break
    if root is None:
        return None
    seen = {root: 0}
    queue = deque([(root, 0)])
    while queue:
        addr, depth = queue.popleft()
        for callee in (profile.get(addr) or {}).get("callees") or []:
            if callee in profile and callee not in seen:
                seen[callee] = depth + 1
                queue.append((callee, depth + 1))
    return seen


def domain_of(ordinal):
    """The domain set of an export, forward from the entry point, without shelling out to the tool."""
    table = json.loads(io.open(os.path.join(HERE, "exports_table.json"), encoding="utf-8").read())
    root = None
    for entry in table:
        if (entry.get("ords") or [0])[0] == ordinal:
            root = entry["rva"]
            break
    if root is None:
        return []
    profile = load_prof()
    succ = {a: [c for c in (i.get("callees") or []) if c in profile] for a, i in profile.items()}

    def excluded(addr):
        if addr in L.VERIFIED or addr in T.BOILERPLATE or addr in getattr(T, "IMPLEMENTED", ()):
            return True
        return False

    domain = {root}
    queue = [root]
    while queue:
        addr = queue.pop()
        for c in succ.get(addr, ()):
            if c in domain or excluded(c):
                continue
            domain.add(c)
            queue.append(c)
    return sorted(domain, key=lambda a: (profile.get(a) or {}).get("size") or 0)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args(argv)

    data = ledger.load()
    tasks = []

    # 1. contradictions. Two claims that cannot both hold: an offset with two widths, a subject with two different predicates
    # at the same grade, a layout whose stated size is smaller than an offset inside it.
    by_subject = {}
    for claim in data["claims"]:
        by_subject.setdefault(claim["subject"], []).append(claim)
    for subject, claims in by_subject.items():
        predicates = {}
        for claim in claims:
            if claim["predicate"] in predicates and predicates[claim["predicate"]] != claim["grade"]:
                tasks.append(("CONTRADICT", "CONTRADICT", subject,
                              "the same predicate is filed at two grades: %s and %s"
                              % (predicates[claim["predicate"]], claim["grade"])))
            predicates[claim["predicate"]] = claim["grade"]
    for claim in data["claims"]:
        m = re.match(r"^0x([0-9A-F]+) bytes$", claim["predicate"])
        if not m:
            continue
        size = int(m.group(1), 16)
        for other in by_subject.get(claim["subject"].replace(".size", ""), []):
            mm = re.search(r"\+0x([0-9A-F]+)", other["predicate"])
            if mm and int(mm.group(1), 16) >= size:
                tasks.append(("CONTRADICT", "CONTRADICT", other["subject"],
                              "claims +0x%s inside a %s object" % (mm.group(1), claim["predicate"])))

    # 2. shape claims whose verifier exists: one read away from a promotion
    for claim in data["claims"]:
        if claim["grade"] != "SHAPE":
            continue
        verifier = VERIFIERS.get(claim["subject"])
        if not verifier:
            continue
        tasks.append(("PROMOTE", "PROMOTE", claim["subject"],
                      "%s  [%s]" % (claim["predicate"], verifier)))

    # 3. exports whose closure is empty: they move forwardedCount and need no reading
    profile = load_prof()
    forwarded = L.forwarded_ordinals()
    table = json.loads(io.open(os.path.join(HERE, "exports_table.json"), encoding="utf-8").read())
    for entry in table:
        ordinal = (entry.get("ords") or [0])[0]
        if ordinal in forwarded:
            continue
        seen = closure_size(ordinal, profile)
        if not seen:
            continue
        domain = [a for a in seen if not (a in T.BOILERPLATE or a in getattr(T, "IMPLEMENTED", ()) or a in L.VERIFIED)]
        if len(domain) <= 1:
            tasks.append(("IMPLEMENT", "IMPLEMENT", "ordinal %d (0x%X)" % (ordinal, entry["rva"]),
                          "its closure is %d functions, %d of them domain -- it needs no further reading"
                          % (len(seen), len(domain))))

    # 4. the largest unfinished closure, in the closure's own work order
    best = None
    for entry in table:
        ordinal = (entry.get("ords") or [0])[0]
        if ordinal in forwarded:
            continue
        seen = closure_size(ordinal, profile)
        if not seen:
            continue
        domain = [a for a in seen if not (a in T.BOILERPLATE or a in getattr(T, "IMPLEMENTED", ()) or a in L.VERIFIED)]
        if best is None or len(domain) > len(best[1]):
            best = (ordinal, domain)
    if best:
        ordinal, domain = best
        for addr in domain[:3]:
            size = (profile.get(addr) or {}).get("size")
            tasks.append(("READ", "READ", "0x%X (ordinal %d)" % (addr, ordinal),
                          "a domain function of the largest unfinished closure, %s bytes" % size))

    tasks.sort(key=lambda t: -WEIGHTS.get(t[0], 0))
    print("the next tasks, in the order the state ranks them:")
    print("")
    for index, (kind, label, subject, reason) in enumerate(tasks[:args.top], 1):
        print("%2d. %-10s %-34s %s" % (index, label, subject[:34], reason))
    print("")
    counts = {}
    for kind, _l, _s, _r in tasks:
        counts[kind] = counts.get(kind, 0) + 1
    print("by kind: %s" % ", ".join("%s=%d" % (k, v) for k, v in sorted(counts.items())))
    if not tasks:
        print("nothing ranked: the ledger has no promotable SHAPE, no export is ready, and no closure is open")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
