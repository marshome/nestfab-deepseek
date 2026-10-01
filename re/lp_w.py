import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import re, collections
pat = re.compile(r'rprice|price_computer|squeez|distanc|dim_alpha|boost_alpha|surface|column|dantzig|\bpric', re.I)
cands = {r: s for r, s in STRS.items() if pat.search(s)}
for r, s in sorted(cands.items()):
    print('%08X %r' % (r, s[:100]))
print('count', len(cands))
# find referrers
refs = collections.defaultdict(list)
for b, e, u in FUNCS:
    o = rva2off(b)
    if o is None: continue
    for ins in MD.disasm(data[o:o + (e - b)], b):
        for op in ins.operands:
            if op.type == 3 and op.mem.base == 41:
                t = ins.address + ins.size + op.mem.disp
                if t in cands:
                    refs[t].append(b)
print('--- referrers')
for r, s in sorted(refs.items()):
    print('%08X %r -> %s' % (r, STRS[r][:70], ' '.join('%X' % f for f in sorted(set(refs[r])))))
