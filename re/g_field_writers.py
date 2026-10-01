"""Who writes the problem fields that gate and feed the RowNester core?

0x6AABC0 reads:
    0x4FC2F0(arg) = [[arg]+0x170]  (byte gate)
    0x4FC300(arg) = [[arg]+0x1A0]  (byte gate)
    0x4FC3C0(arg) =  [arg]+0x1A0   (pointer; fields read at +8/+0x10/+0x18/+0x20
                                    == problem+0x1A8/+0x1B0/+0x1B8/+0x1C0)
Find the functions that store to those offsets, so the setters (probably named exports) are known.
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_REG  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
OFFSETS = {0x170, 0x1A0, 0x1A8, 0x1B0, 0x1B8, 0x1C0}

STORE = ("mov", "movsd", "movaps", "movapd", "movups", "movd", "movq", "movzx", "or", "and",
         "add", "sub", "xor")

found = {}
for rva in sorted(PROF):
    try:
        for ins in disasm(rva):
            if not ins.operands or ins.mnemonic not in STORE:
                continue
            d = ins.operands[0]
            if d.type != X86_OP_MEM or d.mem.base in (0, 41):
                continue
            base = ins.reg_name(d.mem.base)
            if base in ("rsp", "rbp"):
                continue
            if d.mem.disp in OFFSETS and d.mem.index == 0:
                found.setdefault(rva, []).append((ins.address, d.mem.disp, ins.mnemonic,
                                                  ins.op_str))
    except Exception:
        continue

print("=== functions storing to the gate / config offsets ===")
for rva, sites in sorted(found.items()):
    prof = PROF.get(rva) or {}
    name = NAMES.get(rva) or (prof.get("name") or "")
    offs = sorted(set(s[1] for s in sites))
    print("   0x%-8x %-30s size=%-6s nins=%-5s offsets=%s  (%d store(s))"
          % (rva, name or "?", prof.get("size"), prof.get("nins"),
             ",".join("0x%x" % o for o in offs), len(sites)))

print()
print("=== detail for the small functions (likely setters) ===")
for rva, sites in sorted(found.items()):
    prof = PROF.get(rva) or {}
    if (prof.get("size") or 10 ** 9) > 600:
        continue
    print("  --- 0x%x %s size=%s" % (rva, NAMES.get(rva, "?"), prof.get("size")))
    for ins in disasm(rva):
        note = ""
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == 2:
            note = "call ->"
        elif ins.mnemonic == "call":
            note = "call 0x%x %s" % (ins.operands[0].imm, NAMES.get(ins.operands[0].imm, ""))
        print("      %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, note))
