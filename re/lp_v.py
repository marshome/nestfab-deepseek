import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import re
P = load_prof()
pat = re.compile(r'rprice|price_computer|row_|squeez|distanc|dim_alpha|boost_alpha|surface|column|dantzig|pric', re.I)
seen = 0
for f, v in sorted(P.items()):
    for s in v.get('strings', []):
        if isinstance(s, str) and pat.search(s):
            print('%08X %-34s %r' % (f, (v.get('name') or '')[:34], s))
            seen += 1
print('total', seen)
