"""Find pointer arrays (enum name tables) referencing a set of string RVAs."""
import sys, struct
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *

def find_tables(str_rvas):
    """scan for 8-byte little-endian values == rva or rva+IB"""
    want = {}
    for r in str_rvas:
        want[r] = 'S'
        want[r + IB] = 'V'
    hits = []
    for off in range(0, len(data) - 8, 8):
        v = struct.unpack_from('<Q', data, off)[0]
        if v in want:
            r = off2rva(off)
            if r is not None:
                hits.append((r, v - IB if v > IB else v, want[v]))
    # group consecutive
    groups = []
    for r, t, k in hits:
        if groups and r - groups[-1][-1][0] <= 8:
            groups[-1].append((r, t, k))
        else:
            groups.append([(r, t, k)])
    out = []
    for g in groups:
        if len(g) >= 3:
            out.append(g)
    return out

if __name__ == '__main__':
    rs = [int(a, 0) for a in sys.argv[1:]]
    for g in find_tables(rs):
        print('TABLE @ 0x%X  (%d entries)' % (g[0][0], len(g)))
        for r, t, k in g:
            print('   0x%X -> 0x%X %s' % (r, t, STRS.get(t, '?')[:60]))
