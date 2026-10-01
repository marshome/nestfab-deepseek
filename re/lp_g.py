import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import pickle, collections, json
P = load_prof()
vt = json.load(open(REDIR + r'\vtables.json'))
# reverse index: data_ref -> list of functions
dref = collections.defaultdict(list)
for f, v in P.items():
    for dr in v['data_refs']:
        dref[dr].append(f)

interesting = {0xa3ada0:'Lp::LinearProgram',0xa3aed0:'Prc::PriceComputer',0xa3b0b0:'Prc::BoxPriceComputer',
 0xa3b0f0:'Prc::HullPriceComputer',0xa3b130:'Prc::AlphaPriceComputer',0xa3b170:'Prc::LinearCombinationPricer',
 0xa3b1b0:'Row::BasicDistancer',0xa3b1e0:'Row::Squeezer',0xa3b270:'Coin::CoinLP'}
for a,name in interesting.items():
    print('===', name, hex(a))
    for f in sorted(dref.get(a,[])):
        v=P[f]
        print('    %08X size=%-6d name=%s  callers=%s' % (f, v['size'], v['name'], ' '.join('%X'%c for c in v['callers'][:8])))
