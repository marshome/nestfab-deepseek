"""Climb the caller graph from the LP/pricing constructors to see what actually reaches them."""
import sys, json, collections, pickle, os
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

CACHE = r"D:\Nesting\nestfab\re\callers.pkl"
if os.path.exists(CACHE):
    callers = pickle.load(open(CACHE, 'rb'))
    print("loaded cached call graph")
else:
    callers = collections.defaultdict(set)
    for nm_, va, vs, pr, rs, ch in SEC:
        if not (ch & 0x20000000): continue
        for ins in MD.disasm(data[pr:pr+rs], va):
            if ins.mnemonic == 'call' and ins.operands and ins.operands[0].type == X86_OP_IMM:
                t = ins.operands[0].imm
                if t:
                    callers[t].add(owner(ins.address) or ins.address)
    callers = dict(callers)
    pickle.dump(callers, open(CACHE, 'wb'))
    print("built call graph: %d targets" % len(callers))

prof = load_prof()
rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json", encoding='utf-8'))
name_of = {r['rva']: (r['name'] or '') for r in rows}
exp = set(name_of)
def nm(x): return name_of.get(x) or prof.get(x, {}).get('name') or ''
def desc(x):
    p = prof.get(x, {})
    ss = [s for _, s in p.get('strings', [])][:3]
    return "%08X %-6s %-26s %s" % (x, p.get('size', ''), nm(x), ss)

def climb(start, maxdepth=6, maxpaths=8):
    print("\n" + "="*100)
    print("CLIMB from %08X (%s)" % (start, nm(start) or '?'))
    seen = set(); paths = []
    def rec(node, path, depth):
        if len(paths) >= maxpaths or depth > maxdepth: return
        cs = sorted(x for x in callers.get(node, ()) if x != node)
        if not cs:
            paths.append(path + ['(no callers)']); return
        for c in cs:
            tag = 'EXPORT' if c in exp else ''
            newpath = path + ['%08X %s %s' % (c, nm(c), tag)]
            if c in exp or not callers.get(c):
                paths.append(newpath)
            elif c not in seen:
                seen.add(c); rec(c, newpath, depth + 1)
    rec(start, [], 0)
    for p in paths:
        print("   " + '\n     -> '.join(p))

for s in (0x4D64C0, 0x267730, 0x136B80, 0x136B20):
    climb(s)

print("\n" + "="*100); print("DESCRIPTIONS"); print("="*100)
for x in (0x4D64C0, 0x4D84D0, 0x267730, 0x267760, 0x136AE0, 0x136B20, 0x136B80, 0x4D9AD0):
    print("   " + desc(x))
