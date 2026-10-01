import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from g1_names import NAMES
from g3_dis import label_fn
from g3_dis import P
import re

# reconstruct inline-built string literals: find printable runs in code and
# report which function contains them
def scan_paths():
    out = {}
    pat = re.compile(rb'[ -~]{6,}')
    for m in pat.finditer(data):
        s = m.group().decode('latin1')
        if re.search(r'\.(cpp|hpp|h|c|cc)', s):
            r = off2rva(m.start())
            o = owner(r)
            out.setdefault(o, []).append((r, s))
    return out

if __name__ == '__main__':
    for o, lst in sorted((k, v) for k, v in scan_paths().items() if k is not None):
        print(hex(o), NAMES.get(o) or P.get(o, {}).get('name'))
        for r, s in lst:
            print('     ', hex(r), repr(s))
