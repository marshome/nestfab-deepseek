# -*- coding: utf-8 -*-
"""What the first argument points at: the shapes of this module's own structures.

Usage: python g_shapes.py [--min-fns 6] [--top 20] [--all]

re/g_structs2.py clustered on exact (register, offset) signatures and fragmented: the same object is reached through rbx in
one function and r13 in the next, and the register is an artefact of the compiler, not a fact about the type. This tool
drops the register name and keeps only the offsets that are reached through a register which was ASSIGNED FROM THE FIRST
ARGUMENT -- mov rbx, rcx, mov rdi, rcx -- or through rcx itself. That set is the object the function was handed, and the
offsets in it are its members.

Then it counts, over every such function, how often each offset appears, and for the offsets that a group of functions
share it prints the group's shape: the offsets they all touch, with the widths, and the functions' recovered names. Those
shapes are this module's data structures, and the ones at the top are the ones the most functions agree on.

Widths come from the operand text, longest name first, so 'dword' is not mistaken for 'word'.
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_toolchain as T         # noqa: E402
import g_names as N             # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]")
MOV_FROM_RCX = re.compile(r"^([a-z0-9]+), rcx$")
WIDTHS = (("xmmword", 16), ("oword", 16), ("qword", 8), ("dword", 4), ("word", 2), ("byte", 1))
STACK = ("rsp", "rbp")
MAX_OFFSET = 0x800


def width_of(text):
    for name, width in WIDTHS:
        if name in text:
            return width
    return 0


def first_arg_profile(body):
    """offset -> Counter of widths, for accesses through rcx or a register copied from rcx."""
    bases = {"rcx"}
    for ins in body:
        m = MOV_FROM_RCX.match(ins.op_str)
        if ins.mnemonic == "mov" and m:
            bases.add(m.group(1))
    out = defaultdict(Counter)
    for ins in body:
        for m in ACCESS.finditer(ins.op_str):
            reg = m.group(1)
            if reg not in bases or reg in STACK:
                continue
            offset = int(m.group(2), 16) if m.group(2) else 0
            if offset > MAX_OFFSET:
                continue
            out[offset][width_of(ins.op_str)] += 1
    return out


def main(argv):
    min_fns = int(argv[argv.index("--min-fns") + 1]) if "--min-fns" in argv else 6
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 20
    include_all = "--all" in argv
    profile = load_prof()

    functions = {}
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        if not include_all and (addr in T.BOILERPLATE or addr in getattr(T, "IMPLEMENTED", ()) or addr in L.VERIFIED):
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        prof = first_arg_profile(body)
        if prof:
            functions[addr] = prof

    users = defaultdict(set)
    for addr, prof in functions.items():
        for offset in prof:
            users[offset].add(addr)

    ranked = sorted(users.items(), key=lambda kv: -len(kv[1]))
    print("functions with a first-argument member profile: %d" % len(functions))
    print("distinct member offsets among them: %d" % len(users))
    print("")
    print("=== the offsets the most functions agree on (these are the shared structures' headers)")
    shown = 0
    for offset, fns in ranked:
        if len(fns) < min_fns or shown >= 30:
            break
        shown += 1
        names = sorted(set(N.direct(a) for a in fns if N.direct(a)))
        print("    +0x%-6X %5d functions   %s" % (offset, len(fns), ", ".join(names[:5]) or "-"))
    print("")

    print("=== the shapes: for each of the busiest offsets, the offsets its users also touch")
    for offset, fns in ranked[:top]:
        if len(fns) < min_fns:
            break
        tally = Counter()
        widths = defaultdict(Counter)
        for addr in fns:
            for off, counter in functions[addr].items():
                tally[off] += 1
                for width, count in counter.items():
                    widths[off][width] += count
        names = sorted(set(N.direct(a) for a in fns if N.direct(a)))
        print("--- anchor +0x%X: %d functions%s" % (offset, len(fns), ("  (" + ", ".join(names[:4]) + ")") if names else ""))
        line = []
        for off, count in sorted(tally.items()):
            if count * 100 < 85 * len(fns):
                continue
            width = max(widths[off].items(), key=lambda kv: kv[1])[0] if widths[off] else 0
            line.append("+0x%X:%s" % (off, width or "?"))
        print("    %d of them share: %s" % (len(fns), " ".join(line)))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
