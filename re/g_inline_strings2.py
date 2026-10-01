"""Decode inline-constructed strings with a light dataflow pass.

The rprice code builds messages as
    movabs rcx, <8 bytes>;  mov [rax+8], rcx
so a pure immediate->memory scan misses them. Track the last immediate loaded into each register
(and invalidate it on any other write) so the stores can be resolved.
"""
import struct
import sys
from collections import defaultdict

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG  # noqa: E402

PROF = load_prof()
BYTES = {1: "<b", 2: "<h", 4: "<i", 8: "<q"}


def pack(imm, size):
    fmt = BYTES.get(size)
    if fmt is None:
        return None
    mask = (1 << (size * 8)) - 1
    return struct.pack(fmt, imm & mask)


def assemble(fn):
    imm_of = {}                      # register -> (bytes, size)
    bufs = defaultdict(dict)
    for ins in disasm(fn):
        ops = ins.operands
        if ins.mnemonic in ("jmp", "je", "jne", "jle", "jl", "jg", "jge", "ja", "jb", "jae", "jbe",
                            "jp", "jnp", "call", "ret"):
            imm_of.clear()           # control flow joins: drop the tracked constants
            continue
        # mov reg, imm  /  movabs reg, imm
        if ins.mnemonic in ("mov", "movabs") and len(ops) == 2 and ops[0].type == X86_OP_REG \
                and ops[1].type == X86_OP_IMM:
            data = pack(ops[1].imm, ops[1].size or 8)
            if data is not None:
                imm_of[ins.reg_name(ops[0].reg)] = data
            continue
        # mov [mem], reg
        if ins.mnemonic in ("mov", "movabs") and len(ops) == 2 and ops[0].type == X86_OP_MEM \
                and ops[1].type == X86_OP_REG:
            reg = ins.reg_name(ops[1].reg)
            data = imm_of.get(reg)
            if data:
                base = ins.reg_name(ops[0].mem.base)
                for k, b in enumerate(data):
                    bufs[base][ops[0].mem.disp + k] = b
            continue
        # mov [mem], imm
        if ins.mnemonic in ("mov", "movabs") and len(ops) == 2 and ops[0].type == X86_OP_MEM \
                and ops[1].type == X86_OP_IMM:
            data = pack(ops[1].imm, ops[1].size or 8)
            if data:
                base = ins.reg_name(ops[0].mem.base)
                for k, b in enumerate(data):
                    bufs[base][ops[0].mem.disp + k] = b
            continue
        # any other write to a register invalidates it
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
        if txt.count(".") <= len(txt) * 0.5:
            out.append((base, lo, txt))
    return out


for fn in (0x4D64C0, 0x4D97B0, 0x4D84D0, 0x7CA370, 0x220ED0, 0x23B080, 0x4F0D00):
    prof = PROF.get(fn) or {}
    res = assemble(fn)
    print("=== 0x%x size=%s nins=%s -> %d candidate string(s)" % (fn, prof.get("size"),
                                                                 prof.get("nins"), len(res)))
    for base, lo, txt in res:
        print("    [%s+0x%x]  %r" % (base, lo, txt))
