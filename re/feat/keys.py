"""Print a condensed view: for each string reference in out_dis.txt show the
surrounding field accesses (mov/lea with [reg+disp]) """
import sys, re
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *

lines = open(REDIR + r'\feat\out_dis.txt', encoding='utf-8', errors='replace').read().split('\n')
lines = [''.join(c if 32 <= ord(c) < 127 else '.' for c in L) for L in lines]
out = []
import builtins
_pr = builtins.print
def print(*a, **k):
    out.append(' '.join(str(x) for x in a))

KEYS = set()
for r, s in STRS.items():
    if 0x9DA300 <= r < 0x9DB010:
        KEYS.add(s)

cur = None
for i, L in enumerate(lines):
    m = re.search(r'STR:"([^"]*)"', L)
    if m and m.group(1) in KEYS:
        print('---- %s' % L.strip()[:160])
        for j in range(i + 1, min(i + 12, len(lines))):
            print('     ' + lines[j].strip()[:150])
open(REDIR + r'\feat\out_keys.txt', 'w').write('\n'.join(out))
