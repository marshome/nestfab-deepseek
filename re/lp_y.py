import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import json
vt = json.load(open(REDIR + r'\vtables.json'))
for k, v in vt.items():
    d = v.get('demangled') or k
    if 'ClpSimplex' == d.split('<')[0].split('::')[-1] or d in ('ClpSimplex',) or d.endswith('ClpSimplex'):
        print(k, hex(v['vtable_rva']), d, len(v['slots']))
        print('   slot offsets of interest:')
        base = v['vtable_rva']
        for i, f in enumerate(v['slots']):
            if i * 8 + 0x10 in (0x228, 0x230, 0x248, 0x240):
                print('     +%X -> %08X' % (i * 8 + 0x10, f))
