import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import re

P = load_prof()
NAMES = {}
for rva, v in P.items():
    op = v.get('own_plain') or []
    if op:
        NAMES[rva] = op[0]

def nm(rva):
    """best-effort name for an rva (function start)"""
    if rva in NAMES:
        return NAMES[rva]
    v = P.get(rva)
    if v and v.get('name'):
        return v['name']
    o = owner(rva)
    if o is not None and o in NAMES:
        return NAMES[o] + '@' + hex(rva - o)
    return None

if __name__ == '__main__':
    pat = re.compile(sys.argv[1] if len(sys.argv) > 1 else '.', re.I)
    for rva in sorted(P):
        n = NAMES.get(rva)
        if n and pat.search(n):
            print(hex(rva), P[rva]['size'], P[rva]['nins'], n)
