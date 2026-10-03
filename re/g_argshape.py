# -*- coding: utf-8 -*-
"""The first argument's offsets, following register copies.

Usage: python g_argshape.py 0x2AB0 0x5007C0 0x870070 0x22A20 [--bigger 6]

re/g_members.py marks the register that holds the first argument, but it only follows "mov X, rcx". 0x5007C0 receives the
object in rcx, moves it to rdi once, and then reaches EVERY member through rdi -- so a profile that only looks at rcx sees
one offset out of eighteen, and that is why its member list looked empty. This follows the copies transitively:

    mov rdi, rcx        rdi is the object
    mov r13, rdi        r13 is the object too

and reports the union of the offsets reached through any register in that set, with the width of each access, sorted. That
union is the object's member list, and printing two functions' lists side by side is how a shared type is seen -- which is
what the closure of ordinal 51 needed, since 0x5007C0, 0x870070 and 0x2AB0 all walk the same launch order.

`--bigger N` prints only the offsets touched by at least N of the functions given, which is the intersection and therefore
the part of the type all of them agree on.
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

# **THE DISPLACEMENT IS PARSED BY NUMBER, NOT BY SPELLING.** Capstone prints a ONE-DIGIT displacement in DECIMAL (`[rax + 8]`) and every larger one in hex
# (`[rax + 0x10]`), so a pattern demanding `0x` loses offsets 1 to 9 -- and `8` is the module's most common displacement (`vptr + 8`, the std::shared_ptr count).
# **And the register class must take A-Z**: `r8`-`r15` were outside `[a-z0-9]`, so the alias tracker never saw half the register file. `[rR]\w*` covers both.
ACCESS = re.compile(r"\[([A-Za-z][A-Za-z0-9]*)(?: \+ (0x[0-9a-f]+|\d+))?\]")
MOVE = re.compile(r"^([A-Za-z][A-Za-z0-9]*), ([A-Za-z][A-Za-z0-9]*)$")
WIDTHS = (("xmmword", 16), ("oword", 16), ("qword", 8), ("dword", 4), ("word", 2), ("byte", 1))
STACK = ("rsp", "rbp")
ALIAS = {}
for _full, _names in {
    "rax": ("eax", "ax", "al"), "rbx": ("ebx", "bx", "bl"), "rcx": ("ecx", "cx", "cl"),
    "rdx": ("edx", "dx", "dl"), "rsi": ("esi", "si", "sil"), "rdi": ("edi", "di", "dil"),
}.items():
    ALIAS[_full] = _full
    for _n in _names:
        ALIAS[_n] = _full
for _r in range(8, 16):
    for _suffix in ("", "d", "w", "b"):
        ALIAS["r%d%s" % (_r, _suffix)] = "r%d" % _r


def canonical(reg):
    return ALIAS.get(reg, reg)


def width_of(text):
    for name, width in WIDTHS:
        if name in text:
            return width
    return 0


def arg_registers(body):
    """The set of registers that carry the first argument, following the copies in program order."""
    carries = {"rcx"}
    for ins in body:
        m = MOVE.match(ins.op_str)
        if ins.mnemonic != "mov" or not m:
            continue
        dst, src = canonical(m.group(1)), canonical(m.group(2))
        if src in carries and dst not in STACK:
            carries.add(dst)
    return carries


def profile(body):
    """The member offsets of the first argument AND of what its first pointer points at.

    0x2AB0, 0x5007C0 and 0x870070 each read [rcx] once and then work through the result: the first argument is a HANDLE --
    a shared_ptr's first word, or a wrapper -- and the object with the members is *[rcx]. A profile that stops at the
    handle sees one offset and looks empty, which is exactly what happened: 0x5007C0 showed a single member until the
    dereference was followed, and then it showed the launch order.
    """
    carries = arg_registers(body)
    # a register loaded from [carry + 0] is the object behind the handle. The word "qword ptr " has to be stripped first:
    # capstone writes 'mov rdi, qword ptr [rcx]', and a pattern anchored on "reg, reg" never matches it, which is why the
    # first version of this function still showed one offset.
    behind = set()
    for ins in body:
        m = re.match(r"^([a-z0-9]+), (.+)$", ins.op_str)
        if ins.mnemonic != "mov" or not m:
            continue
        dst = canonical(m.group(1))
        src = re.sub(r"^(byte|word|dword|qword|xmmword|oword) ptr ", "", m.group(2).strip())
        mm = re.match(r"^\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]$", src)
        if mm and canonical(mm.group(1)) in carries and not mm.group(2):
            behind.add(dst)
    # and copies of those
    for _round in range(4):
        for ins in body:
            m = re.match(r"^([a-z0-9]+), ([a-z0-9]+)$", ins.op_str)
            if ins.mnemonic != "mov" or not m:
                continue
            dst, src = canonical(m.group(1)), canonical(m.group(2))
            if src in behind:
                behind.add(dst)
    bases = carries | behind
    out = {}
    for ins in body:
        for m in ACCESS.finditer(ins.op_str):
            reg = canonical(m.group(1))
            if reg not in bases:
                continue
            offset = int(m.group(2), 16) if m.group(2) else 0
            width = width_of(ins.op_str) or 0
            out[offset] = max(out.get(offset, 0), width)
    return out


def main(argv):
    addrs = [int(a, 0) for a in argv if a.startswith("0x")]
    bigger = int(argv[argv.index("--bigger") + 1]) if "--bigger" in argv else 0
    if not addrs:
        print("give one or more function addresses")
        return 2
    profile_map = load_prof()
    profiles = {}
    for addr in addrs:
        size = (profile_map.get(addr) or {}).get("size") or 0
        body = [i for i in disasm(addr) if i.address < addr + size]
        profiles[addr] = profile(body)
        items = sorted(profiles[addr].items())
        print("=== 0x%X (%d bytes)%s -- %d offsets of the first argument"
              % (addr, size, ("  " + N.direct(addr)) if N.direct(addr) else "", len(items)))
        line = []
        for offset, width in items:
            line.append("+0x%X:%s" % (offset, width or "?"))
            if len(line) == 10:
                print("    %s" % " ".join(line))
                line = []
        if line:
            print("    %s" % " ".join(line))
        print("")
    if len(addrs) > 1:
        tally = Counter()
        for addr in addrs:
            for offset in profiles[addr]:
                tally[offset] += 1
        threshold = max(2, bigger)
        shared = sorted(o for o, c in tally.items() if c >= threshold)
        print("offsets touched by at least %d of the %d functions given: %d of %d"
              % (threshold, len(addrs), len(shared), len(tally)))
        line = []
        for offset in shared:
            width = max(profiles[a].get(offset, 0) for a in addrs)
            line.append("+0x%X:%s" % (offset, width or "?"))
            if len(line) == 10:
                print("    %s" % " ".join(line))
                line = []
        if line:
            print("    %s" % " ".join(line))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
