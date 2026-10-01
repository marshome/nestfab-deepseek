import sys
sys.path.insert(0, 'D:/Nesting/nestfab/re')
from an2 import *

def D(r, n=200, base=None):
    p = PROF.get(r, {})
    print('===== %08X  size=%d  class=%s  strings=%s' % (r, int(p.get('size', 0)), cls_of(r), (F2S.get(r) or [])[:8]))
    for ins in disasm(r, count=n):
        print('  %08X  %-24s %s' % (ins.address, ins.mnemonic, ins.op_str))

if __name__ == '__main__':
    import sys as _s
    args = _s.argv[1:]
    r = int(args[0], 16)
    n = int(args[1]) if len(args) > 1 else 200
    D(r, n)
