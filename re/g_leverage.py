# -*- coding: utf-8 -*-
"""Find the unimplemented exports that can be implemented WITHOUT reading anything new.

Round 415 tried this as a one-liner and died on a bracket mismatch, so it lives in a file now. The question it answers:
among the 154 unimplemented entry points, which have external call or jump targets that are ALL already implemented and
verified in this project? Those can be implemented immediately. A second group has no external target at all, so they are
pure field work and can also be implemented immediately. If both groups are empty, every remaining export needs a
dependency read first, and the answer to that is to work down the dependency depth one function at a time.
"""
import io
import json
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))
from lib import disasm  # noqa: E402

# The routines this project has implemented and verified. An export whose external targets are all in here needs no new
# reading.
VERIFIED = {
    0x5C8A10: "boxAccumulate",
    0x50FD40: "boxAccumulateRange",
    0x5C8C50: "mergeBoxInto",
    0x5CE7B0: "translationTransform",
    0x5CED50: "invertTransform",
    0x5CE970: "composeTransform",
    0x5CF6B0: "transformPairCopy",
    0x5CFD80: "transformPointInPlace",
    0x5CFDC0: "transformPairInPlace",
    0x5CEA80: "transformPairInPlaceVariant",
    0x24B440: "orientationDeterminant",
    0x55E190: "lengthExceedsThreshold",
    0x51D2F0: "getSubObject",
    0x51D090: "getMultiplicityField",
    0x51D0C0: "partsVectorAt28",
}


def forwarded_ordinals():
    out = set()
    path = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")
    for line in io.open(path, encoding="utf-8"):
        m = re.match(r"\s*\{(\d+),", line)
        if m:
            out.add(int(m.group(1)))
    return out


def external_targets(rva, size):
    """Addresses called or jumped to from outside the function's own body."""
    targets = []
    for ins in disasm(rva):
        if size and ins.address >= rva + size:
            break
        if ins.mnemonic not in ("call", "jmp"):
            continue
        m = re.search(r"0x([0-9a-f]+)", ins.op_str)
        if not m:
            continue
        t = int(m.group(1), 16)
        if not (rva <= t < rva + size):
            targets.append(t)
    return sorted(set(targets))


def main():
    done = forwarded_ordinals()
    table = json.loads(io.open(os.path.join(ROOT, "re", "exports_table.json"), encoding="utf-8").read())
    ready = []
    fieldwork = []
    blocked = []
    for e in table:
        ord0 = (e.get("ords") or [0])[0]
        if ord0 in done:
            continue
        name = e.get("name") or ("sub_%05X" % e["rva"])
        targets = external_targets(e["rva"], e["size"])
        row = (name, ord0, e["rva"], e["size"], targets)
        if not targets:
            fieldwork.append(row)
        elif all(t in VERIFIED for t in targets):
            ready.append(row)
        else:
            unknown = [t for t in targets if t not in VERIFIED]
            blocked.append((row, unknown))

    print("unimplemented exports: %d" % (len(ready) + len(fieldwork) + len(blocked)))
    print("")
    print("(a) all external targets already verified -- implementable now: %d" % len(ready))
    for name, ord0, rva, size, targets in ready:
        print("    0x%-6X ord %-4d %-32s %5d bytes  <- %s"
              % (rva, ord0, name, size, ", ".join("%s(0x%X)" % (VERIFIED[t], t) for t in targets)))
    print("")
    print("(b) no external target at all -- pure field work: %d" % len(fieldwork))
    for name, ord0, rva, size, _ in fieldwork[:40]:
        print("    0x%-6X ord %-4d %-32s %5d bytes" % (rva, ord0, name, size))
    print("")
    print("(c) need a dependency read first: %d" % len(blocked))
    depth = {}
    for (_row, unknown) in blocked:
        for t in unknown:
            depth[t] = depth.get(t, 0) + 1
    for t, n in sorted(depth.items(), key=lambda kv: -kv[1])[:15]:
        size = None
        print("    0x%-8X blocking %3d exports" % (t, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
