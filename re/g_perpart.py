"""Stage 1: the predicate 0x5C2E40 and the skeleton of the per-part cost 0x133DE0.

For 0x133DE0 (1458 B) start with structure rather than every instruction: its calls (which name
the geometry operations), its rodata constants, and which offsets of its output it writes. That
usually exposes the formula.
"""
import struct
import sys
from collections import Counter

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
IMAGE = 0x6B4C0000


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


for fn, label in ((0x5C2E40, "predicate"), (0x133DE0, "per-part cost")):
    prof = PROF.get(fn) or {}
    print("=== 0x%x (%s) size=%s nins=%s ===" % (fn, label, prof.get("size"), prof.get("nins")))

print()
print("=== 0x5C2E40 in full ===")
for ins in disasm(0x5C2E40):
    ctx = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            ctx.append("STR@%x %r" % (t, STRS[t][:40]) if t in STRS else "data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            ctx.append("%s(0x%x)" % (name_of(op.imm), op.imm))
    print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))

print()
print("=== 0x133DE0: calls in order ===")
seen = []
for ins in disasm(0x133DE0):
    if ins.mnemonic == "call":
        op = ins.operands[0]
        if op.type == X86_OP_IMM:
            k = (ins.address, op.imm, name_of(op.imm))
        else:
            k = (ins.address, None, "[reg]")
        seen.append(k)
for a, t, n in seen:
    print("   @0x%-8x %s" % (a, ("0x%x %s" % (t, n)) if t else n))

print()
print("=== 0x133DE0: rodata constants read ===")
for ins in disasm(0x133DE0):
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            if t in STRS:
                print("   @0x%-8x STR@0x%-8x %r" % (ins.address, t, STRS[t][:50]))
            else:
                v = f64(t)
                print("   @0x%-8x data@0x%-8x = %r" % (ins.address, t, v))

print()
print("=== 0x133DE0: writes by base register/offset (first 24 by count) ===")
w = Counter()
for ins in disasm(0x133DE0):
    if not ins.operands:
        continue
    d = ins.operands[0]
    if d.type == X86_OP_MEM and d.mem.base not in (0, 41) and d.mem.index == 0:
        reg = ins.reg_name(d.mem.base)
        if reg not in ("rsp", "rbp") and ins.mnemonic.startswith(
                ("mov", "movsd", "movups", "movaps", "add", "or", "and", "xor")):
            w[(reg, d.mem.disp)] += 1
for (reg, disp), n in sorted(w.items(), key=lambda kv: -kv[1])[:24]:
    print("   [%s+0x%x] x%d" % (reg, disp, n))
