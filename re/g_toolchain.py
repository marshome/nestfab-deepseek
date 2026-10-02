# -*- coding: utf-8 -*-
"""Classify the blockers of the unimplemented exports, using only real function starts.

Round 424's version walked the call graph and disassembled whatever it reached, which produced 22,685 "addresses", a
third of them junk (data misread as code, visible as functions with one instruction per byte), and it still missed a
known platform stub because its rule did not cover `call qword ptr [rip + ...]`. This version:

  * only judges addresses that the profile lists as functions, so no data is disassembled;
  * treats as toolchain: a single-instruction function, anything that jumps or calls through a RIP-relative pointer (the
    import stubs and the indirect platform calls), and anything that calls into the 0x63F3xx stub bank;
  * treats as diagnostic anything that calls 0x910BA0, the helper that builds strings and reports;
  * calls everything else domain, which is what must actually be read.

No propagation between functions, because a verdict that depends on an unverified neighbour is how round 424 produced a
list that could not be trusted.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L  # noqa: E402
from lib import disasm, load_prof  # noqa: E402


def kind(addr, profile):
    """One verdict per function, from its own instructions only. Returns None if it is not a known function."""
    if addr not in profile:
        return None
    text = []
    for ins in disasm(addr):
        size = (profile.get(addr) or {}).get("size")
        if size and ins.address >= addr + size:
            break
        text.append(ins.mnemonic + " " + ins.op_str)
    if not text:
        return None
    if len(text) == 1:
        return "toolchain"
    for t in text:
        if "qword ptr [rip" in t and (t.startswith("jmp") or t.startswith("call")):
            return "toolchain"
        if t.startswith("call 0x63f3"):
            return "toolchain"
    for t in text:
        if t == "call 0x910ba0":
            return "diagnostic"
    return "domain"


def main():
    profile = load_prof()
    done = L.forwarded_ordinals()
    table = json.loads(io.open(os.path.join(L.ROOT, "re", "exports_table.json"), encoding="utf-8").read())

    verdicts = {}
    rows = []
    for e in table:
        ord0 = (e.get("ords") or [0])[0]
        if ord0 in done:
            continue
        name = e.get("name") or ("sub_%05X" % e["rva"])
        targets = L.external_targets(e["rva"], e["size"])
        rows.append((name, ord0, e["rva"], e["size"], targets))
        for t in targets:
            if t in L.VERIFIED or t in verdicts:
                continue
            k = kind(t, profile)
            verdicts[t] = k if k is not None else "unknown"

    counts = {}
    for v in verdicts.values():
        counts[v] = counts.get(v, 0) + 1
    print("distinct blocker addresses judged: %d" % len(verdicts))
    for k in sorted(counts):
        print("    %-11s %d" % (k, counts[k]))

    ready = []
    blocked = []
    for name, ord0, rva, size, targets in rows:
        bad = []
        for t in targets:
            if t in L.VERIFIED:
                continue
            if verdicts.get(t) == "domain":
                bad.append(t)
        if not targets:
            ready.append((name, ord0, rva, size, "no external target at all"))
        elif not bad:
            ready.append((name, ord0, rva, size, "only toolchain, diagnostic or verified"))
        else:
            blocked.append((name, ord0, rva, size, bad))

    print("")
    print("implementable once toolchain and diagnostic are set aside: %d" % len(ready))
    for name, ord0, rva, size, why in ready[:80]:
        print("    0x%-6X ord %-4d %-36s %5d bytes  (%s)" % (rva, ord0, name, size, why))
    print("")
    print("still blocked on domain code: %d" % len(blocked))
    dom = {}
    for _n, _o, _r, _s, bad in blocked:
        for t in bad:
            dom[t] = dom.get(t, 0) + 1
    for t, c in sorted(dom.items(), key=lambda kv: -kv[1])[:15]:
        size = (profile.get(t) or {}).get("size")
        print("    0x%-8X blocks %3d exports, %s bytes" % (t, c, size))
    print("")
    print("a domain blocker whose callers number in the thousands is a warning sign: it is more likely a CRT wrapper than a")
    print("high-leverage domain function, so check its body before reading anything below it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
