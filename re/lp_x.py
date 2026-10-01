import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import re, collections
want = ['AlphaSurfacePricer ', 'Pb pricing ', 'Prices: ', 'Grouper prices : ',
        'static_cast<long long>(pricer.m_prices[p]) >= 0', 'prices.size() == m_problem.GetNumberOfParts()',
        'CNS_SetSheetPrice', 'sheet_priority', 'multiplicity']
cands = {}
for r, s in STRS.items():
    for w in want:
        if w in s:
            cands[r] = s
            break
for r, s in sorted(cands.items()):
    print('%08X %r' % (r, s[:90]))
print('n=', len(cands))
refs = collections.defaultdict(set)
for b, e, u in FUNCS:
    o = rva2off(b)
    if o is None: continue
    for ins in MD.disasm(data[o:o + (e - b)], b):
        for op in ins.operands:
            if op.type == 3 and op.mem.base == 41:
                t = ins.address + ins.size + op.mem.disp
                if t in cands:
                    refs[t].add(b)
print('--- referrers')
P = load_prof()
for r in sorted(refs):
    print('%08X %r' % (r, STRS[r][:60]))
    for f in sorted(refs[r]):
        v = P.get(f, {})
        print('     %08X size=%-6s callers=%s' % (f, v.get('size'), ' '.join('%X' % c for c in v.get('callers', [])[:6])))
