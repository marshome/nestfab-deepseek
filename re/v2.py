import sys, json, collections
sys.path.insert(0, 'D:/Nesting/nestfab/re')
from an2 import *

pat = sys.argv[1] if len(sys.argv) > 1 else ''
for c in sorted(VT):
    if pat and pat.lower() not in c.lower():
        continue
    v = VT[c]
    print('%-46s vtable=%08X nslots=%d' % (c, v['vtable_rva'], len(v['slots'])))
    for i, s in enumerate(v['slots']):
        p = PROF.get(s, {})
        print('    %2d %08X size=%-6s %s' % (i, s, p.get('size'), (F2S.get(s) or [])[:2]))
