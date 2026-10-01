import sys, re
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
pats = sys.argv[1:]
for r in sorted(STRS):
    s = STRS[r]
    for p in pats:
        if re.search(p, s):
            print('0x%06X  %s' % (r, s[:120]))
            break
