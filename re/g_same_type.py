# -*- coding: utf-8 -*-
"""Do two member offsets belong to the same type? The overlap of their user sets answers it.

Usage: python g_same_type.py 0x240 0x2A8 [more offsets...]

If the functions that touch +0x240 are largely the functions that touch +0x2A8, the two offsets are members of one
structure, and the names of those functions say which. This is the question that turns a pile of offsets into a type: the
object 0x2AB0 receives has a mode at +0x240, and the object the destructor 0x5007C0 walks has a node list at +0x2A8 -- are
they the same object?

It prints the overlap both ways (what fraction of each offset's users the other offset's users cover), the functions in the
intersection with their recovered names, and the two sets' sizes, so a small accidental overlap cannot be mistaken for a
type.
"""
import io
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N             # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]")
STACK = ("rsp", "rbp")


def main(argv):
    offsets = [int(a, 0) for a in argv if a.startswith("0x")]
    if len(offsets) < 2:
        print("give at least two offsets")
        return 2
    profile = load_prof()
    users = defaultdict(set)
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        for ins in disasm(addr):
            if ins.address >= addr + size:
                break
            for m in ACCESS.finditer(ins.op_str):
                if m.group(1) in STACK:
                    continue
                offset = int(m.group(2), 16) if m.group(2) else 0
                if offset in offsets:
                    users[offset].add(addr)

    for offset in offsets:
        names = sorted(set(N.direct(a) for a in users[offset] if N.direct(a)))
        print("+0x%-6X %4d functions%s" % (offset, len(users[offset]),
                                           ("   " + ", ".join(names[:6])) if names else ""))
    print("")
    for i in range(len(offsets)):
        for j in range(i + 1, len(offsets)):
            a, b = offsets[i], offsets[j]
            inter = users[a] & users[b]
            if not users[a] or not users[b]:
                continue
            print("+0x%X and +0x%X: %d functions in common (%.0f%% of +0x%X, %.0f%% of +0x%X)"
                  % (a, b, len(inter), 100.0 * len(inter) / len(users[a]), a,
                     100.0 * len(inter) / len(users[b]), b))
            names = sorted(set(N.direct(x) for x in inter if N.direct(x)))
            if names:
                print("    named among them: %s" % ", ".join(names[:8]))
            print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
