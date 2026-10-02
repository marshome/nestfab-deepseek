# -*- coding: utf-8 -*-
"""The option and configuration keys: the lower_case_underscore literals, and who reads them.

Usage: python g_option_keys.py [--min 2]

This module names its settings like a config file -- 'bottom_gap', 'common_cut_allowed', 'clusters', 'assembly_group' --
and those literals are the field names of the objects the settings belong to. A function that reads a key and a field in the
same breath is a function that reads that field.

The tool prints, for every function that carries several such keys, the keys and the member offsets the same function
touches through its first argument, which is the pairing that names a field:

    0x5052C0   keys: bottom_gap, common_cut_allowed, ...   offsets: +0x10 +0x18 +0x20

It also lists the whole key vocabulary in one place, because a key that appears exactly once is still a name.
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N             # noqa: E402
from lib import disasm, load_prof  # noqa: E402

KEY = re.compile(r"^[a-z][a-z0-9_]{2,40}$")
ACCESS = re.compile(r"\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]")
MOVE = re.compile(r"^([a-z0-9]+), (.+)$")
ALIAS = {}
for _full, _names in {"rax": ("eax", "ax", "al"), "rbx": ("ebx", "bx", "bl"), "rcx": ("ecx", "cx", "cl"),
                      "rdx": ("edx", "dx", "dl"), "rsi": ("esi", "si", "sil"), "rdi": ("edi", "di", "dil")}.items():
    ALIAS[_full] = _full
    for _n in _names:
        ALIAS[_n] = _full
for _r in range(8, 16):
    for _s in ("", "d", "w", "b"):
        ALIAS["r%d%s" % (_r, _s)] = "r%d" % _r


def canonical(reg):
    return ALIAS.get(reg, reg)


def main(argv):
    minimum = int(argv[argv.index("--min") + 1]) if "--min" in argv else 3
    profile = load_prof()

    carriers = {}
    vocabulary = Counter()
    for addr, info in profile.items():
        keys = [t for _a, t in (info.get("strings") or []) if KEY.match(t)]
        if keys:
            carriers[addr] = keys
            for k in keys:
                vocabulary[k] += 1

    print("%d functions carry %d distinct lower_case_underscore literals" % (len(carriers), len(vocabulary)))
    print("")
    print("=== the functions that carry the most of them, with the offsets they touch in the same body")
    for addr in sorted(carriers, key=lambda a: -len(carriers[a]))[:20]:
        size = (profile.get(addr) or {}).get("size") or 0
        if len(carriers[addr]) < minimum:
            break
        body = [i for i in disasm(addr) if i.address < addr + size]
        bases = {"rcx"}
        for ins in body:
            m = MOVE.match(ins.op_str)
            if ins.mnemonic == "mov" and m and canonical(m.group(2)) in bases:
                bases.add(canonical(m.group(1)))
        offsets = set()
        for ins in body:
            for m in ACCESS.finditer(ins.op_str):
                if canonical(m.group(1)) in bases and m.group(2):
                    offsets.add(int(m.group(2), 16))
        name = N.direct(addr) or ""
        print("  0x%-8X %6d B %-28s %2d keys  offsets: %s"
              % (addr, size, name, len(carriers[addr]),
                 " ".join("+0x%X" % o for o in sorted(offsets)[:10]) or "-"))
        print("        %s" % ", ".join(carriers[addr][:12]))
    print("")
    print("=== the most used keys (a key is a field or option name wherever it appears)")
    for key, count in vocabulary.most_common(40):
        print("    %-42s %d" % (key, count))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
