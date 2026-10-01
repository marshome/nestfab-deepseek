import sys
sys.path.insert(0, 'D:/Nesting/nestfab/re')
from an2 import *

def S(r, n=20):
    p = PROF.get(r, {})
    print('%08X size=%-6d class=%s' % (r, int(p.get('size', 0)), cls_of(r)))
    out = []
    for x in (F2S.get(r) or []):
        out.append(repr(x)[:70])
    print('   strs:', out[:n])

if __name__ == '__main__':
    for a in sys.argv[1:]:
        S(int(a, 16))
