import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import pickle, json, collections

P = load_prof()

def nm(rva):
    v = P.get(rva)
    return v.get('name') if v else None

if __name__ == '__main__':
    import re
    pat = re.compile(sys.argv[1] if len(sys.argv) > 1 else '.', re.I)
    for rva in sorted(P):
        n = P[rva].get('name') or ''
        if pat.search(n):
            print(hex(rva), P[rva]['size'], P[rva]['nins'], n)
