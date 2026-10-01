import sys
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *

lo, hi = 0x9AA000, 0x9B0000
lines = []
for r in sorted(STRS):
    if lo <= r < hi:
        lines.append('0x%06X  %s' % (r, STRS[r]))
open(REDIR + r'\feat\out_rodata.txt', 'w').write('\n'.join(lines))
print(len(lines))
