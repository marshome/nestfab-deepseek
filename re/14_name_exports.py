import pickle, re, collections, json
D = pickle.load(open(r"D:\Nesting\nestfab\re\xref.pkl","rb"))
prof, funcs, exports, strs = D['prof'], D['funcs'], D['exports'], D['strs']

IDENT = re.compile(r'^[A-Za-z_~][A-Za-z0-9_]*(::[A-Za-z_~][A-Za-z0-9_]*)*$')
def identlike(s):
    if len(s)<3 or len(s)>90: return False
    if not IDENT.match(s): return False
    if s in ('basic_string','vector','string'): return False
    return True

# ---- name recovery per function ----
names = {}
for b,p in prof.items():
    ss = [s for r,s in p['strings']]
    plain = set(s for s in ss if identlike(s))
    comm  = set(s[2:].strip() for s in ss if s.startswith('//'))
    # a tracer pair
    both = plain & comm
    own = None
    if len(both)==1: own = both.pop()
    elif len(both)>1:
        # prefer one not containing '::'
        cands = sorted(both, key=lambda x: ('::' in x, len(x)))
        own = cands[0]
    p['own_plain']=sorted(plain); p['own_comm']=sorted(comm); p['name']=own
    if own: names[own]=b

print("functions with a tracer name pair: %d / %d" % (len(names), len(prof)))
print("total unique tracer names:", len(set(names)))

# ---- exports ----
print("\n" + "="*100)
print("EXPORT TABLE WITH RECOVERED NAMES")
print("="*100)
rows=[]
for rva in sorted(exports):
    ords = exports[rva]
    p = prof.get(rva)
    nm = p['name'] if p else None
    if not nm:
        # fall back: single plain ident referenced
        if p and len(p['own_plain'])==1: nm = p['own_plain'][0]+'?'
    rows.append((ords, rva, p, nm))

# resolve name for exports lacking one by looking at the pdata-owner function
import bisect
fstarts=[f[0] for f in funcs]
def owner(r):
    i=bisect.bisect_right(fstarts,r)-1
    if i>=0 and funcs[i][0]<=r<funcs[i][1]: return funcs[i][0]
    return None

named=0
for ords, rva, p, nm in rows:
    if nm: named+=1
print("exports with recovered name: %d / %d" % (named, len(rows)))

for ords, rva, p, nm in rows:
    if not p: 
        print("\n%-14s %08X  <no pdata fn>" % (','.join(map(str,ords)), rva)); continue
    ss = [s for r,s in p['strings'] if len(s)>=3 and not s.startswith('_Z')]
    print("\n ord %-11s RVA %08X  size=%-6d ins=%-5d calls=%-4d ind=%-3d fpu=%-4d  NAME=%s"
          % (','.join(map(str,ords)), rva, p['size'], p['nins'], len(p['callees']), p['ind'], p['fpu'], nm or '?'))
    if ss:
        print("      strings: %s" % ' | '.join(ss[:14]))

json.dump([{'ords':o,'rva':r,'size':(p['size'] if p else 0),'name':n,
            'strings':[s for _,s in p['strings']] if p else []} for o,r,p,n in rows],
          open(r"D:\Nesting\nestfab\re\exports_named.json","w"), indent=1)
pickle.dump(prof, open(r"D:\Nesting\nestfab\re\prof2.pkl","wb"))
