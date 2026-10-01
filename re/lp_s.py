import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from capstone.x86 import *
import collections
targets = {0xa3ada0:'Lp', 0xa3aed0:'PC', 0xa3b0b0:'Box', 0xa3b0f0:'Hull', 0xa3b130:'Alpha', 0xa3b170:'LC',
           0xa3b1b0:'BD', 0xa3b1e0:'SQ', 0xa3b270:'CoinLP'}
hits = collections.defaultdict(set)
cnt = 0
for b, e, u in FUNCS:
    o = rva2off(b)
    if o is None:
        continue
    for ins in MD.disasm(data[o:o + (e - b)], b):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in targets:
                    hits[t].add(b)
                    cnt += 1
print('raw hits', cnt)
for t, n in targets.items():
    print(n, hex(t), sorted('%X' % f for f in hits[t])[:20])
