import sys, json, collections, struct
sys.path.insert(0, 'D:/Nesting/nestfab/re')
from an2 import *

# dump the vtable metadata region as qwords
def dumpq(rva, n=64, label=''):
    print('--- %s @ %08X' % (label, rva))
    o = rva2off(rva)
    for i in range(n):
        v = u64(o + i * 8)
        t = norm(v)
        cls = ''
        if t:
            for c, vv in VT.items():
                if vv['vtable_rva'] == t:
                    cls = 'VT:' + c
            if t in PROF:
                cls += ' fn:' + str(PROF[t].get('name'))
        print('  %08X: %016X  rva=%s %s' % (rva + i * 8, v, hex(t) if t else '-', cls))

if __name__ == '__main__':
    a = sys.argv[1:]
    dumpq(int(a[0], 16), int(a[1]) if len(a) > 1 else 32, a[2] if len(a) > 2 else '')
