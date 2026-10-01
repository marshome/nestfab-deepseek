import pefile, struct, re, collections
PATH = r"D:\Nesting\nestfab\libcns_dump_64.dll"
data = open(PATH,'rb').read()
pe = pefile.PE(PATH, fast_load=False)
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
    if v==0: return None
    for c in (v, v-IB):
        if 0x1000 <= c < 0x2000000 and rva2off(c) is not None: return c
    return None

# all strings
strs={}
cur=bytearray(); start=0
for i,b in enumerate(data):
    if 32<=b<127:
        if not cur: start=i
        cur.append(b)
    else:
        if cur:
            r=off2rva(start)
            if r is not None: strs[r]=cur.decode('latin1')
            cur=bytearray()

cns = {r:s for r,s in strs.items() if s.startswith('CNS_') or s.startswith('// CNS_')}
print("CNS_* strings: %d" % len(cns))
for r,s in sorted(cns.items(), key=lambda kv:kv[1]):
    print("   %08X  %s" % (r,s))

# build word index of all 8-byte pointers -> rva
ptr_at = collections.defaultdict(list)
for off in range(0, len(data)-8, 1):
    v=struct.unpack_from('<Q', data, off)[0]
    r=norm(v)
    if r is not None: ptr_at[r].append(off)

print("\n" + "="*78)
print("REFERENCES TO CNS_* STRINGS (pointer / near-pointer)")
print("="*78)
for r,s in sorted(cns.items(), key=lambda kv: kv[1]):
    refs = ptr_at.get(r, [])
    print("\n  %s  (str @%08X)  refs=%d" % (s, r, len(refs)))
    for off in refs[:6]:
        base = off - 8*3
        ctx=[]
        for k in range(6):
            p = off - 8*3 + k*8
            if p<0 or p+8>len(data): continue
            v=struct.unpack_from('<Q',data,p)[0]
            rr=norm(v)
            desc = ('rva:%08X'%rr) if rr else ('0x%X'%v)
            lab = strs.get(rr,'') if rr else ''
            mark = ' <==THIS' if p==off else ''
            ctx.append("      +%2d %016X %-22s %s%s" % (p-off, v, desc, lab[:52], mark))
        print("   word@%08X (rva %s):" % (off, off2rva(off) and '%08X'%off2rva(off)))
        print('\n'.join(ctx))

# find RIP-relative code refs
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True
targets = set(cns)
print("\n" + "="*78); print("CODE REFERENCES (lea rip) TO CNS_* STRINGS"); print("="*78)
found = collections.defaultdict(list)
for s in pe.sections:
    if not (s.Characteristics & 0x20000000): continue
    base=s.VirtualAddress; o=s.PointerToRawData
    code=data[o:o+s.SizeOfRawData]
    for ins in md.disasm(code, base):
        for op in ins.operands:
            if op.type==3 and op.mem.base==41:  # X86_OP_MEM, RIP
                tgt = ins.address+ins.size+op.mem.disp
                if tgt in targets:
                    found[tgt].append((ins.address, ins.mnemonic, ins.op_str))
for t in sorted(found):
    print("\n  %s:" % strs[t])
    for a,m,o in found[t][:8]: print("     %08X  %s %s" % (a,m,o))
print("\ncode-refs found for %d of %d CNS strings" % (len(found), len(cns)))
