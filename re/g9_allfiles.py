import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from g1_names import NAMES
from g5_inline import inline_strings
import collections, re

P = load_prof()
byfile = collections.defaultdict(set)
names = collections.defaultdict(set)
for i, rva in enumerate(sorted(P)):
    P_ = P[rva]
    if P_['size'] < 40:
        continue
    try:
        ss = inline_strings(rva)
    except Exception:
        continue
    for a, s in ss:
        if re.search(r'\.(cpp|hpp|inl|h|c|cc)$', s):
            byfile[s].add(rva)
        elif len(s) >= 6 and re.match(r'^[A-Za-z_:~][A-Za-z0-9_:~<>]*$', s):
            names[rva].add(s)
    if i % 2000 == 0:
        print('progress', i, file=sys.stderr)

with open(r'D:\Nesting\nestfab\re\out_g_filemap2.txt', 'w', encoding='utf-8') as f:
    for s in sorted(byfile):
        f.write('%-50r %s\n' % (s, ' '.join('%x(%d,%s)' % (x, P.get(x, {}).get('size', 0), NAMES.get(x) or P.get(x, {}).get('name') or '') for x in sorted(byfile[s]))))
    f.write('\n\n==== identifiers per function (probable __func__) ====\n')
    for x in sorted(names):
        f.write('%x %s :: %s\n' % (x, NAMES.get(x) or P.get(x, {}).get('name') or '', ' | '.join(sorted(names[x]))))
print('done')
