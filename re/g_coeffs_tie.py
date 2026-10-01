"""Tie the 5-double coefficient struct to a name.

Leads from the identifier scan:
  * 0x7CA430 'coeffs >' sits INSIDE LinearCombinationPricer::slot2 = 0x7CA370 (578 B)
  * 0x24DFC0 'coeffs.si...' is somewhere in the 0x24xxxx range
  * 0x4D9913 'alpha > ' / 0x4D993E '& alpha ' / 0x4D9979 'BoxDimSu...' sit just before the pricer
    factories at 0x4D9AD0
Print the strings per owning function and the member offsets each one touches.
"""
import sys
from collections import Counter

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


def owner_of(addr):
    for rva in sorted(PROF):
        ext = func_extent(rva)
        if ext and ext[0] <= addr < ext[1]:
            return rva
    return None


TARGETS = [0x7CA370, 0x7CA5C0, 0x7CA6C0, 0x24DFC0, 0x4D9900, 0x4D9B60, 0x2BE9A, 0x4F0E14]
print("=== owners and strings ===")
for t in TARGETS:
    o = owner_of(t) if t not in PROF else t
    if o is None:
        print("  0x%x : no owner" % t)
        continue
    prof = PROF.get(o) or {}
    strings = []
    for ins in disasm(o):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                s = ins.address + ins.size + op.mem.disp
                if s in STRS and STRS[s] not in strings:
                    strings.append(STRS[s])
    print()
    print("--- 0x%x %s size=%s nins=%s   (from 0x%x)" % (o, name_of(o), prof.get("size"),
                                                         prof.get("nins"), t))
    for s in strings[:12]:
        print("      %r" % s[:80])

print()
print("=== member offsets touched by LinearCombinationPricer slots ===")
for rva in (0x7CA370, 0x7CA6C0, 0x7CA5C0):
    writes = Counter()
    reads = Counter()
    for ins in disasm(rva):
        if not ins.operands:
            continue
        dst = ins.operands[0]
        if dst.type == X86_OP_MEM and dst.mem.base not in (0, X86_REG_RIP):
            reg = ins.reg_name(dst.mem.base)
            if reg not in ("rsp", "rbp") and ins.mnemonic.startswith(
                    ("mov", "add", "sub", "or", "and", "xor", "movsd", "movaps", "movups", "movapd")):
                writes[(reg, dst.mem.disp)] += 1
        for op in ins.operands[1:]:
            if op.type == X86_OP_MEM and op.mem.base not in (0, X86_REG_RIP):
                reg = ins.reg_name(op.mem.base)
                if reg not in ("rsp", "rbp"):
                    reads[(reg, op.mem.disp)] += 1
    print("  0x%x writes %s" % (rva, ", ".join("[%s+0x%x]x%d" % (r, d, n)
                                              for (r, d), n in sorted(writes.items(), key=lambda kv: -kv[1])[:8])))
    print("        reads  %s" % ", ".join("[%s+0x%x]x%d" % (r, d, n)
                                          for (r, d), n in sorted(reads.items(), key=lambda kv: -kv[1])[:10]))
