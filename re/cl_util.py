"""Shared analysis helpers for the cloud/licensing task."""
import sys, json, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
import libfix
from lib import *

PROF = load_prof()

def nm(rva):
    p = PROF.get(rva)
    return p.get('name') if p else None

def name_of(rva):
    o = owner(rva)
    return (o, nm(o)) if o else (None, None)

# string-rva -> [func rvas]
S2F = collections.defaultdict(set)
for _r, _p in PROF.items():
    for _sr, _s in _p.get('strings', []):
        S2F[_sr].add(_r)

def find_str(sub, exact=False):
    return [(r, s) for r, s in sorted(STRS.items())
            if (s == sub if exact else sub in s)]

def refs(sub, cap=60):
    out = []
    for r, s in find_str(sub):
        for f in sorted(S2F.get(r, ())):
            out.append((f, nm(f), r, s))
    seen = set(); res = []
    for f, n, r, s in out:
        if (f, r) in seen: continue
        seen.add((f, r)); res.append((f, n, r, s))
    return res[:cap]

def show_refs(sub, cap=60):
    print(f"### refs to {sub!r}")
    for f, n, r, s in refs(sub, cap):
        print(f"   fn {hex(f):>8s} {str(n):34s} str {hex(r)} {s[:90]!r}")

def strings(rva, maxn=200):
    p = PROF.get(owner(rva))
    if not p: return []
    return p.get('strings', [])[:maxn]

def callers(rva):
    p = PROF.get(owner(rva))
    return p.get('callers') if p else None

def callees(rva):
    p = PROF.get(owner(rva))
    return p.get('callees') if p else None

def callgraph_up(rva, depth=3, seen=None):
    """list of (depth, func, name) callers transitively"""
    if seen is None: seen = set()
    out = []
    p = PROF.get(owner(rva))
    if not p: return out
    for c in (p.get('callers') or []):
        o = owner(c) or c
        if o in seen: continue
        seen.add(o)
        out.append((depth, o, nm(o)))
        if depth > 0:
            out += callgraph_up(o, depth - 1, seen)
    return out

EXPORT_RVAS = sorted(EXPORTS.keys())
def exp_ord(rva):
    return EXPORTS.get(rva)

def all_exports_named():
    return [(r, EXPORTS[r], nm(r)) for r in EXPORT_RVAS]

def dump_dis(rva, n=60, start=None):
    cnt = 0
    for ins in disasm(rva):
        if start and ins.address < start: continue
        tgt = ''
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                a = ins.address + ins.size + op.mem.disp
                if a in STRS: tgt = '   ; "%s"' % STRS[a][:80]
                else: tgt = '   ; -> %#x' % a
        print(f"  {ins.address:#08x}  {ins.mnemonic:8s} {ins.op_str}{tgt}")
        cnt += 1
        if cnt >= n: break

def who_refs_addr(a):
    """functions with data_refs containing a"""
    return sorted(r for r, p in PROF.items() if a in (p.get('data_refs') or []))
