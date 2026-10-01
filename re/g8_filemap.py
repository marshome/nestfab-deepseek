import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from g1_names import NAMES
from g3_dis import P
import re, collections

# group printable runs containing a source-file-ish suffix by owning function
pat = re.compile(rb'[ -~]{6,}')
byfile = collections.defaultdict(set)
for m in pat.finditer(data):
    s = m.group().decode('latin1')
    if not re.search(r'\.(cpp|hpp|inl|h|c|cc)', s):
        continue
    r = off2rva(m.start())
    o = owner(r)
    if o is None:
        continue
    byfile[s].add(o)

if __name__ == '__main__':
    key = sys.argv[1] if len(sys.argv) > 1 else ''
    for s in sorted(byfile):
        if key and key not in s:
            continue
        print('%-45r %s' % (s, ' '.join('%x(%d,%s)' % (f, P.get(f, {}).get('size', 0), NAMES.get(f) or P.get(f, {}).get('name') or '') for f in sorted(byfile[s]))))
