"""Analysis helper: class/method index with names+strings."""
import sys, json, collections
sys.path.insert(0, 'D:/Nesting/nestfab/re')
from lib import *

VT = json.load(open('D:/Nesting/nestfab/re/vtables.json'))
PROF = load_prof()

def demangle(n):
    return n

def vt_of(cls):
    for k, v in VT.items():
        if k == cls:
            return v
    return None

def find_class(sub):
    return [k for k in VT if sub in k]

def info(rva):
    p = PROF.get(rva)
    if not p:
        return {'rva': hex(rva), 'name': None, 'strings': []}
    return {'rva': hex(rva), 'name': p.get('name'), 'size': int(p['size']),
            'strings': p.get('strings'), 'callees': [hex(c) for c in p['callees']],
            'ncall': len(p['calls'])}

def slots(cls, show=True):
    v = vt_of(cls)
    if not v:
        return None
    out = []
    for i, s in enumerate(v['slots']):
        p = PROF.get(s, {})
        nm = p.get('name')
        st = p.get('strings') or []
        out.append((i, s, nm, st))
        if show:
            print('%2d %08X %-32s %s' % (i, s, nm, st[:3]))
    return out

def dump(rva, count=200, show_bytes=False):
    for ins in disasm(rva, count=count):
        print('%08X  %-30s %s %s' % (ins.address, ins.mnemonic, ins.op_str, ''))
