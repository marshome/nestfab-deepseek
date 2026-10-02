# -*- coding: utf-8 -*-
"""The structures this module reuses, found by which offsets travel together through which register.

Usage: python g_structs2.py [--min-fns 8] [--min-offsets 4] [--top 25]

The first version of this ranked bare offsets and drowned: every function has a stack frame at +0x0, +0x8, +0x10 and so on,
so "[base+0x10]" was touched by nine thousand functions and told us nothing. The fix is to keep the register:

    [rcx + 0x50]    a member of the object the function was handed
    [rsp + 0x50]    a local
    [rbx + 0x50]    a member, but of a second object

A structure is then a SET of (register, offset) pairs that recurs. This walks every function, records the pairs it touches,
and clusters the functions whose pair sets overlap heavily -- two functions reading the same twenty offsets of their first
argument are looking at the same type, whatever they are called. For each cluster it prints the type's shape: the offsets,
their widths, and the named functions that use it.

Widths come from the operand, so a cluster says "+0x28 is a qword and +0x2C is a dword", which is what a declaration needs.
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
WIDTHS = (("byte", 1), ("word", 2), ("dword", 4), ("qword", 8), ("xmmword", 16), ("oword", 16))
STACK = ("rsp", "rbp")
MAX_OFFSET = 0x800


def width_of(text):
    for name, width in WIDTHS:
        if name in text:
            return width
    return 0


def profile_of(body):
    """(register, offset) -> Counter of widths, for the non-stack bases of one function."""
    out = defaultdict(Counter)
    for ins in body:
        for m in ACCESS.finditer(ins.op_str):
            reg = m.group(1)
            if reg in STACK or reg.startswith("r1") and reg not in ("r12", "r13", "r14", "r15"):
                continue
            offset = int(m.group(2), 16) if m.group(2) else 0
            if offset > MAX_OFFSET:
                continue
            out[(reg, offset)][width_of(ins.op_str)] += 1
    return out


def main(argv):
    min_fns = int(argv[argv.index("--min-fns") + 1]) if "--min-fns" in argv else 8
    min_offsets = int(argv[argv.index("--min-offsets") + 1]) if "--min-offsets" in argv else 4
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 25
    profile = load_prof()

    functions = {}
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        if addr in T.BOILERPLATE or addr in getattr(T, "IMPLEMENTED", ()) or addr in L.VERIFIED:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        prof = profile_of(body)
        if len(prof) >= min_offsets:
            functions[addr] = prof

    # signature: the set of (register, offset). Cluster by an exact signature first, which is cheap and finds the families
    # the compiler generated from one template.
    by_signature = defaultdict(list)
    for addr, prof in functions.items():
        key = frozenset(prof)
        by_signature[key].append(addr)

    families = sorted(by_signature.items(), key=lambda kv: -len(kv[1]))
    print("functions with a register-based member profile: %d" % len(functions))
    print("distinct exact signatures: %d; the largest family has %d functions"
          % (len(by_signature), len(families[0][1]) if families else 0))
    print("")

    shown = 0
    for key, members in families:
        if len(members) < min_fns:
            break
        shown += 1
        if shown > top:
            break
        widths = Counter()
        for addr in members:
            for pair, counter in functions[addr].items():
                for width, count in counter.items():
                    widths[(pair[0], pair[1], width)] += count
        names = sorted(set(N.direct(a) for a in members if N.direct(a)))
        sizes = sorted(((profile.get(a) or {}).get("size") or 0) for a in members)
        print("=== family of %d functions, %d member offsets (sizes %d..%d)"
              % (len(members), len(key), sizes[0], sizes[-1]))
        if names:
            print("    named members: %s" % ", ".join(names[:6]))
        print("    an example: 0x%X" % members[0])
        pairs = sorted(((off, reg) for reg, off in key))
        line = []
        for off, reg in pairs[:26]:
            w = widths.most_common()
            width = 0
            for (r, o, wd), _c in widths.items():
                if o == off:
                    width = max(width, wd)
            line.append("%s+0x%X:%s" % (reg, off, width or "?"))
        print("    shape: %s" % " ".join(line))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
