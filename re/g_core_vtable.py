"""Confirm 0x4FC3A0 and name the core's own vtable (address point 0xA3BB80).

The pipe-mode path does `call 0x4FC3A0(arg)` then reads [rax+8..+0x28] into core+8/+0x10/+0x20/
+0x18/+0x38, so 0x4FC3A0 should be `[[arg]]+0x170`. And 0x6AC250 (the next function) installs
address point 0xA3BB80, which is probably the core's own vtable.
"""
import struct
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
IMAGE_BASE = 0x6B4C0000


def read_q(rva):
    off = rva2off(rva)
    return struct.unpack("<Q", data[off:off + 8])[0] if off is not None else None


def read_cstr(rva, n=160):
    off = rva2off(rva)
    if off is None:
        return None
    raw = data[off:off + n]
    i = raw.find(b"\x00")
    if i >= 0:
        raw = raw[:i]
    t = raw.decode("latin-1")
    return t if t and all(32 <= ord(c) < 127 for c in t) else None


def name_for(ap):
    for delta in (8, 0x18, 0x10, 0x20):
        va = read_q(ap - delta)
        if not va:
            continue
        ti = va - IMAGE_BASE if va >= IMAGE_BASE else va
        nm_va = read_q(ti + 8)
        if not nm_va:
            continue
        nm = nm_va - IMAGE_BASE if nm_va >= IMAGE_BASE else nm_va
        s = read_cstr(nm)
        if s and s.startswith("N"):
            return "typeinfo RVA 0x%x name RVA 0x%x = %r" % (ti, nm, s)
    return "unresolved"


print("=== 0x4FC3A0 ===")
for ins in disasm(0x4FC3A0, count=5):
    print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))

print()
print("=== address points near the row/core code ===")
for ap in (0xA3BB80, 0xA3BB90, 0xA3BBA0, 0xA3BBB0, 0xA3BBC0, 0xA3BBD0):
    print("   AP 0x%-8x : %s" % (ap, name_for(ap)))

print()
print("=== 0x6AC250 (the function after the pipe path) head ===")
for ins in disasm(0x6AC250, count=14):
    note = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            note.append("AP->%s" % name_for(t) if 0xA3B000 <= t <= 0xA3C000 else "data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            note.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
    print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(note)))
