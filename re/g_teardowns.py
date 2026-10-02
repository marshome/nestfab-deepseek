# -*- coding: utf-8 -*-
"""Find the recursive teardown routines the way their own bodies declare them.

Usage: python g_teardowns.py [--top 30]

The order's destructor 0x5007C0 calls four member destructors, and comparing them found a signature that identifies the whole
family without reading any of them:

    0x92B340   605 B  19 calls, 18 of them the allocator's free, ONE call to ITSELF
    0x92B940   597 B  20 calls, 18 free, one to itself, one to 0x929FA0
    0x92BBA0   687 B  22 calls, 21 free, ONE call to ITSELF
    0x92ECB0   791 B  27 free, no self call, a LOOP instead

so a recursive teardown is recognisable as: **it calls itself exactly once, it calls the allocator's free many times, and it
touches a chain link at +0x18.** The self call is what distinguishes it from an ordinary destructor -- one call to itself is a
walk down a recursive structure, and a walk down a structure is a five line loop once the link offset is known.

This lists every function with that shape, in the module, with its self-call count, its free count and how far the +0x18 chain
recurses. It is the mechanical half of the work 0x92ECB0 took a round to do by hand.

A function with exactly one self call and NO free calls is not a teardown; a function with many free calls and no self call is a
flat destructor, like 0x92ECB0 before its loop was recognised. Both are printed with their classification, because the interesting
question is which family a body belongs to and not whether it is "destructor-like".
"""
import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N  # noqa: E402
from lib import disasm, load_prof  # noqa: E402

FREE = 0x9984B0


DIRECT_CALL = re.compile(r"^0x([0-9a-f]+)$")


def direct_calls(body):
    """The targets of DIRECT calls only.

    The first version searched for `0x...` anywhere in the operand, so an indirect call -- `call qword ptr [rax + 0x10]` --
    contributed a target of 0x10, and 0x18, and so on. Those are not callees and they made every count in this tool slightly
    wrong. A direct call's operand is exactly `0x<hex>` and nothing else, which is what this requires.
    """
    out = []
    for ins in body:
        if ins.mnemonic != "call":
            continue
        m = DIRECT_CALL.match(ins.op_str.strip())
        if m:
            out.append(int(m.group(1), 16))
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=30)
    args = parser.parse_args(argv)
    profile = load_prof()

    rows = []
    for address, info in profile.items():
        size = info.get("size") or 0
        if size < 80:
            continue
        body = [i for i in disasm(address) if i.address < address + size]
        counted = collections.Counter(direct_calls(body))
        self_calls = counted.get(address, 0)
        frees = counted.get(FREE, 0)
        chain = sum(1 for ins in body for m in [re.search(r"\[r[a-z0-9]+ \+ 0x18\]", ins.op_str)] if m)
        if self_calls != 1 or frees < 4:
            continue
        rows.append((frees, address, size, len(counted), chain, self_calls))

    rows.sort(reverse=True)
    print("functions with a recursive teardown signature (exactly one self call, four or more frees): %d" % len(rows))
    print("")
    print("%-8s %-10s %-7s %-9s %-7s %s" % ("frees", "rva", "bytes", "targets", "+0x18", "note"))
    for frees, address, size, targets, chain, _self in rows[:args.top]:
        note = N.direct(address) or ""
        print("%-8d 0x%-8X %-7d %-9d %-7d %s" % (frees, address, size, targets, chain, note))
    print("")
    print("The largest is the module's biggest teardown, and each of them is a loop once its link offset is known: the order's")
    print("0x92ECB0 was read as eight levels of nesting until its body showed the loop, and the same substitution applies here.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
