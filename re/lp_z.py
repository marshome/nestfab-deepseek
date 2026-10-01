import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *

fams = [('Lp::LinearProgram vtable 0xa3ada0', 0xa3ada0),
        ('Prc::PriceComputer vtable 0xa3aed0', 0xa3aed0),
        ('Prc::BoxPriceComputer 0xa3b0b0', 0xa3b0b0),
        ('Prc::HullPriceComputer 0xa3b0f0', 0xa3b0f0),
        ('Prc::AlphaPriceComputer 0xa3b130', 0xa3b130),
        ('Prc::LinearCombinationPricer 0xa3b170', 0xa3b170),
        ('Row::BasicDistancer 0xa3b1b0', 0xa3b1b0),
        ('Row::Squeezer 0xa3b1e0', 0xa3b1e0),
        ('Coin::CoinLP 0xa3b270', 0xa3b270)]
for name, base in fams:
    print('=' * 78)
    print(name)
    i = 0
    p = base + 0x10
    end = base + 0x10 + 24 * 8
    while p < end:
        v = u64(p)
        if v == 0:
            break
        f = norm(v)
        ext = func_extent(f) if f else None
        # scan the whole file for another occurrence of the same label VA (shared slot => common base)
        import struct
        cnt = data.count(struct.pack('<Q', f + IB)) if f else 0
        strs = strings_of(f) if f else []
        ann = ' | '.join('%r' % s for _, s in strs[:3])
        print('  +%03X slot%2d  %08X  size=%-6s shared=%-3d %s' % (0x10 + i * 8, i, f, (ext[1] - ext[0]) if ext else '?', cnt, ann))
        i += 1
        p += 8
