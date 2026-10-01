import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import struct, collections

def fn_info(rva):
    ext = func_extent(rva)
    strs = strings_of(rva)
    return ext, strs

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
    print('#'*70)
    print('##', cls)
    for f in fl:
        ext = func_extent(f)
        try:
            sf = strings_of(f)
        except Exception as e:
            sf = []
        nm = ''
        for r,s in sf:
            if s == (STRS.get(r) or ''):
                pass
        idents = [s for r,s in sf if s and all(c.isalnum() or c in '_:~<> ' for c in s) and len(s) < 70]
        print('  %08X  size %-6s  strs: %s' % (f, (ext[1]-ext[0]) if ext else '?', ' | '.join(repr(x) for x in idents[:8])))
