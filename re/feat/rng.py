import sys
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
lo, hi = int(sys.argv[1], 0), int(sys.argv[2], 0)
for r in sorted(STRS):
    if lo <= r < hi:
        print('0x%06X  %s' % (r, STRS[r]))
