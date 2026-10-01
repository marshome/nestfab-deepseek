import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import struct

def vtinfo(base, n=0x60):
    print('=== raw vtable @ %s' % hex(base))
    for i in range(0, n, 4):
        r = base + i
        v = u32(r)
        if v == 0:
            break
        nm = STRS.get(r + 4) or ''
        print('   +%02x' % i, hex(v), '->', hex(norm(v)) if norm(v) else '-', repr(nm[:80]))

for b in (0x656340, 0x656310, 0x861a20, 0x7c4c70, 0x7c4cf0, 0x7c4cc0, 0x7c4d50, 0x7c4dd0):
    vtinfo(b)
print()
# scan the whole rodata for vtable headers: a 4-byte value that is a valid vtable string pattern
# instead: find any offset whose preceding 4 bytes point to a string starting with N and containing our classes
for cls in ['Prc', 'Lp', 'Row', 'Coin']:
    print('#### search vtable-name strings matching', cls)
    for r, s in sorted(STRS.items()):
        if s.startswith('N') and cls in s and s.endswith('E') and len(s) < 60:
            pass
