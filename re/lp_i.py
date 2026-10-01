import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import collections, json
vt = json.load(open(REDIR + r'\vtables.json'))
VTS = {v['vtable_rva']: (v.get('demangled') or k) for k,v in vt.items()}
P = load_prof()
hits = collections.defaultdict(set)
for f, v in P.items():
    for dr in v['data_refs']:
        if dr in VTS:
            hits[dr].add(f)
print('total vtables', len(VTS), 'referenced via data_refs:', len(hits))
for t,name in sorted(VTS.items()):
    if name.startswith(('Prc::','Row::','Lp::','Coin::')):
        print('  %-40s %08X refs=%d' % (name, t, len(hits.get(t,()))))
        for f in sorted(hits.get(t,())):
            vv=P[f]
            print('       %08X size=%-6d callers=%s' % (f, vv['size'], ' '.join('%X'%c for c in vv['callers'][:8])))
