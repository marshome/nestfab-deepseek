import sys, re
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
pat = re.compile(sys.argv[1])
for L in open(REDIR + r'\feat\out_dis.txt', encoding='utf-8', errors='replace'):
    L = ''.join(c if 32 <= ord(c) < 127 else '.' for c in L).rstrip()
    if pat.search(L):
        print(L)
