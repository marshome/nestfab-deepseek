# -*- coding: utf-8 -*-
"""Pair a Get and a Set of the same offset: that pair IS the field's name, and it comes from the module.

Usage: python g_named_fields.py 0x1C0 0x2C0 [--min 3]

re/g_field_names.py prints who reads and who writes an offset. This one looks for the shape that names a field outright:

    an offset with a `GetX` among its readers and a `SetX` among its writers, sharing a noun

`GetSheetPriority` / `SetSheetPriority`, `GetNumberOfMarks` / `SetMarkMode`. When both halves exist the module has told us
the field's name twice, and the pairing is printed as a candidate name for the offset. Offsets with only one half are printed
too, since a lone setter is still a name.

Only the functions this project recovered a name for are considered, and the names come from the same assertion and log
channels as the rest of the naming work, so nothing here is invented.
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


def handles(body):
    carries = {"rcx"}
    for ins in body:
        m = MOVE.match(ins.op_str)
        if ins.mnemonic == "mov" and m and canonical(m.group(2)) in carries:
            carries.add(canonical(m.group(1)))
    behind = set()
    for _round in range(3):
        for ins in body:
            m = MOVE.match(ins.op_str)
            if ins.mnemonic != "mov" or not m:
                continue
            src = re.sub(r"^(byte|word|dword|qword|xmmword|oword) ptr ", "", m.group(2).strip())
            mm = re.match(r"^\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]$", src)
            if mm and canonical(mm.group(1)) in (carries | behind) and not mm.group(2):
                behind.add(canonical(m.group(1)))
            elif canonical(m.group(2)) in behind:
                behind.add(canonical(m.group(1)))
    return carries | behind


def noun(name):
    """The part of a Get/Set/CNS_Get name that is the field."""
    for prefix in ("CNS_",):
        if name.startswith(prefix):
            name = name[len(prefix):]
    for prefix in ("Get", "Set", "Is", "Add", "Enable", "Disable"):
        if name.startswith(prefix) and len(name) > len(prefix):
            return name[len(prefix):]
    return None


def main(argv):
    lo = int(argv[0], 0) if argv else 0x1C0
    hi = int(argv[1], 0) if len(argv) > 1 else 0x2C0
    minimum = int(argv[argv.index("--min") + 1]) if "--min" in argv else 3
    profile = load_prof()

    reads = defaultdict(set)
    writes = defaultdict(set)
    single = {}                      # function -> the one offset it touches in the range
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        bases = handles(body)
        touched = set()
        local_reads = defaultdict(set)
        local_writes = defaultdict(set)
        for ins in body:
            for m in ACCESS.finditer(ins.op_str):
                if canonical(m.group(1)) not in bases:
                    continue
                offset = int(m.group(2), 16) if m.group(2) else 0
                if not (lo <= offset <= hi):
                    continue
                touched.add(offset)
                head = ins.op_str.split(",")[0].strip()
                store = head.startswith(("byte ptr [", "word ptr [", "dword ptr [", "qword ptr [", "xmmword ptr [", "["))
                (local_writes if store else local_reads)[offset].add(addr)
        # An ACCESSOR is a small function that touches exactly one offset in the range. A big function that writes twenty
        # offsets is a setter of twenty fields at once, and attributing all twenty to its name is how this tool first
        # stamped every offset in the object 'CommonCutParameters'. Size and single-mindedness are the filter.
        if len(touched) == 1 and size <= 0x100:
            single[addr] = next(iter(touched))
            for offset in touched:
                (writes if local_writes.get(offset) else reads)[offset].add(addr)

    print("offsets in 0x%X..0x%X with a named single-field accessor among their users" % (lo, hi))
    print("(an accessor is at most 0x100 bytes and touches exactly one offset in the range)")
    print("")
    for offset in sorted(set(reads) | set(writes)):
        rnames = sorted(set(N.direct(a) for a in reads[offset] if N.direct(a)))
        wnames = sorted(set(N.direct(a) for a in writes[offset] if N.direct(a)))
        if not (rnames or wnames):
            continue
        rnouns = set(n for n in (noun(x) for x in rnames) if n)
        wnouns = set(n for n in (noun(x) for x in wnames) if n)
        both = sorted(rnouns & wnouns)
        verdict = ""
        if both:
            verdict = "  <== FIELD NAME: %s (Get and Set agree)" % ", ".join(both)
        elif wnouns:
            verdict = "  <== setter noun: %s" % ", ".join(sorted(wnouns))
        elif rnouns:
            verdict = "  <== getter noun: %s" % ", ".join(sorted(rnouns))
        print("+0x%-6X readers %-3d writers %-3d%s" % (offset, len(reads[offset]), len(writes[offset]), verdict))
        if rnames:
            print("            getters/readers: %s" % ", ".join(rnames[:10]))
        if wnames:
            print("            setters/writers: %s" % ", ".join(wnames[:10]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
