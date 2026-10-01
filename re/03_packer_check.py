import pefile, struct
PATH = r"D:\Nesting\nestfab\libcns_dump_64.dll"
data = open(PATH,'rb').read()
pe = pefile.PE(PATH, fast_load=True)

print("="*78); print("TAIL / OVERLAY"); print("="*78)
raw_end = 0
for s in pe.sections:
    raw_end = max(raw_end, s.PointerToRawData + s.SizeOfRawData)
print("max(raw end) = %08X (%d)" % (raw_end, raw_end))
print("file size    = %08X (%d)" % (len(data), len(data)))
print("overlay      = %d bytes" % (len(data)-raw_end))
print("\nLast 128 bytes:")
tail = data[-128:]
for i in range(0,128,16):
    print("  %08X  %-47s  %s" % (len(data)-128+i, tail[i:i+16].hex(' '), ''.join(chr(c) if 32<=c<127 else '.' for c in tail[i:i+16])))

print("\n" + "="*78); print("EMBEDDED PE HEADERS (MZ..PE)"); print("="*78)
found=0
for m in __import__('re').finditer(rb'MZ', data):
    off=m.start()
    if off+0x40>len(data): continue
    e_lfanew = struct.unpack_from('<I', data, off+0x3C)[0]
    if e_lfanew < 0x40 or e_lfanew > 0x1000: continue
    p = off+e_lfanew
    if p+4>len(data) or data[p:p+4]!=b'PE\x00\x00': continue
    mach = struct.unpack_from('<H', data, p+4)[0]
    nsec = struct.unpack_from('<H', data, p+6)[0]
    ts   = struct.unpack_from('<I', data, p+8)[0]
    print("  MZ@%08X  PE@%08X  machine=%04X nsect=%d timestamp=%08X" % (off,p,mach,nsec,ts))
    found+=1
print("  total:", found)

print("\n" + "="*78); print("DISASM SANITY CHECK AT EXPORT RVAs"); print("="*78)
try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    def rva2off(rva):
        for s in pe.sections:
            if s.VirtualAddress <= rva < s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
                return s.PointerToRawData + (rva - s.VirtualAddress)
        return None
    for rva in (0x16420, 0x162B0, 0x15BF0, 0x2AB0, 0x1AE40, 0x1000):
        o = rva2off(rva)
        chunk = data[o:o+48]
        print("\n  RVA %08X -> off %08X  bytes: %s" % (rva,o,chunk[:16].hex(' ')))
        n=0
        for ins in md.disasm(chunk, rva):
            print("      %08X  %-24s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
            n+=1
            if n>=6: break
        if n==0: print("      <invalid / not code>")
except ImportError as e:
    print("  capstone missing:", e)
