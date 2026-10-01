import sys, re
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
lo, hi = int(sys.argv[1], 0), int(sys.argv[2], 0)
for L in open(REDIR + r'\feat\out_dis.txt', encoding='utf-8', errors='replace'):
    L = ''.join(c if 32 <= ord(c) < 127 else '.' for c in L).rstrip()
    m = re.match(r'\s*([0-9A-F]{6})\s', L)
    if m:
        a = int(m.group(1), 16)
        if lo <= a < hi:
            print(L)
