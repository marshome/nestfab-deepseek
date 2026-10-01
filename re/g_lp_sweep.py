"""Batch sweep for every remaining unknown in the COIN-OR / Lp / Prc / Row layer.

Covers, in one pass:
  1. the constants BuildAndSolveLp and the CoinLP slots use (penalty double, Clp bounds)
  2. the semantics of CoinLP vtable slots 2..8
  3. 0x7CA830: which Clp entry point it drives (addRows / addColumns / loadProblem)
  4. the helper functions BuildAndSolveLp calls, so the 0x1A8-stride records are identified
  5. the three remaining CoinLP construction sites
  6. findings_lp.md section 8 leftovers: Row::Squeezer cost 0x1380D0, the three non
     polymorphic Prc types, the LSQR owner
"""
import struct
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
OUT = r"D:\Nesting\nestfab\re\out_g_lp_use_sweep.txt"
fh = open(OUT, "w", encoding="utf-8")


def p(*a):
    print(*a, file=fh)


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


def read_f64(rva):
    off = rva2off(rva)
    if off is None or off + 8 > len(data):
        return None
    return struct.unpack("<d", data[off:off + 8])[0]


def read_u64(rva):
    off = rva2off(rva)
    if off is None or off + 8 > len(data):
        return None
    return u64(off)


def read_i32(rva):
    off = rva2off(rva)
    if off is None or off + 4 > len(data):
        return None
    return struct.unpack("<i", data[off:off + 4])[0]


# ------------------------------------------------------------------ 1
p("=" * 78)
p("1. constants")
p("=" * 78)
for rva, why in [
    (0x9B08B0, "BuildAndSolveLp xmm8  (dummy column coefficient?)"),
    (0x9C2E18, "used by CoinLP ctor and slot 4"),
    (0x9C2DF8, "Clp bound constant"),
    (0x9C2E20, "Clp bound constant"),
    (0x9C2E30, "Clp bound constant"),
    (0x9B0726, "string 'linear'"),
    (0x9B0776, "assert 'biggest_sheet->price()'"),
    (0x9B0810, "assert 'BuildAndSolveLp'"),
    (0x9B0710, "assert '..\\multi\\database.cpp'"),
    (0xA078F0, "rdx constant in BuildAndSolveLp prologue"),
]:
    f = read_f64(rva)
    u = read_u64(rva)
    s = STRS.get(rva)
    p("  0x%-8x %-46s f64=%-24r u64=0x%x %s" % (rva, why, f, u or 0,
                                                 ("STR=%r" % s[:60]) if s else ""))

