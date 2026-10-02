# -*- coding: utf-8 -*-
"""Separate the CRT and toolchain wrappers out of the "domain blockers" list, iteratively.

Rounds 421 and 423 read two addresses that the frequency ranking put near the top and found neither to be domain code:

  * 0x9984B0 -- a five-byte `jmp 0x63F390`, 5721 callers: a deallocation wrapper; 0x63F390 turns out to be a whole bank
    of IAT stubs (`jmp qword ptr [rip + ...]` with nop padding), i.e. the import jump table;
  * 0x998500 -- 109 bytes, 2317 callers: `operator new`, with the null-to-one correction, the new_handler retry loop and
    the failure path.

Both rank high only because everything allocates and frees. A frequency ranking therefore cannot be read as a list of
high-leverage domain functions, and this script reclassifies them so that the remaining list means what it says.

A function is TOOLCHAIN when any of these holds, and the rule is applied repeatedly until nothing changes:

  1. its body is a single jmp;
  2. its body contains `jmp qword ptr [rip + ...]` or `call 0x63F3...` -- the import stub bank;
  3. every function it calls is already toolchain.

Nothing here is guessed: each rule reads the function is own instructions, and rule 3 only propagates a verdict that
rules 1 and 2 established.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L  # noqa: E402
from lib import disasm  # noqa: E402

STUB_BANK = 0x63F390  # the import jump table: every entry is jmp qword ptr [rip + ...]


def scan(addr):
    """Return (names, text, callees) for one function."""
    text = []
    callees = []
    for ins in disasm(addr):
        t = ins.mnemonic + " " + ins.op_str
        text.append(t)
        if ins.mnemonic in ("call", "jmp"):
            m = re.search(r"0x([0-9a-f]+)", ins.op_str)
            if m:
                callees.append(int(m.group(1), 16))
    return text, callees


def is_toolchain(addr, verdicts):
    if addr in verdicts:
        return verdicts[addr]
    text, callees = scan(addr)
    verdict = False
    if len(text) == 1 and text[0].startswith("jmp"):
        verdict = True
    for t in text:
        if t.startswith("jmp qword ptr [rip"):
            verdict = True
        if t.startswith("call 0x63f3"):
            verdict = True
    # rule 3, evaluated with whatever is already known; the outer loop repeats until stable
    if not verdict and callees:
        known = [c for c in callees if c in verdicts]
        if known and len(known) == len(callees) and all(verdicts[c] for c in callees):
            verdict = True
    verdicts[addr] = verdict
    return verdict


def main():
    done = L.forwarded_ordinals()
    table = json.loads(io.open(os.path.join(L.ROOT, "re", "exports_table.json"), encoding="utf-8").read())

    # Every address any unimplemented export reaches, plus everything those reach, so the verdicts are available.
    pending = set()
    rows = []
    for e in table:
        ord0 = (e.get("ords") or [0])[0]
        if ord0 in done:
            continue
        name = e.get("name") or ("sub_%05X" % e["rva"])
        tg = L.external_targets(e["rva"], e["size"])
        rows.append((name, ord0, e["rva"], e["size"], tg))
        for t in tg:
            pending.add(t)

    verdicts = {}
    for _round in range(6):
        before = len([a for a in verdicts if verdicts[a]])
        for a in list(pending):
            is_toolchain(a, verdicts)
            _t, callees = scan(a)
            for c in callees:
                if c not in verdicts:
                    pending.add(c)
        after = len([a for a in verdicts if verdicts[a]])
        if after == before and _round > 0:
            break

    tool = sorted(a for a in verdicts if verdicts[a])
    domain = sorted(a for a in verdicts if not verdicts[a])
    print("addresses examined: %d" % len(verdicts))
    print("  toolchain: %d" % len(tool))
    print("  domain   : %d" % len(domain))
    print("")
    print("the first twelve toolchain addresses, which the frequency ranking had been calling blockers:")
    for a in tool[:12]:
        text, _c = scan(a)
        print("    0x%-8X %d bytes, %d instructions, first: %s" % (a, len(text), len(text), text[0][:48]))
    print("")
    ready = []
    blocked = []
    for name, ord0, rva, size, tg in rows:
        bad = [t for t in tg if (t in verdicts and not verdicts[t]) and t not in L.VERIFIED]
        if not tg:
            ready.append((name, ord0, rva, size, "no external target"))
        elif not bad:
            ready.append((name, ord0, rva, size, "toolchain or verified only"))
        else:
            blocked.append((name, ord0, rva, size, bad))
    print("implementable once toolchain is set aside: %d" % len(ready))
    for name, ord0, rva, size, why in ready[:60]:
        print("    0x%-6X ord %-4d %-34s %5d bytes  (%s)" % (rva, ord0, name, size, why))
    print("")
    print("still blocked on real domain code: %d" % len(blocked))
    dom = {}
    for _n, _o, _r, _s, bad in blocked:
        for t in bad:
            dom[t] = dom.get(t, 0) + 1
    for t, c in sorted(dom.items(), key=lambda kv: -kv[1])[:12]:
        print("    0x%-8X blocks %3d exports" % (t, c))
    return 0


if __name__ == "__main__":
    sys.exit(main())
