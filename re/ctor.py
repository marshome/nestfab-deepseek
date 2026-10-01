"""Given a constructor rva, print the vtables it installs (rip lea to a vtable start)."""
import sys
sys.path.insert(0, 'D:/Nesting/nestfab/re')
from an2 import *
from capstone.x86 import X86_OP_MEM, X86_REG_RIP

VTSET = {}
for c, v in VT.items():
    VTSET.setdefault(v['vtable_rva'] + 0x10, c)   # slot0 address = vtable_rva+0x10
    VTSET.setdefault(v['vtable_rva'], c)

def ctors(rs):
    for r in rs:
        p = PROF.get(r, {})
        found = []
        for ins in disasm(r):
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    t = ins.address + ins.size + op.mem.disp
                    if t in VTSET:
                        found.append((ins.address, hex(t), VTSET[t]))
        print('%08X size=%-6s -> %s' % (r, p.get('size'), found))

if __name__ == '__main__':
    ctors([int(a, 16) for a in sys.argv[1:]])
