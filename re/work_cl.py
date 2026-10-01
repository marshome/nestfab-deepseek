import sys, json, struct, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from cl_util import *

vt = json.load(open(r"D:\Nesting\nestfab\re\vtables.json"))
# map any interesting pointer -> class
ptr2cls = {}
for k, v in vt.items():
    if not k.startswith('N8CryptoPP'):
        continue
    va = v['vtable_rva']
    for off in (0, 8, 0x10):
        ptr2cls[va + off] = k

# functions (all) with data_refs pointing at these
hits = collections.defaultdict(list)
for r, p in PROF.items():
    for d in (p.get('data_refs') or []):
        if d in ptr2cls:
            hits[ptr2cls[d]].append((r, d))

print("=== CryptoPP classes whose vtable/typeinfo is referenced from APP code (<0x725000) ===")
app = collections.defaultdict(set)
for cls, lst in hits.items():
    for r, d in lst:
        if r < 0x725000:
            app[cls].add(r)
for cls in sorted(app):
    print(f"  {cls}")
    for r in sorted(app[cls])[:8]:
        print(f"       fn {r:#08x}  {nm(r)}")
print()
print("=== all CryptoPP classes referenced anywhere (count) ===")
for cls in sorted(hits, key=lambda c: -len(hits[c]))[:40]:
    print(f"  {len(hits[cls]):5d}  {cls}")
