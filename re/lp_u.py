import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
P = load_prof()
# find all functions whose callees/strings reference the LP/Prc/Row families' key sites
targets = [0x7CA200, 0x7C9D90, 0x7CA370, 0x7CA6C0, 0x7CA5C0, 0x13A360, 0x138BE0, 0x138CA0,
           0x6792C0, 0x679670, 0x679940, 0x679420, 0x679D00, 0x7CA830, 0x4D96F0, 0x910BA0]
for t in targets:
    v = P.get(t, {})
    print('=== %08X size=%s' % (t, v.get('size')))
    print('   callers:', ' '.join('%X' % c for c in v.get('callers', [])[:20]))
# who CALLS the virtual slots (0x7c4c70 etc) -- indirect, so look for funcs referencing vtable? none.
# Instead: find functions that mention 'price_computer' or 'rprice' or 'row' strings
import re
for f, v in P.items():
    for s in v.get('strings', []):
        if isinstance(s, str) and re.search(r'rprice|price_computer|row_|squeez|distanc|dim_alpha|boost_alpha|surface', s, re.I):
            print('%08X %-40s %r' % (f, (v.get('name') or '')[:40], s))
