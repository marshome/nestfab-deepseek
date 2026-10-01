import sys, collections
sys.path.insert(0, 'D:/Nesting/nestfab/re')
from an3 import *

targets = set(range(0xa3ce00, 0xa3d100, 8))
# try absolute-address form
for base in (IB, 0):
    tg = set(t + base for t in targets)
    hits = collections.defaultdict(list)
    for i in range(0, len(data) - 8):
        v = u64(i)
        if v in tg:
            hits[v - base].append(i)
    print('base', hex(base), 'nhits', sum(len(v) for v in hits.values()))
    for k in sorted(hits):
        offs = hits[k]
        info = []
        for o in offs[:8]:
            r = off2rva(o)
            ow = owner(r) if r else None
            info.append((hex(o), hex(r) if r else None, hex(ow) if ow else None))
        print('  ', hex(k), 'n=', len(offs), info)
