import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from capstone.x86 import *
print('X86_OP_MEM', X86_OP_MEM, 'X86_REG_RIP', X86_REG_RIP)
o = rva2off(0x656340)
for ins in MD.disasm(data[o:o+32], 0x656340):
    print(hex(ins.address), ins.mnemonic, ins.op_str, [(op.type, getattr(op,'mem',None) and (op.mem.base, op.mem.index, op.mem.disp)) for op in ins.operands])
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            print('    rip target', hex(ins.address + ins.size + op.mem.disp))
