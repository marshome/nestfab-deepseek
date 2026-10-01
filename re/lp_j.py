import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import collections, json
vt = json.load(open(REDIR + r'\vtables.json'))
VTS = {v['vtable_rva']: (v.get('demangled') or k) for k,v in vt.items()}
P = load_prof()
c = collections.Counter()
for f, v in P.items():
    for dr in v['data_refs']:
        c[dr] += 1
print('distinct data_refs', len(c))
for dr,n in c.most_common(10):
    print(hex(dr), n)
allrefs = set(c)
print('vtable rvas present as data_refs:', sum(1 for t in VTS if t in allrefs))
print('sample intersection:', [hex(t) for t in list(VTS)[:5]], [t in allrefs for t in list(VTS)[:5]])
# maybe data_refs are already-normalized but stored as constants; print profile of 0x656340 again
print(P[0x656340]['data_refs'])
