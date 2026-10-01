"""Read the annotation string 0x9D9B66 that the reflection registry uses for all three
orphan Prc types, plus its neighbourhood."""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

print("=== rodata around 0x9D9B00-0x9D9C20 ===")
for rva in sorted(STRS):
    if 0x9D9B00 <= rva <= 0x9D9C20:
        print("   0x%-8x %r" % (rva, STRS[rva][:100]))

print()
print("=== raw bytes at 0x9D9B66 (160 bytes) ===")
off = rva2off(0x9D9B66)
raw = data[off:off + 160]
print("   " + "".join(chr(c) if 32 <= c < 127 else "." for c in raw))

print()
print("=== the two log-tag functions and their neighbours ===")
PROF = load_prof()
for rva in (0x220ED0, 0x221110, 0x222200):
    prof = PROF.get(rva) or {}
    strings = []
    for ins in disasm(rva):
        for op in ins.operands:
            if op.type == 3 and op.mem.base == 41:  # X86_OP_MEM with RIP base
                import capstone.x86 as cx
                pass
    print("   0x%x size=%s nins=%s" % (rva, prof.get("size"), prof.get("nins")))
