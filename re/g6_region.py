import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from g1_names import NAMES
from g5_inline import inline_strings

lo = int(sys.argv[1], 16)
hi = int(sys.argv[2], 16)
P = load_prof()
for rva in sorted(P):
    if lo <= rva < hi:
        v = P[rva]
        ss = inline_strings(rva)
        # keep only plausible literals (path/assert-like)
        keep = [(a, s) for a, s in ss if len(s) >= 8]
        print('%x size=%d nins=%d ind=%d %s' % (rva, v['size'], v['nins'], v['ind'], NAMES.get(rva) or v.get('name') or ''))
        for a, s in keep:
            print('      %x %r' % (a, s))