# ------------------------------------------------------------------ 2
p()
p("=" * 78)
p("2. CoinLP vtable slot bodies (slots 2..8)")
p("=" * 78)
SLOTS = {
    2: (0x679C20, "calls ClpSimplex vtable +0x498"),
    3: (0x679660, "mov [rcx+0x10], dl"),
    4: (0x6792C0, "takes bool + double, uses Clp bounds"),
    5: (0x679670, "called per PART with (n, idx[], val[], demand)"),
    6: (0x679940, ""),
    7: (0x679420, ""),
    8: (0x679D00, "called to solve; return tested"),
}
for k, (rva, why) in SLOTS.items():
    prof = PROF.get(rva) or {}
    p()
    p("--- slot %d = 0x%x  size=%s nins=%s   %s" % (k, rva, prof.get("size"), prof.get("nins"), why))
    for ins in disasm(rva):
        note = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                note.append("STR@%x %r" % (t, STRS[t][:60]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
        p("    %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                 ("; " + " | ".join(note)) if note else ""))
    p("    -- callees --")
    seen = set()
    for ins in disasm(rva):
        if ins.mnemonic == "call":
            op = ins.operands[0]
            if op.type == X86_OP_IMM and op.imm not in seen:
                seen.add(op.imm)
                p("       -> 0x%-8x %s" % (op.imm, name_of(op.imm)))
            elif op.type == X86_OP_MEM:
                p("       -> virtual [%s]" % ins.op_str)

# ------------------------------------------------------------------ 3
p()
p("=" * 78)
p("3. 0x7CA830 -- which Clp entry point? (addRows / addColumns / loadProblem)")
p("=" * 78)
prof = PROF.get(0x7CA830) or {}
p("size=%s nins=%s" % (prof.get("size"), prof.get("nins")))
for ins in disasm(0x7CA830):
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            if t in STRS:
                p("    @0x%-7x STR@%x %r" % (ins.address, t, STRS[t][:80]))
p("   -- callees --")
seen = set()
for ins in disasm(0x7CA830):
    if ins.mnemonic == "call":
        op = ins.operands[0]
        if op.type == X86_OP_IMM and op.imm not in seen:
            seen.add(op.imm)
            p("      -> 0x%-8x %s size=%s" % (op.imm, name_of(op.imm),
                                              (PROF.get(op.imm) or {}).get("size")))
        elif op.type == X86_OP_MEM:
            p("      -> virtual %s" % ins.op_str)

# ------------------------------------------------------------------ 4
p()
p("=" * 78)
p("4. helpers BuildAndSolveLp uses")
p("=" * 78)
for rva, why in [
    (0x4F8550, "returns double (sheet/part price?)"),
    (0x51D2F0, ""),
    (0x523050, "returns pointer"),
    (0x4FC5A0, "returns int (number of parts?)"),
    (0x4FC5B0, "GetPart"),
    (0x4F7050, "returns int from a Part (demand?)"),
    (0x5F4310, "container ctor with 0xA078F0"),
    (0x5F4340, "cleanup"),
    (0x90BEF0, ""),
    (0x90CAF0, ""),
]:
    prof = PROF.get(rva) or {}
    p()
    p("--- 0x%x %s  size=%s nins=%s   %s" % (rva, name_of(rva), prof.get("size"),
                                             prof.get("nins"), why))
    for ins in disasm(rva, count=14):
        note = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                note.append("STR@%x %r" % (t, STRS[t][:70]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
        p("    %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                 ("; " + " | ".join(note)) if note else ""))

# ------------------------------------------------------------------ 5
p()
p("=" * 78)
p("5. remaining CoinLP construction sites")
p("=" * 78)
for fn, site in [(0x24E2D0, 0x24E2DB), (0x25B040, 0x25B0EF), (0x6A6AD0, 0x6A6B73)]:
    p()
    p("--- owner 0x%x size=%s, construction at 0x%x" % (fn, (PROF.get(fn) or {}).get("size"), site))
    for ins in disasm(fn):
        if site - 0x40 <= ins.address <= site + 0x70:
            note = []
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    t = ins.address + ins.size + op.mem.disp
                    note.append("STR@%x %r" % (t, STRS[t][:70]) if t in STRS else "data@%x" % t)
                elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                    note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
            p("    %-8x %-40s %s%s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                      ("; " + " | ".join(note)) if note else "",
                                      "   <<< construct" if ins.address == site else ""))

# ------------------------------------------------------------------ 6
p()
p("=" * 78)
p("6. leftovers from findings_lp.md section 8")
p("=" * 78)
p("--- Row::Squeezer cost function 0x1380D0 ---")
prof = PROF.get(0x1380D0) or {}
p("size=%s nins=%s" % (prof.get("size"), prof.get("nins")))
for ins in disasm(0x1380D0, count=30):
    note = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            note.append("STR@%x %r" % (t, STRS[t][:70]) if t in STRS else "data@%x" % t)
    p("    %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                             ("; " + " | ".join(note)) if note else ""))

p()
p("--- who references the LSQR message block 0x9A74A0 ---")
for rva in sorted(PROF):
    try:
        for ins in disasm(rva):
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    t = ins.address + ins.size + op.mem.disp
                    if 0x9A74A0 <= t < 0x9A7700:
                        p("    0x%-8x @0x%-8x -> 0x%x %s %r" % (rva, ins.address, t,
                                                                 name_of(rva), STRS.get(t, "")[:60]))
    except Exception:
        continue

p()
p("--- non polymorphic Prc types: strings that name them ---")
for rva, s in sorted(STRS.items()):
    if any(k in s for k in ("BoostAlpha", "SurfaceCoeffs", "DimAlpha", "AlphaSurfacePricer",
                            "DimPricer")):
        p("    @0x%-8x %r" % (rva, s[:90]))

fh.close()
print("wrote", OUT)
