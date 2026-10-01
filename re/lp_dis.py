import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *

def D(rva, n=None):
    print('='*78)
    print('### disasm %08X' % rva)
    for ins in disasm(rva, count=n):
        s = ''
        for op in ins.operands:
            pass
        print('  %08X  %-24s %s' % (ins.address, ins.mnemonic, ins.op_str))

import sys as _s
args = _s.argv[1:]
for a in args:
    D(int(a, 16))
