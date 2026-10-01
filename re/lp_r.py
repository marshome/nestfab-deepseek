import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from capstone.x86 import *
ext = func_extent(0x656340)
print('extent', ext)
b = 0x656340
e = ext[1]
o = rva2off(b)
tg=[]
for ins in MD.disasm(data[o:o+(e-b)], b):
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            tg.append(ins.address + ins.size + op.mem.disp)
print([hex(t) for t in tg])
print('FUNCS contains?', sum(1 for x in FUNCS if x[0]==0x656340), 'total', len(FUNCS))
print('near', [ (hex(a),hex(bb)) for a,bb,_ in FUNCS if 0x656300<=a<=0x6563a0])
