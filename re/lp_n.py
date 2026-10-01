import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import collections, json, struct, re
vt = json.load(open(REDIR + r'\vtables.json'))
P = load_prof()
# collect all "stored qword" that equal IB+rva for any vtable label... too slow; use direct substring search on all rvas
VTS = sorted(v['vtable_rva'] for v in vt.values())
allrefs = set()
for f,v in P.items():
    allrefs.update(v['data_refs'])
ref = [t for t in VTS if t in allrefs]
print('vtables referenced via data_refs: %d / %d' % (len(ref), len(VTS)))
# show distribution by vtable rva ranges and which classes are NOT referenced
notref = [ (t, vt_by) for t in VTS]
by = {v['vtable_rva']:(v.get('demangled') or k) for k,v in vt.items()}
nref = [t for t in VTS if t not in allrefs]
print('sample NOT referenced:', [(hex(t), by[t]) for t in nref[:20]])
print('sample referenced   :', [(hex(t), by[t]) for t in ref[:20]])
