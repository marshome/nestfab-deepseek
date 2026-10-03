# -*- coding: utf-8 -*-
"""Dump the store list of a constructor: which offset gets which width, in the order the code writes them.

Usage: python g_ctor_fields.py 0x14620 [registers]

A constructor that allocates its own object and writes every field is the authority on that object's layout, so this prints
exactly what it writes and nothing else: the offset, the width of the store, and the value or register it came from. The
output is what a C++ declaration is written from.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

STORE = re.compile(r"^(byte|word|dword|qword|xmmword) ptr \[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\], (.+)$")


def main(argv):
    if not argv:
        print("give a constructor rva")
        return 2
    addr = int(argv[0], 0)
    registers = set(argv[1].split(",")) if len(argv) > 1 else None
    profile = load_prof()
    size = (profile.get(addr) or {}).get("size") or 0
    body = [i for i in disasm(addr) if i.address < addr + size]
    rows = []
    alloc = None
    for ins in body:
        if ins.mnemonic == "mov" and re.match(r"^ecx, (0x[0-9a-f]+)$", ins.op_str):
            alloc = int(ins.op_str.split(", ")[1], 16)
        m = STORE.match(ins.op_str)
        if not m:
            continue
        if registers and m.group(2) not in registers:
            continue
        offset = int(m.group(3), 16) if m.group(3) else 0
        rows.append((ins.address, offset, m.group(1), m.group(4)))
    print("0x%X (%d bytes): %d stores%s" % (addr, size, len(rows),
                                            (", allocation size 0x%X" % alloc) if alloc else ""))
    for iaddr, offset, width, source in sorted(rows, key=lambda r: r[1]):
        print("    %08x  +0x%-5X %-8s <- %s" % (iaddr, offset, width, source))
    if rows:
        print("")
        print("largest offset written: +0x%X" % max(r[1] for r in rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
