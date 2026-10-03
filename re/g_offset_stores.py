#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Find the STORES that establish an offset, so a field's width and type come from an instruction rather than from a declaration.

**WHY THIS EXISTS.** `Order` carries `maxThreads` at +0x1F8, `maxIterations` at +0x1FC and `localEngine` at +0x200, and **no ledger claim backs any of them** --
they are declarations without an instruction. `LaunchingOrderLayout` covers the same range with ONE 32 byte `unsigned char unnamed1F8`, which is the honest
shape when the stores only ever write a block.

**AND THE DISCRIMINATOR IS THE STORE'S WIDTH.** A field written with `mov dword [reg + 0x1F8], ...` is four bytes wide and a name is then a READING; a range
only ever written as a whole block cannot be named from the stores at all.

    python -u g_offset_stores.py --offset 0x1F8
    python -u g_offset_stores.py --from 0x1F0 --to 0x210
"""
import argparse
import collections
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

STORE = re.compile(r"^(byte|word|dword|qword) ptr \[(\w+)(?: \+ (0x[0-9a-f]+))?\], (.+)$")
WIDTH = {"byte": 1, "word": 2, "dword": 4, "qword": 8}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--offset", dest="offset")
    parser.add_argument("--from", dest="low")
    parser.add_argument("--to", dest="high")
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args(argv)

    if args.offset:
        wanted = {int(args.offset, 16)}
    elif args.low and args.high:
        low, high = int(args.low, 16), int(args.high, 16)
        wanted = set(range(low, high, 4))
    else:
        parser.error("give --offset or --from with --to")

    profile = load_prof()
    by_offset = collections.defaultdict(list)
    for address, info in profile.items():
        size = info.get("size") or 0
        if not size:
            continue
        for instruction in disasm(address):
            if instruction.address >= address + size:
                break
            found = STORE.match(instruction.op_str)
            if not found:
                continue
            # **AN EXPLICIT OFFSET IS REQUIRED.** `mov dword [rbx], 1` has NO offset, and defaulting it to zero made it match `--from 0x1F8` through the
            # `range` step of 4 -- so the first run reported 285 "stores at +0x1F8" that were stores at +0x00, which is the same class of error as counting
            # the padding: **a pattern matching a shape that is not the shape sought.**
            if not found.group(3):
                continue
            offset = int(found.group(3), 16)
            if offset not in wanted:
                continue
            by_offset[offset].append((address, instruction.address, WIDTH[found.group(1)],
                                      found.group(1), found.group(2), found.group(4)[:24]))

    for offset in sorted(wanted):
        rows = by_offset.get(offset)
        print("+0x%03X" % offset)
        if not rows:
            print("   NO STORE ANYWHERE writes this offset")
            continue
        widths = collections.Counter(row[2] for row in rows)
        print("   %d store(s), width(s): %s" % (len(rows), ", ".join("%d B x%d" % (w, n) for w, n in widths.most_common())))
        for function, site, width, kind, base, value in rows[:args.limit]:
            print("      0x%-8X at 0x%-8X  %-5s [%s] <- %s" % (function, site, kind, base, value))
        if len(rows) > args.limit:
            print("      ... and %d more" % (len(rows) - args.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
