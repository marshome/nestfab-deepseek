import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import pickle, collections
P = load_prof()

def show(rva, tag=''):
    v = P.get(rva)
    if v is None:
        print('  %08X  <no profile>' % rva); return
    print('  %08X %-30s size=%-6d nins=%-5d calls=%-4d callees=%-4d callers=%-4d' % (
        rva, (v.get('name') or '')[:30], v['size'], v['nins'], len(v['calls']), len(v['callees']), len(v['callers'])))
    if v['strings']:
        print('       strings:', [s for s in v['strings'][:8]])
    print('       callees:', ' '.join('%X' % c for c in v['callees']))
    print('       callers:', ' '.join('%X' % c for c in v['callers']))
    print('       data_refs:', ' '.join('%X' % c for c in v['data_refs'][:12]))

targets = {
 'Lp::LinearProgram vtable 0xa3ada0': [0x656340,0x656310,0x861a20,0x7c4c70,0x7c4cf0,0x7c4cc0,0x7c4d50,0x7c4dd0],
 'Lp::PriceComputer vtable 0xa3aed0': [0x656420,0x6563f0,0x861a20,0x7c4c70,0x7c4cf0,0x7c4f90,0x7c4fe0,0x7c50e0],
 'Prc::BoxPriceComputer 0xa3b0b0': [0x678d40,0x678d30,0x7c9d90,0x7ca100,0x7ca0d0],
 'Prc::HullPriceComputer 0xa3b0f0': [0x678d60,0x678d50,0x7ca130,0x7ca170,0x7ca140],
 'Prc::AlphaPriceComputer 0xa3b130': [0x678d80,0x678d70,0x7ca1b0,0x7ca200,0x7ca1c0],
 'Prc::LinearCombinationPricer 0xa3b170': [0x678df0,0x678d90,0x7ca370,0x7ca6c0,0x7ca5c0],
 'Row::BasicDistancer 0xa3b1b0': [0x679060,0x679050,0x7ca810],
 'Row::Squeezer 0xa3b1e0': [0x138be0,0x138ca0,0x13a360],
 'Coin::CoinLP 0xa3b270': [0x679e70,0x679db0,0x679c20,0x679660,0x6792c0,0x679670,0x679940,0x679420,0x679d00,0x7cb700,0x7cb710,0x7cb740,0x7cb720],
}
for cls, fl in targets.items():
    print('#'*70); print('##', cls)
    for f in fl:
        show(f)
