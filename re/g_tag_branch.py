"""(a) 0x5CEE50's tag != 0 path in full; (b) who writes element +0xa0 / +0x98 / +0x99?
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


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


print("=== (a) 0x5CEE50 from 0x5CEF36 (the store block) to 0x5CEFE0 ===")
for ins in disasm(0x5CEE50):
    if 0x5CEF36 <= ins.address < 0x5CEFE0:
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ctx.append("data@%x=%r" % (t, f64(t)))
        print("   %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))

print()
print("=== (b) writers of +0xa0 / +0x98 / +0x99 anywhere in 0x133000..0x13B000 ===")
targets = {0xa0, 0x98, 0x99}
hits = 0
for rva in sorted(PROF):
    if not (0x133000 <= rva < 0x13B000):
        continue
    try:
        lines = list(disasm(rva, count=600))
    except Exception:
        continue
    for ins in lines:
        if not ins.operands:
            continue
        d = ins.operands[0]
        try:
            if d.type == 3 and d.mem.index == 0 and d.mem.disp in targets and d.mem.base not in (0, 41):
                if ins.mnemonic.startswith(("mov", "movsd", "add", "sub", "or", "and", "xor")):
                    print("   @0x%-8x (fn 0x%x) %s" % (ins.address, rva, ins.mnemonic + " " + ins.op_str))
                    hits += 1
                    if hits > 40:
                        raise SystemExit
        except SystemExit:
            raise
        except Exception:
            pass
print("   total %d" % hits)
