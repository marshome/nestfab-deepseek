import pefile, struct, re, collections, json, sys, pickle
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_REG_RIP

PATH = r"D:\Nesting\nestfab\libcns_dump_64.dll"
data = open(PATH,'rb').read()
pe = pefile.PE(PATH, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
SEC = [(s.Name.rstrip(b'\0').decode('latin1'), s.VirtualAddress,
        max(s.Misc_VirtualSize, s.SizeOfRawData), s.PointerToRawData, s.SizeOfRawData,
        s.Characteristics) for s in pe.sections]
def rva2off(rva):
    for n,va,vs,pr,rs,ch in SEC:
        if va <= rva < va+vs: return pr + (rva-va)
    return None
def off2rva(off):
    for n,va,vs,pr,rs,ch in SEC:
        if pr <= off < pr+rs: return va + (off-pr)
    return None

# ---- strings map: rva -> str
strs={}
cur=bytearray(); start=0
for i,b in enumerate(data):
    if 32<=b<127:
        if not cur: start=i
        cur.append(b)
    else:
        if len(cur)>=3:
            r=off2rva(start)
            if r is not None: strs[r]=cur.decode('latin1')
        cur=bytearray()
print("strings:", len(strs))

# ---- functions from .pdata
pd_rva = pe.OPTIONAL_HEADER.DATA_DIRECTORY[3].VirtualAddress
pd_size= pe.OPTIONAL_HEADER.DATA_DIRECTORY[3].Size
o=rva2off(pd_rva)
funcs=[]
for i in range(pd_size//12):
    b,e,u = struct.unpack_from('<III', data, o+i*12)
    if b: funcs.append((b,e))
funcs.sort()
fstarts=[f[0] for f in funcs]
import bisect
def owner(rva):
    i=bisect.bisect_right(fstarts,rva)-1
    if i>=0 and funcs[i][0]<=rva<funcs[i][1]: return funcs[i][0]
    return None
print("functions:", len(funcs))

# ---- exports
syms = pe.DIRECTORY_ENTRY_EXPORT.symbols
exp_ord = collections.OrderedDict()
for s in sorted(syms, key=lambda x:x.ordinal):
    exp_ord.setdefault(s.address, []).append(s.ordinal)
print("unique exports:", len(exp_ord))

# ---- linear disasm per function
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True
codesecs = [s for s in SEC if s[5] & 0x20000000]
prof = {}
allxrefs = collections.defaultdict(list)   # target func -> [caller func]
N=len(funcs)
for idx,(b,e) in enumerate(funcs):
    if idx % 2000 == 0: print("  ...%d/%d" % (idx,N), flush=True)
    off = rva2off(b)
    if off is None: continue
    size = min(e-b, 400000)
    code = data[off:off+size]
    refs=[]; calls=[]; nins=0; ind=0; fpu=0; imms=collections.Counter()
    for ins in md.disasm(code, b):
        nins+=1
        m=ins.mnemonic
        if m.startswith('call') or m.startswith('jmp'):
            if ins.operands and ins.operands[0].type==2:  # IMM
                t=ins.operands[0].imm
                if t: calls.append(t)
            else: ind+=1
        if m.startswith('v') or m.startswith('p') or m.startswith('movs') or m.startswith('adds') or m.startswith('muls') or m.startswith('divs') or m.startswith('cvt') or m.startswith('ucomi') or m.startswith('comi'):
            fpu+=1
        for op in ins.operands:
            if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
                tgt = ins.address+ins.size+op.mem.disp
                refs.append(tgt)
    prof[b] = dict(start=b,end=e,size=e-b,nins=nins,calls=calls,ind=ind,fpu=fpu,
                   data_refs=sorted(set(refs)))
    for c in set(calls):
        if c in fstarts or (owner(c)): allxrefs[owner(c) or c].append(b)

# attribute strings
for b,p in prof.items():
    ss=[]
    for r in p['data_refs']:
        s=strs.get(r)
        if s and 3<=len(s)<220: ss.append((r,s))
    p['strings']=ss
    p['callees']=sorted(set(p['calls']))
    p['callers']=sorted(set(allxrefs.get(b,[])))

pickle.dump({'prof':prof,'funcs':funcs,'exports':{k:v for k,v in exp_ord.items()},
             'strs':strs}, open(r"D:\Nesting\nestfab\re\xref.pkl","wb"))
print("done")
