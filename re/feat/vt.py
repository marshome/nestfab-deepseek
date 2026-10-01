import json, sys, re
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *

v = json.load(open(REDIR + r'\vtables.json'))

def demangle(k):
    # crude Itanium -> readable
    s = k
    s = re.sub(r'^N', '', s)
    return s

want = sys.argv[1:]
for k, d in sorted(v.items()):
    if not want or any(w in k for w in want):
        print('%-70s vtable=0x%X nslots=%d slots[:6]=%s' % (
            k, d['vtable_rva'], len(d['slots']),
            ','.join('0x%X' % x for x in d['slots'][:6])))
