import sys, json, collections, struct
sys.path.insert(0, 'D:/Nesting/nestfab/re')
from an import *

# build string -> funcs index (normalised)
S2F = collections.defaultdict(set)
F2S = {}
for r, p in PROF.items():
    ss = p.get('strings') or []
    out = []
    for s in ss:
        if isinstance(s, str):
            out.append(s)
        else:
            for x in s:
                out.append(x)
    F2S[r] = out
    for s in out:
        S2F[s].add(r)

def who(s, exact=True):
    """funcs whose recovered __func__ string matches"""
    res = set()
    for k, fs in S2F.items():
        if (k == s) if exact else (isinstance(k, str) and s in k):
            res |= fs
    return sorted(res)

def cls_of(rva):
    """class whose vtable contains rva as a slot"""
    out = []
    for c, v in VT.items():
        if rva in v['slots']:
            out.append((c, v['slots'].index(rva), v['vtable_rva']))
    return out

def nm(rva):
    p = PROF.get(rva, {})
    return p.get('name')

def show(rva, n=60):
    print('=== %08X  name=%s  size=%s  class=%s' % (rva, nm(rva), PROF.get(rva,{}).get('size'), cls_of(rva)))
    ss = F2S.get(rva, [])
    if ss: print('   strings:', ss[:14])
    for ins in disasm(rva, count=n):
        print('  %08X  %-26s %s' % (ins.address, ins.mnemonic, ins.op_str))
