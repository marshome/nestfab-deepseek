import pefile, struct, re, collections, json
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
def norm(v):
    """normalise a stored pointer to an RVA, or None"""
    if v == 0: return None
    for cand in (v, v-IB):
        if 0 < cand < 0x2000000:
            o = rva2off(cand)
            if o is not None and cand >= 0x1000: return cand
    return None

# ---------- all C strings with RVAs ----------
strings = {}
cur=bytearray(); start=0
for i,b in enumerate(data):
    if 32<=b<127:
        if not cur: start=i
        cur.append(b)
    else:
        if cur:
            r = off2rva(start)
            if r is not None: strings[r] = cur.decode('latin1')
            cur=bytearray()
if cur:
    r = off2rva(start)
    if r is not None: strings[r]=cur.decode('latin1')

# ---------- demangler for Itanium names ----------
def demangle(m):
    """minimal Itanium demangler: names + nested names"""
    out=[]; i=0
    def parse(src, i, out, depth=0):
        while i < len(src):
            c = src[i]
            if c == 'N':
                i += 1
                # nested-name: sequence of <len><name> or St / template args
                parts=[]
                while i < len(src) and src[i] != 'E':
                    if src[i] == 'S':
                        # substitution - skip St etc
                        j=i+1
                        while j<len(src) and src[j].isdigit(): j+=1
                        if j<len(src) and src[j]=='_': j+=1
                        parts.append('<subst>'); i=j; continue
                    if src[i] == 'I':
                        # template args
                        sub=[]; i=parse(src,i+1,sub,depth+1)
                        # i now at 'E' of args
                        if i<len(src) and src[i]=='E': i+=1
                        parts.append('<'+','.join(sub)+'>')
                        continue
                    if src[i].isdigit():
                        j=i
                        while j<len(src) and src[j].isdigit(): j+=1
                        ln=int(src[i:j]); nm=src[j:j+ln]; i=j+ln
                        parts.append(nm); continue
                    if src[i] in 'CcDd':
                        i+=1
                        if i<len(src) and src[i].isdigit():
                            j=i
                            while j<len(src) and src[j].isdigit(): j+=1
                            ln=int(src[i:j]); parts.append(src[j:j+ln]); i=j+ln
                        elif i<len(src) and src[i]=='v':
                            parts.append('void'); i+=1
                        continue
                    i+=1
                if i<len(src) and src[i]=='E': i+=1
                out.append('::'.join(parts))
                return i
            else:
                i+=1
        return i
    parse(m,0,out)
    return out[0] if out else m

# ---------- find typeinfo objects ----------
# typeinfo: [ptr -> _ZTVN10__cxxabiv1XX...E+16][ptr -> mangled name string][optional base]
name_rva = {}   # rva of mangled string -> string
for r,s in strings.items():
    if re.fullmatch(r'N[0-9A-Za-z_]+E', s) and len(s)>3:
        name_rva[r]=s

# index all 8-byte words
words = collections.defaultdict(list)
for off in range(0, len(data)-8):
    v = struct.unpack_from('<Q', data, off)[0]
    r = norm(v)
    if r: words[r].append(off)

ti_types = {}
for r,s in name_rva.items():
    for off in words.get(r, []):
        # candidate typeinfo object at off-8
        ti_off = off-8
        if ti_off < 0: continue
        vt = struct.unpack_from('<Q', data, ti_off)[0]
        vtr = norm(vt)
        if vtr is None: continue
        vt_s = strings.get(vtr-16) or strings.get(vtr) or ''
        ti_types[off2rva(ti_off)] = (s, vtr, vt_s)

print("typeinfo objects found:", len(ti_types))
kinds = collections.Counter(t[2] for t in ti_types.values())
for k,c in kinds.most_common(30): print("   %-55s %d" % (k or '<unknown vtable>', c))

# ---------- find vtables ----------
# vtable: [offset-to-top][ptr -> typeinfo][funcptrs...]
ti_addrs = {}
for r,(s,vtr,vts) in ti_types.items(): ti_addrs[r]=s
vtables = {}
for r,s in ti_addrs.items():
    for off in words.get(r, []):
        voff = off-8
        if voff < 0: continue
        ott = struct.unpack_from('<Q', data, voff)[0]
        if ott not in (0,): continue     # offset-to-top usually 0 for single inheritance
        fns=[]
        p = off+8
        while p+8 <= len(data):
            fv = struct.unpack_from('<Q', data, p)[0]
            fr = norm(fv)
            if fr is None: break
            fns.append(fr); p+=8
            if len(fns)>400: break
        if fns:
            vtables[off2rva(voff)] = (s, fns)

print("\nvtables found:", len(vtables))
mult = sum(1 for v in vtables.values() if len(v[1])>1)
print("with >1 slot    :", mult)

results = {}
for r,(s,fns) in sorted(vtables.items(), key=lambda kv:-len(kv[1][1])):
    results[s] = {'vtable_rva': r, 'slots': fns, 'demangled': demangle(s)}
json.dump(results, open(r"D:\Nesting\nestfab\re\vtables.json","w"), indent=1)

print("\n" + "="*78); print("VTABLES (class -> virtual method addresses)"); print("="*78)
for r,(s,fns) in sorted(vtables.items(), key=lambda kv:-len(kv[1][1]))[:60]:
    print("\n  %s   [vtable @%08X, %d slots]" % (demangle(s), r, len(fns)))
    print("     raw: %s" % s)
    print("     fns: %s" % ' '.join('%08X'%f for f in fns[:20]))

# ---------- all class names, grouped ----------
allnames = sorted(set(s for s in name_rva.values()))
print("\n\nTOTAL class-like RTTI names:", len(allnames))
by_ns = collections.defaultdict(list)
for s in allnames:
    d = demangle(s)
    ns = d.split('::')[0] if '::' in d else '(root)'
    by_ns[ns].append(d)
for ns in sorted(by_ns, key=lambda k:-len(by_ns[k])):
    print("\n### namespace/prefix: %s  (%d)" % (ns, len(by_ns[ns])))
    for d in sorted(by_ns[ns]): print("     ", d)
