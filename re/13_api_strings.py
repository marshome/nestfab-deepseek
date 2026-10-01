import pefile, re, collections
PATH = r"D:\Nesting\nestfab\libcns_dump_64.dll"
data = open(PATH,'rb').read()
pe = pefile.PE(PATH, fast_load=False)
SEC=[(s.Name.rstrip(b'\0').decode(),s.VirtualAddress,max(s.Misc_VirtualSize,s.SizeOfRawData),
      s.PointerToRawData,s.SizeOfRawData,s.Characteristics) for s in pe.sections]
def rva2off(r):
    for n,va,vs,pr,rs,ch in SEC:
        if va<=r<va+vs: return pr+(r-va)
def off2rva(o):
    for n,va,vs,pr,rs,ch in SEC:
        if pr<=o<pr+rs: return va+(o-pr)

print("="*78); print("STRINGS IN EXPORT REGION  0x1000 .. 0x1C000  (code+rodata, BAB0)"); print("="*78)
lo,hi=0x1000,0x1C000
cur=bytearray(); start=0
out=[]
for i in range(lo,hi):
    b=data[i]
    if 32<=b<127:
        if not cur: start=i
        cur.append(b)
    else:
        if len(cur)>=3: out.append((start,cur.decode('latin1')))
        cur=bytearray()
print("count:",len(out))
for off,s in out:
    print("  %08X  %s" % (off,s))
