import sys, json
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *

EX = json.load(open(REDIR + r'\exports_named.json'))
FNAME = {}
for e in EX:
    if e['name']:
        FNAME.setdefault(e['rva'], set()).add(e['name'].rstrip('?'))
P = load_prof()
for r, f in P.items():
    if f.get('name'):
        FNAME.setdefault(r, set()).add(f['name'].rstrip('?'))

def find(refs):
    """functions whose data_refs or rip targets include any of refs"""
    out = {}
    for r, f in P.items():
        dr = set(f.get('data_refs') or [])
        hit = dr & refs
        if hit:
            out[r] = hit
    return out

def by_str(sub):
    rs = {r for r, s in STRS.items() if sub in s}
    print('## strings matching %r: %s' % (sub, ['0x%X:%s' % (r, STRS[r][:60]) for r in sorted(rs)]))
    for r, hit in sorted(find(rs).items()):
        print('   ref by 0x%X %s  via %s' % (r, sorted(FNAME.get(r, [])), ['0x%X' % h for h in sorted(hit)]))

def by_rva(rva):
    rs = {rva}
    print('## 0x%X = %r' % (rva, STRS.get(rva)))
    for r, hit in sorted(find(rs).items()):
        print('   ref by 0x%X %s' % (r, sorted(FNAME.get(r, []))))

if __name__ == '__main__':
    for a in sys.argv[1:]:
        if a.startswith('0x') or a.isdigit():
            by_rva(int(a, 0))
        else:
            by_str(a)
