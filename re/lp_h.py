import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import collections, time

targets = {0xa3ada0:'Lp::LinearProgram vt',0xa3aed0:'Prc::PriceComputer vt',0xa3b0b0:'Prc::BoxPriceComputer vt',
 0xa3b0f0:'Prc::HullPriceComputer vt',0xa3b130:'Prc::AlphaPriceComputer vt',0xa3b170:'Prc::LinearCombinationPricer vt',
 0xa3b1b0:'Row::BasicDistancer vt',0xa3b1e0:'Row::Squeezer vt',0xa3b270:'Coin::CoinLP vt'}
P = load_prof()
hits = collections.defaultdict(set)
t0=time.time()
n=0
for b,e,u in FUNCS:
    n+=1
    try:
        for t in rip_targets(b):
            if t in targets:
                hits[t].add(b)
    except Exception as ex:
        pass
print('scanned', n, 'funcs in %.1fs' % (time.time()-t0))
for t,name in targets.items():
    print('===', name, hex(t), len(hits[t]))
    for f in sorted(hits[t]):
        v=P.get(f,{})
        print('    ref in %08X size=%-6d name=%s callers=%s' % (f, v.get('size',-1), v.get('name'), ' '.join('%X'%c for c in v.get('callers',[])[:8])))
