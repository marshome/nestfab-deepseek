"""Is the LP / pricing machinery actually reachable from the nesting engine?
   Find the vtables for Lp::/Prc::/Row::/Coin::, then their virtual slot functions,
   then who calls those slots (directly or via vtable)."""
import sys, json, collections, struct
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

prof = load_prof()
vt = json.load(open(r"D:\Nesting\nestfab\re\vtables.json"))
rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json", encoding='utf-8'))
name_of = {r['rva']: (r['name'] or '') for r in rows}

WANT = ('Lp::', 'Prc::', 'Row::', 'Coin::', 'Clp::', 'CoinUtils')
targets = {k: v for k, v in vt.items() if v['demangled'].startswith(WANT)}
print("vtables of interest: %d" % len(targets))
for k, v in sorted(targets.items(), key=lambda kv: kv[1]['demangled']):
    print("  %-40s vtable=%s slots=%d" % (v['demangled'], v['vtable_rva'] and hex(v['vtable_rva']), len(v['slots'])))

slots = set()
for v in targets.values(): slots.update(v['slots'])
print("\nunique slot functions: %d" % len(slots))

# who calls any of these?
callers = collections.defaultdict(set)
for b, p in prof.items():
    for c in p.get('callees', []):
        if c in slots: callers[c].add(b)
print("\nslot -> direct callers (non-trivial ones):")
found_any = False
for s in sorted(slots):
    cs = callers.get(s)
    if cs:
        found_any = True
        print("   slot %08X  <- %s" % (s, ', '.join('%08X' % c for c in sorted(cs)[:6])))
if not found_any:
    print("   (no direct callers found)")

# also: do any functions mention the class name strings (RTTI use / dynamic_cast)?
print("\nfunctions referencing typeinfo-name strings of these classes:")
for k, v in sorted(targets.items()):
    nm = k
    hits = []
    for b, p in prof.items():
        if any(s == v['demangled'] for _, s in p.get('strings', [])): hits.append(b)
    if hits: print("   %-40s <- %s" % (v['demangled'], ', '.join('%08X' % h for h in hits[:6])))

# Are these classes instantiated at all? look for vtable address-point references in code
print("\ncode references to the vtable address points (instantiation evidence):")
for k, v in sorted(targets.items(), key=lambda kv: kv[1]['demangled']):
    vr = v['vtable_rva']
    if not vr: continue
    ap = vr + 16
    refs = []
    for b, p in prof.items():
        for t in p.get('data_refs', []):
            if t == ap: refs.append(b)
    if refs: print("   %-40s addr-point %08X <- %s" % (v['demangled'], ap, ', '.join('%08X' % r for r in refs[:6])))
