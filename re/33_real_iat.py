"""Locate the real (loader-rebuilt) IAT used by the app's jmp-thunks."""
import sys, struct, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

thunks = {}
sec = [s for s in SEC if s[5] & 0x20000000]
for name, va, vs, pr, rs, ch in sec:
    for ins in MD.disasm(data[pr:pr+rs], va):
        if ins.mnemonic == 'jmp' and ins.operands:
            op = ins.operands[0]
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                thunks[ins.address] = t
print("total jmp-thunks: %d" % len(thunks))
tgt = collections.Counter(thunks.values())
print("distinct thunk targets: %d" % len(tgt))
print("target address range: %08X .. %08X" % (min(tgt), max(tgt)))
print("\nmost common targets:")
for a, c in tgt.most_common(12):
    print("   %08X  x%d" % (a, c))

print("\n--- hexdump of the region around the main target ---")
lo = 0x00B28E00; hi = 0x00B29000
o = rva2off(lo)
raw = data[o:o+(hi-lo)]
resolved = 0
for i in range(0, len(raw), 8):
    v = struct.unpack_from('<Q', raw, i)[0]
    if 0x7FF000000000 <= v <= 0x800000000000: resolved += 1
print("8-byte values in %08X..%08X that look like loaded addresses (0x7FF...): %d / %d"
      % (lo, hi, resolved, len(raw)//8))
for i in range(0, min(len(raw), 0x200), 8):
    a = lo + i; v = struct.unpack_from('<Q', raw, i)[0]
    mark = '   <-- loaded addr' if 0x7FF000000000 <= v <= 0x800000000000 else ''
    print("   %08X  %016X%s" % (a, v, mark))

# how many thunks point into a loaded-address-looking table?
in_tbl = [t for t in tgt if 0x00B28E00 <= t < 0x00B2A000]
print("\nthunks pointing into 0xB28E00..0xB2A000: %d (distinct %d)" % (len(in_tbl), len(set(in_tbl))))
