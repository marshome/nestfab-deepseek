import pickle, re, collections, json
prof = pickle.load(open(r"D:\Nesting\nestfab\re\prof2.pkl","rb"))
D = pickle.load(open(r"D:\Nesting\nestfab\re\xref.pkl","rb"))
exports, funcs, strs = D['exports'], D['funcs'], D['strs']

IDENT = re.compile(r'^[A-Za-z_~][A-Za-z0-9_]*(::[A-Za-z_~][A-Za-z0-9_]*)*$')
def identlike(s):
    return 3<=len(s)<=90 and bool(IDENT.match(s)) and s not in ('basic_string','vector','string','Local','Cloud','Order','Start','Keys','final','intermediate','Order valid','pqcs','timer','thread','winsock','iocp','cancel','close','mutex','sha1')

# every function: which ident strings does it reference directly (as data refs)
print("="*100); print("AMBIGUITY ANALYSIS: exports referencing >1 identifier-like string"); print("="*100)
amb=0; multi_all=0
for rva in sorted(exports):
    p=prof.get(rva)
    if not p: continue
    ids=[s for r,s in p['strings'] if identlike(s)]
    ids = sorted(set(ids))
    if len(ids)>1:
        amb+=1
        print("  RVA %08X ord %-11s ids=%s" % (rva, ','.join(map(str,exports[rva])), ids))
print("  exports with >1 ident string: %d" % amb)

named={}
for rva in sorted(exports):
    p=prof.get(rva)
    if not p: continue
    ids=sorted(set(s for r,s in p['strings'] if identlike(s)))
    if len(ids)==1: named[rva]=ids[0]
print("\nexports with exactly 1 ident string:", len(named))

# ---- alphabetical hypothesis ----
print("\n" + "="*100); print("ALPHABETICAL-ORDINAL TEST"); print("="*100)
seq=[]
for rva in sorted(exports, key=lambda r: exports[r][0]):
    seq.append((exports[rva][0], rva, named.get(rva)))
known=[(o,r,n) for o,r,n in seq if n]
print("known in ordinal order (%d):" % len(known))
for o,r,n in known: print("   ord %-4d %08X  %s" % (o,r,n))
ks=[n for _,_,n in known]
ok = ks == sorted(ks)
print("\n  known names already alphabetical in ordinal order? ", ok)
if not ok:
    bad=[(a,b) for a,b in zip(ks,ks[1:]) if a>b]
    print("  violations: %d  e.g. %s" % (len(bad), bad[:12]))

# are names unique?
allnames=[n for _,_,n in known]
dup=[k for k,v in collections.Counter(allnames).items() if v>1]
print("  duplicate names among exports:", dup)

# also check: does every export have a unique name overall?
print("\n  name pool size (all ident strings in rodata 0x9A0000-0x9B0000):",
      len(set(s for r,s in strs.items() if 0x9A0000<=r<0x9B0000 and identlike(s))))
