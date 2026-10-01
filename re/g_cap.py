"""Confirm the source-record layout: is [rec+0xc] really 10000 (the drain cap)?

0x133DE0 builds a one-element container at rsp+0x60:
    133EBB  new(0x10)
    133EC9  [rax]    = rdi            ; the angle transform from 0x5CEE50
    133EDF  rbx      = 0x271000000000
    133EE9  [rax+8]  = rbx
Then 0x137FE0 iterates it: `esi = dword [rbx+0xc]`, and retries 0x137A90 until it returns 0 or esi
is exhausted. Decode the immediate by byte offset and re-read that loop.
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

v = 0x271000000000
b = v.to_bytes(8, "little")
print("immediate 0x%x bytes (LE): %s" % (v, " ".join("%02x" % x for x in b)))
print("  byte  [+8] = 0x%02x" % b[0])
print("  u32   [+0xc] = 0x%08x = %d   <- the drain cap 0x137FE0 reads" %
      (int.from_bytes(b[4:8], "little"), int.from_bytes(b[4:8], "little")))

PROF = load_prof()
print()
print("=== 0x137FE0 again, the drain loop in full ===")
for ins in disasm(0x137FE0):
    print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
