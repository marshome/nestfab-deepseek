"""The rsp+0x110 object: its initialiser 0x136C00, the merge 0x137A90, and 0x134F30.

Also reconstruct their inline strings, which historically gave the source file (and hence the
class) names for this translation unit.
"""
import struct
import sys
from collections import defaultdict

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
BYTES = {1: "<b", 2: "<h", 4: "<i", 8: "<q"}
JUMPS = ("jmp", "je", "jne", "jle", "jl", "jg", "jge", "ja", "jb", "jae", "jbe", "jp", "jnp",
         "call", "ret")


def pack(imm, size):
    fmt = BYTES.get(size)
    if fmt is None:
        return None
    v = imm & ((1 << (size * 8)) - 1)
    if size == 8 and v > 0x7FFFFFFFFFFFFFFF:
        v -= 1 << 64
    return struct.pack(fmt, v)


def inline_strings(fn):
    imm_of, bufs = {}, defaultdict(dict)
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
        if ins.mnemonic in ("mov", "movabs") and len(ops) == 2 and ops[0].type == X86_OP_MEM:
            if ops[1].type == X86_OP_REG:
                d = imm_of.get(ins.reg_name(ops[1].reg))
            elif ops[1].type == X86_OP_IMM:
                d = pack(ops[1].imm, ops[1].size or 8)
            else:
                d = None
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
        if txt.count(".") <= len(txt) * 0.6 and len(txt) >= 5:
            out.append((base, lo, txt))
    return out


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


def dump(fn, count=None):
    prof = PROF.get(fn) or {}
    print()
    print("=== 0x%x %s size=%s nins=%s ===" % (fn, NAMES.get(fn, "?"), prof.get("size"),
                                               prof.get("nins")))
    for ins in disasm(fn, count=count):
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    ctx.append("STR@%x %r" % (t, STRS[t][:40]))
                else:
                    ctx.append("data@%x=%r" % (t, f64(t)))
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))
    for base, lo, txt in inline_strings(fn):
        print("   [inline str %s+0x%x] %r" % (base, lo, txt))


dump(0x136C00)
dump(0x134F30, count=40)
dump(0x137A90, count=45)
