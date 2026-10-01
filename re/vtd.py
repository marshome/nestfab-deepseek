"""Proper vtable dumper: vtables.json vtable_rva is the vtable START (slot0),
slots[] are the virtual function entries.  Also print RTTI name from the
preceding qword (typeinfo pointer) if resolvable."""
import sys, json, collections, struct
sys.path.insert(0, 'D:/Nesting/nestfab/re')
from an2 import *

def dump_vt(start, label=''):
    print('==== %s vtable@%08X (typeinfo qword = %016X)' % (label, start, u64(rva2off(start))))
    slots = []
    a = start
    i = 0
    while True:
        o = rva2off(a)
        if o is None: break
        v = u64(o)
        t = norm(v)
        if t is None or t not in PROF:
            if v == 0 or t is None:
                pass
            print('  %2d %08X: %016X (non-func)' % (i, a, v))
            break
        p = PROF[t]
        print('  %2d %08X: %08X  size=%-6d name=%-22s %s' % (i, a, t, int(p['size']), str(p.get('name')), (F2S.get(t) or [])[:2]))
        slots.append(t)
        a += 8
        i += 1
        if i > 40: break
    return slots

if __name__ == '__main__':
    for x in sys.argv[1:]:
        dump_vt(int(x, 16), '')
