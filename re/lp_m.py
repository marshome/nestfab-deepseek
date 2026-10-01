import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
# who references the typeinfo objects themselves (they must be loaded for __cxa_throw)
import collections
P = load_prof()
ti = {0xa17d60:'ti Box',0xa17d80:'ti Hull',0xa17da0:'ti Alpha',0xa17dc0:'ti LinComb',
      0xa17de0:'ti BasicDistancer',0xa17e00:'ti Squeezer',0xa17ea0:'ti CoinLP',
      0xa17d40:'ti LinearProgram',0xa17d50:'ti PriceComputer',0xa17e20:'ti Row::Distancer'}
for f,v in P.items():
    for dr in v['data_refs']:
        if dr in ti:
            print('%08X size=%-6d -> %s  callers=%s' % (f, v['size'], ti[dr], ' '.join('%X'%c for c in v['callers'][:6])))
# also raw qword search for absolute va of ti
import struct, re
for r in ti:
    p8 = struct.pack('<Q', r+IB)
    o=[m.start() for m in re.finditer(re.escape(p8), data)]
    print(hex(r), ti[r], 'qword hits', len(o), [hex(off2rva(x)) for x in o[:6]])
