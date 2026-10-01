"""Confirm the angle-conversion constants of 0x5C22D0 and read 0x1380D0's sin window."""
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


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


print("=== 0x5C22D0 constants ===")
for rva, why in ((0x9DE758, "divisor (expect 2*pi)"),
                 (0x9DE740, "multiplier (expect 360e10)"),
                 (0x9DE750, "addend (expect 0.5)"),
                 (0x9DE747 if False else 0x9DE758, "")):
    if not why:
        continue
    print("   0x%-8x %-28s = %r" % (rva, why, f64(rva)))
print("   0x%x = %d (0x%x)   <- 360 * 1e10" % (0x34630B8A000, 0x34630B8A000, 0x34630B8A000))

print()
print("=== helpers used by 0x5C22D0 ===")
for rva in (0x634C70, 0x62FA20, 0x62FE20):
    prof = PROF.get(rva) or {}
    print("   0x%x %s size=%s nins=%s" % (rva, name_of(rva), prof.get("size"), prof.get("nins")))
    for ins in disasm(rva, count=8):
        print("        %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))

print()
print("=== 0x1380D0 window around the sin call ===")
lines = list(disasm(0x1380D0))
for idx, ins in enumerate(lines):
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM \
            and ins.operands[0].imm == 0x635970:
        print("  sin at 0x%x" % ins.address)
        for j in range(max(0, idx - 22), min(len(lines), idx + 10)):
            note = ""
            for op in lines[j].operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    t = lines[j].address + lines[j].size + op.mem.disp
                    note = "  ; data@%x=%r" % (t, f64(t)) if t not in STRS else "  ; STR=%r" % STRS[t][:40]
            print("      %-8x %-38s%s" % (lines[j].address, lines[j].mnemonic + " " + lines[j].op_str, note))

print()
print("=== 0x1380D0 window around the angle helper 0x5C22D0 ===")
for idx, ins in enumerate(lines):
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM \
            and ins.operands[0].imm == 0x5C22D0:
        print("  0x5C22D0 at 0x%x" % ins.address)
        for j in range(max(0, idx - 10), min(len(lines), idx + 6)):
            print("      %-8x %-38s" % (lines[j].address, lines[j].mnemonic + " " + lines[j].op_str))
