import sys, re
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
pat = re.compile(sys.argv[1])
n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
lines = [''.join(c if 32 <= ord(c) < 127 else '.' for c in L).rstrip()
         for L in open(REDIR + r'\feat\out_dis.txt', encoding='utf-8', errors='replace')]
for i, L in enumerate(lines):
    if pat.search(L):
        for j in range(i, min(i + n, len(lines))):
            print(lines[j])
        print('   ---')
