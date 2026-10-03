# -*- coding: utf-8 -*-
"""A constructor's members, from its stores to a register that is the object -- with the RIP-relative false positives removed.

Usage: python g_ctor_members.py 0x8A9510

re/g_ctor_fields.py reported 287 stores for 0x8A9510 with offsets up to +0xFEB13, which cannot be true of an object whose fields
are at +0x00 to +0x48: the large "offsets" are instruction addresses leaking in, because a store through a global (`mov [rip +
disp], rax`) parses as `[base + disp]` with the base being read as a register. Two filters fix it and both are mechanical:

  * the object is the register the constructor STORES ITS FIRST ARGUMENT INTO. `mov qword ptr [rcx+0x18], rcx` and
    `mov dword ptr [rcx], edx` say the object is rcx; a store through any other base belongs to a global or a local.
  * an offset larger than the object's extent -- taken as the largest offset that many stores agree on -- is not a member.

The output is what a declaration needs: the offset, the width, the value stored, and whether the store was an immediate (a real
field initialiser) or a register (a computed pointer, so the member is a container whose own storage it points at).
"""
import argparse
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

STORE = re.compile(r"^(byte|word|dword|qword|xmmword) ptr \[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\], (.+)$")
WIDTHS = {"byte": 1, "word": 2, "dword": 4, "qword": 8, "xmmword": 16}


def main(argv):
    target = int(argv[0], 0)
    profile = load_prof()
    size = (profile.get(target) or {}).get("size") or 0
    body = [i for i in disasm(target) if i.address < target + size]

    # the object is whichever register holds the first argument, and rcx is where it arrives
    carries = {"rcx"}
    for _round in range(4):
        for ins in body:
            m = re.match(r"^([a-z0-9]+), (rcx|rbx|rbp|rsi|rdi|r1[0-5])$", ins.op_str)
            if ins.mnemonic == "mov" and m and m.group(2) in carries:
                carries.add(m.group(1))

    by_base = Counter()
    stores = defaultdict(list)
    for ins in body:
        m = STORE.match(ins.op_str)
        if ins.mnemonic != "mov" or not m:
            continue
        base = m.group(2)
        by_base[base] += 1
        if base in carries:
            offset = int(m.group(3), 16) if m.group(3) else 0
            stores[offset].append((ins.address, WIDTHS[m.group(1)], m.group(4), ins.address))

    print("0x%X  %d bytes  %d stores" % (target, size, sum(by_base.values())))
    print("stores by base register: %s" % ", ".join("%s=%d" % (b, n) for b, n in by_base.most_common(6)))
    print("the object registers: %s" % ", ".join(sorted(carries)))
    print("")
    if not stores:
        print("no store through an object register, so this is not a constructor of a single object")
        return 0
    extent = max(stores)
    print("%d distinct offsets on the object, up to +0x%X" % (len(stores), extent))
    print("")
    print("%-8s %-6s %-5s %s" % ("offset", "width", "count", "the value stored"))
    for offset in sorted(stores):
        entries = stores[offset]
        width = min(e[1] for e in entries)
        values = Counter(e[2] for e in entries)
        sample = ", ".join("%s x%d" % (v, n) for v, n in values.most_common(3))
        print("+0x%-5X %-6d %-5d %s" % (offset, width, len(entries), sample[:60]))
    print("")
    immediates = [o for o in stores if all(not re.match(r"^(e|r)[a-z0-9]+$", e[2]) for e in stores[o])]
    computed = [o for o in stores if o not in immediates]
    print("fields written only with an immediate:  %d  %s" % (len(immediates), " ".join("+0x%X" % o for o in sorted(immediates)[:12])))
    print("fields written from a register:         %d  %s" % (len(computed), " ".join("+0x%X" % o for o in sorted(computed)[:12])))
    print("")
    print("A field written from a register holds a POINTER, so the member is a container whose own constructor allocated its")
    print("storage; the declaration says the container type and the compiler emits all of this.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
