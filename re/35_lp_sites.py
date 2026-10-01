"""Where are the LP/pricing classes instantiated, and what calls those sites?"""
import sys, json, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

prof = load_prof()
rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json", encoding='utf-8'))
name_of = {r['rva']: (r['name'] or '') for r in rows}
vt = json.load(open(r"D:\Nesting\nestfab\re\vtables.json"))

sites = [0x267760, 0x679DB0, 0x679E70, 0x4D9B30, 0x7CA1C0, 0x4D9AD0, 0x7CA0D0,
         0x4D9B00, 0x7CA140, 0x4D9CD0, 0x4D9DE0, 0x4D9F80, 0x678D90, 0x678DF0,
         0x7CA5C0, 0x136AE0, 0x138A20, 0x138BE0, 0x138CA0, 0x138D60]

print("="*100); print("ENCLOSING FUNCTIONS OF LP/PRICING INSTANTIATION SITES"); print("="*100)
enc = {}
for s in sites:
    o = owner(s)
    enc.setdefault(o, []).append(s)
for o, ss in sorted(enc.items(), key=lambda kv: (kv[0] is None, kv[0])):
    p = prof.get(o, {})
    print("\n  fn %s  size=%-6s  sites=%s" % ('%08X' % o if o else 'None', p.get('size'), ['%X' % x for x in ss]))
    print("     name=%s strings=%s" % (name_of.get(o) or p.get('name'), [x for _, x in p.get('strings', [])][:6]))
    print("     callers=%s" % ', '.join(('%08X' % c) + ('(' + (name_of.get(c) or prof.get(c, {}).get('name') or '') + ')') for c in p.get('callers', [])[:8]))

print("\n" + "="*100); print("CALLERS OF THE ENCLOSING FUNCTIONS (2 levels up)"); print("="*100)
level1 = set(enc)
level2 = collections.Counter()
for o in level1:
    for c in prof.get(o, {}).get('callers', []):
        level2[c] += 1
for c, n in level2.most_common(40):
    p = prof.get(c, {})
    print("   %08X  x%-3d size=%-6s name=%-28s strings=%s" % (
        c, n, p.get('size'), name_of.get(c) or p.get('name') or '',
        [x for _, x in p.get('strings', [])][:3]))
