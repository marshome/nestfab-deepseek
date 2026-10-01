"""Compressed view of 0x1380D0 (Row::Squeezer cost): only floating point dataflow,
control flow and the interval field accesses, so the arithmetic chain is readable.

Also prints the stack slot usage map, since the function spills the two intervals.
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
TARGET = 0x1380D0


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


KEEP_MNEMONIC = {
    "movsd", "movapd", "movaps", "movups", "movd", "movq",
    "addsd", "subsd", "mulsd", "divsd", "sqrtsd", "maxsd", "minsd",
    "ucomisd", "comisd", "cvtsi2sd", "cvttsd2si", "cvtsd2si", "xorpd", "andpd", "orpd",
    "pxor", "unpcklpd", "shufpd", "addpd", "subpd", "mulpd", "divpd",
    "call", "ret", "jmp", "je", "jne", "jbe", "jae", "jb", "ja", "jl", "jg", "jle", "jge",
    "jp", "jnp", "test", "cmp",
}
KEEP_PREFIX = ("j",)

OUT = r"D:\Nesting\nestfab\re\out_g_1380d0_flow.txt"
with open(OUT, "w", encoding="utf-8") as fh:
    call_targets = {}
    print("#### 0x1380D0 compressed flow  size=%s nins=%s" %
          ((PROF.get(TARGET) or {}).get("size"), (PROF.get(TARGET) or {}).get("nins")), file=fh)
    for ins in disasm(TARGET):
        m = ins.mnemonic
        keep = (m in KEEP_MNEMONIC) or any(m.startswith(p) and len(m) <= 4 for p in KEEP_PREFIX)
        if not keep:
            # still show the constant loads and the field writes into the result object
            if m in ("lea", "mov", "movzx", "movsxd") and ins.operands:
                dst = ins.operands[0]
                if dst.type == X86_OP_MEM and dst.mem.disp != 0 and dst.mem.base not in (41,):
                    pass
                else:
                    continue
            else:
                continue
        notes = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    notes.append("STR@%x %r" % (t, STRS[t][:50]))
                else:
                    try:
                        import struct as _s
                        off = rva2off(t)
                        v = _s.unpack("<d", data[off:off + 8])[0] if off else None
                        notes.append("data@%x=%r" % (t, v))
                    except Exception:
                        notes.append("data@%x" % t)
            elif op.type == X86_OP_IMM and m == "call":
                notes.append(name_of(op.imm) or ("0x%x" % op.imm))
                call_targets[op.imm] = call_targets.get(op.imm, 0) + 1
        print("%-8x %-40s %s" % (ins.address, m + " " + ins.op_str,
                                 ("; " + " | ".join(notes)) if notes else ""), file=fh)
print("wrote", OUT)
print("lines:", sum(1 for _ in open(OUT, encoding="utf-8")))
