"""Decode the inline-constructed strings of the Row:: chain and the strategy body.

Last round proved that rodata hits inside .text are artefacts and that the reliable route is to
simulate `movabs reg,imm` + `mov [mem],reg`. Apply that to the functions on the path
    strategy body 0x6AABC0 -> 0x8F210 -> 0x13C380 / 0x134470 -> 0x136B80 -> 0x138A20
so the strategy and the helper calls can be named.
"""
import struct
import sys
from collections import defaultdict

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402 as lib
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_RIP  # noqa: E402

PROF = load_prof()
BYTES = {1: "<b", 2: "<h", 4: "<i", 8: "<q"}


def pack(imm, size):
    fmt = BYTES.get(size)
    if fmt is None:
        return None
    mask = (1 << (size * 8)) - 1
    v = imm & mask
    if size == 8 and v > 0x7FFFFFFFFFFFFFFF:
        v -= 1 << 64
    return struct.pack(fmt, v)


JUMPS = ("jmp", "je", "jne", "jle", "jl", "jg", "jge", "ja", "jb", "jae", "jbe", "jp", "jnp",
         "call", "ret")


def assemble(fn):
    imm_of = {}
    bufs = defaultdict(dict)
    for ins in disasm(fn):
        ops = ins.operands
        if ins.mnemonic in JUMPS:
            imm_of.clear()
            continue
        if ins.mnemonic in ("mov", "movabs") and len(ops) == 2 and ops[0].type == X86_OP_REG \
                and ops[1].type == X86_OP_IMM:
            d = pack(ops[1].imm, ops[1].size or 8)
            if d:
                imm_of[ins.reg_name(ops[0].reg)] = d
            continue
        if ins.mnemonic in ("mov", "movabs") and len(ops) == 2 and ops[0].type == X86_OP_MEM \
                and ops[1].type == X86_OP_REG:
            d = imm_of.get(ins.reg_name(ops[1].reg))
            if d:
                base = ins.reg_name(ops[0].mem.base)
                for k, b in enumerate(d):
                    bufs[base][ops[0].mem.disp + k] = b
            continue
        if ins.mnemonic in ("mov", "movabs") and len(ops) == 2 and ops[0].type == X86_OP_MEM \
                and ops[1].type == X86_OP_IMM:
            d = pack(ops[1].imm, ops[1].size or 8)
            if d:
                base = ins.reg_name(ops[0].mem.base)
                for k, b in enumerate(d):
                    bufs[base][ops[0].mem.disp + k] = b
            continue
        if ops and ops[0].type == X86_OP_REG and ins.mnemonic not in ("cmp", "test", "ucomisd",
                                                                     "comisd"):
            imm_of.pop(ins.reg_name(ops[0].reg), None)
    out = []
    for base, m in bufs.items():
        if not m:
            continue
        lo, hi = min(m), max(m)
        raw = bytes(m.get(i, 0x2E) for i in range(lo, hi + 1))
        txt = "".join(chr(c) if 32 <= c < 127 else "." for c in raw)
        if txt.count(".") <= len(txt) * 0.6 and len(txt) >= 4:
            out.append((base, lo, txt))
    return out


FUNCS = [0x6AABC0, 0x8F210, 0x13C380, 0x134470, 0x136B80, 0x138A20, 0x5CD800, 0x133190,
         0x2530D0, 0x500710, 0x4FFC10, 0x13A360, 0x1380D0]
for fn in FUNCS:
    prof = PROF.get(fn) or {}
    res = assemble(fn)
    print()
    print("=== 0x%x %s size=%s nins=%s" % (fn, (PROF.get(fn, {}) or {}).get("name", ""),
                                           prof.get("size"), prof.get("nins")))
    for base, lo, txt in res:
        print("      [%s+0x%x]  %r" % (base, lo, txt))
