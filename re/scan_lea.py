"""Scan code for RIP-relative LEA/MOV/CALL targeting the vtable page range."""
import sys, collections
sys.path.insert(0, 'D:/Nesting/nestfab/re')
from an3 import *

t0 = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0xa3c000
t1 = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0xa3d800

res = collections.defaultdict(set)   # target rva -> set of func rvas
for name, va, vs, pr, rs, ch in SEC:
    if not (ch & 0x20000000):
        continue
    o = pr
    base = va
    for ins in MD.disasm(data[o:o + rs], base):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                tgt = ins.address + ins.size + op.mem.disp
                if t0 <= tgt < t1:
                    f = owner(ins.address)
                    res[tgt].add(f)
print('targets found:', len(res))
for t in sorted(res):
    print('%08X -> %s' % (t, [hex(x) for x in sorted(res[t]) if x]))
