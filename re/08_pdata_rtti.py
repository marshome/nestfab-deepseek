import pefile, struct, re, collections, json, sys
PATH = r"D:\Nesting\nestfab\libcns_dump_64.dll"
data = open(PATH,'rb').read()
pe = pefile.PE(PATH, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SEC = [(s.Name.rstrip(b'\0').decode('latin1'), s.VirtualAddress,
        max(s.Misc_VirtualSize, s.SizeOfRawData), s.PointerToRawData, s.SizeOfRawData)
       for s in pe.sections]

def rva2off(rva):
    for n,va,vs,pr,rs in SEC:
        if va <= rva < va+vs: return pr + (rva-va)
    return None
def off2rva(off):
    for n,va,vs,pr,rs in SEC:
        if pr <= off < pr+rs: return va + (off-pr)
    return None

print("ImageBase = %016X" % IB)
print("Sections:", [(n,hex(va),hex(vs)) for n,va,vs,pr,rs in SEC])

# ---------- 1. .pdata  RUNTIME_FUNCTION ----------
pd_rva = pe.OPTIONAL_HEADER.DATA_DIRECTORY[3].VirtualAddress
pd_size = pe.OPTIONAL_HEADER.DATA_DIRECTORY[3].Size
o = rva2off(pd_rva)
funcs = []
n = pd_size//12
for i in range(n):
    b,e,u = struct.unpack_from('<III', data, o+i*12)
    if b==0 and e==0: continue
    funcs.append((b,e,u))
funcs.sort()
print("\n.pdata RVA=%08X size=%d -> %d RUNTIME_FUNCTION entries (%d valid)" % (pd_rva,pd_size,n,len(funcs)))
print("code range covered: %08X .. %08X" % (funcs[0][0], max(f[1] for f in funcs)))
print("first 8:", [(hex(a),hex(b)) for a,b,_ in funcs[:8]])
print("last 4 :", [(hex(a),hex(b)) for a,b,_ in funcs[-4:]])
sizes=[b-a for a,b,_ in funcs]
print("func size: min=%d max=%d mean=%.1f" % (min(sizes),max(sizes),sum(sizes)/len(sizes)))
json.dump([[a,b] for a,b,_ in funcs], open(r"D:\Nesting\nestfab\re\funcs.json","w"))

starts = {a:i for i,(a,b,_) in enumerate(funcs)}
def owner(rva):
    import bisect
    i = bisect.bisect_right([f[0] for f in funcs], rva)-1
    if i>=0 and funcs[i][0]<=rva<funcs[i][1]: return funcs[i][0]
    return None

# ---------- 2. RTTI ----------
print("\n" + "="*78); print("RTTI  (Itanium ABI / GCC)"); print("="*78)
# itanium mangled type names: start with N...E or a digit, inside strings
strs=[]
cur=bytearray(); start=0
for i,b in enumerate(data):
    if 32<=b<127 or b==0:
        if b and not cur: start=i
        if b: cur.append(b)
        else:
            if cur: strs.append((start,bytes(cur).decode('latin1'))); cur=bytearray()
    else:
        if cur: strs.append((start,bytes(cur).decode('latin1'))); cur=bytearray()
if cur: strs.append((start,cur.decode('latin1')))

mani = re.compile(r'^(N[0-9][A-Za-z0-9_]*E|[0-9]+[A-Za-z_][A-Za-z0-9_]*|St[0-9]|PKc|N10__cxxabiv)')
cands = [(off,s) for off,s in strs if 3<=len(s)<200 and mani.match(s)]
print("mangled-name-like strings: %d" % len(cands))
classes = sorted(set(s for _,s in cands if s.startswith('N') and s.endswith('E')))
print("class-like N...E strings: %d" % len(classes))
for s in classes[:120]:
    print("   ", s)
json.dump([(o,s) for o,s in cands], open(r"D:\Nesting\nestfab\re\mangled.json","w"))
