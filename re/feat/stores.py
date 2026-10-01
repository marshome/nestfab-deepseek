"""Print all stores of form [reg+disp] for a function, with the reg."""
import sys
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from capstone.x86 import *

for a in sys.argv[1:]:
    rva = int(a, 0)
    print('=== 0x%X' % rva)
    for i in disasm(rva):
        if len(i.operands) == 2 and i.mnemonic.startswith('mov') and i.operands[0].type == X86_OP_MEM:
            d, s = i.operands[0], i.operands[1]
            if d.mem.base and d.mem.index == 0:
                v = i.reg_name(s.reg) if s.type == X86_OP_REG else (hex(s.imm) if s.type == X86_OP_IMM else '?')
                print('  %06X  %s[%s+0x%X] <- %s' % (i.address,
                      {1: 'B', 2: 'W', 4: 'D', 8: 'Q'}.get(d.size, '?'), i.reg_name(d.mem.base), d.mem.disp, v))
