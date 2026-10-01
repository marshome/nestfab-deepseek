"""Decode the inline-constructed assertion strings of the pricer assembly 0x4D64C0.

The rprice translation unit builds its assertion messages from immediates stored into a freshly
allocated buffer (there is no rodata anchor), so a string table lookup inside .text yields
artefacts. Reconstruct them by walking the store instructions and placing each immediate at the
[i + offset] it is written to.
"""
import struct
import sys
from collections import defaultdict

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG  # noqa: E402


def assemble(rva_start, rva_end):
    """Collect immediate stores to [reg+disp] and rebuild the strings."""
    bufs = defaultdict(dict)
    for ins in disasm(rva_start):
        if ins.address >= rva_end:
            break
        if len(ins.operands) != 2:
            continue
        dst, src = ins.operands
        if dst.type != X86_OP_MEM or src.type != X86_OP_IMM:
            continue
        base = ins.reg_name(dst.mem.base)
        data = None
        if ins.mnemonic in ("mov", "movabs"):
            data = struct.pack("<q", src.imm & 0xFFFFFFFFFFFFFFFF)
        elif ins.mnemonic in ("mov",) and src.size == 4:
            data = struct.pack("<i", src.imm & 0xFFFFFFFF)
        elif ins.mnemonic == "mov" and src.size == 2:
            data = struct.pack("<h", src.imm & 0xFFFF)
        elif ins.mnemonic == "mov" and src.size == 1:
            data = struct.pack("<b", src.imm & 0xFF)
        if data is None:
            if ins.mnemonic == "mov" and src.size == 8:
                data = struct.pack("<q", src.imm & 0xFFFFFFFFFFFFFFFF)
            else:
                continue
        for k, b in enumerate(data):
            bufs[base][dst.mem.disp + k] = b
    out = []
    for base, m in bufs.items():
        if not m:
            continue
        lo, hi = min(m), max(m)
        raw = bytes(m.get(i, 0x2E) for i in range(lo, hi + 1))
        txt = "".join(chr(c) if 32 <= c < 127 else "." for c in raw)
        out.append((base, lo, hi, txt))
    return out


print("=== 0x4D64C0 immediate-string reconstruction ===")
for base, lo, hi, txt in assemble(0x4D64C0, 0x4D6720):
    print("   [%s+0x%x .. +0x%x]  %r" % (base, lo, hi, txt))

print()
print("=== the same for the pricer constructors region 0x4D97B0-0x4DA000 ===")
for f in (0x4D97B0, 0x4D9AD0, 0x4D9B00, 0x4D9B30, 0x4D9CD0, 0x4D9DE0, 0x4D9F80):
    res = assemble(f, (PROF_END := (f + (load_prof().get(f, {}) or {}).get("size", 400))))
    if not res:
        continue
    print("  --- 0x%x" % f)
    for base, lo, hi, txt in res:
        print("     [%s+0x%x]  %r" % (base, lo, txt))
