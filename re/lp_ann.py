import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import struct

def show(rva, n=70):
    print('--- %08X' % rva)
    c = 0
    for ins in disasm(rva):
        ops = []
        for op in ins.operands:
            if op.type == 3 and op.mem.base == 41:
                t = ins.address + ins.size + op.mem.disp
                s = STRS.get(t)
                if s:
                    ops.append('  ; "%s"' % s[:70])
        print('  %08X %-22s %s%s' % (ins.address, ins.mnemonic, ins.op_str, ''.join(ops)))
        c += 1
        if c >= n: break

for a in [int(x, 16) for x in sys.argv[1:]]:
    show(a)
