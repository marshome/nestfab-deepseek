import pefile, struct, re
PATH = r"D:\Nesting\nestfab\libcns_dump_64.dll"
data = open(PATH,'rb').read()
pe = pefile.PE(PATH, fast_load=False)

def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None

ed_rva = pe.OPTIONAL_HEADER.DATA_DIRECTORY[0].VirtualAddress
ed_size = pe.OPTIONAL_HEADER.DATA_DIRECTORY[0].Size
o = rva2off(ed_rva)
print("export dir off=%08X size=%d" % (o, ed_size))
f = struct.unpack_from('<IIHHIIIIIII', data, o)
print("""
Characteristics/flags : %08X
TimeDateStamp         : %08X
Major/Minor           : %d.%d
Name RVA              : %08X  -> %r
Base                  : %d
NumberOfFunctions     : %d
NumberOfNames         : %d
AddressOfFunctions    : %08X
AddressOfNames        : %08X
AddressOfNameOrdinals : %08X""" % (f[0], f[1], f[2], f[3], f[4], None, f[5], f[6], f[7], f[8], f[9], f[10]))

name_rva, nfunc, nnames, aof, aon, aono = f[4], f[6], f[7], f[8], f[9], f[10]
for label, rva, cnt, width in [("AddressOfFunctions", aof, nfunc, 4),
                               ("AddressOfNames", aon, nnames, 4),
                               ("AddressOfNameOrdinals", aono, nnames, 2)]:
    off = rva2off(rva) if rva else None
    print("\n%s rva=%s off=%s count=%d" % (label, hex(rva) if rva else None, hex(off) if off else None, cnt))
    if off:
        raw = data[off:off+min(cnt*width+64, 256)]
        print("   first bytes:", raw[:64].hex(' '))

print("\n--- RAW 1424 bytes at export dir (hex+ascii) ---")
raw = data[o:o+ed_size]
for i in range(0, len(raw), 16):
    chunk = raw[i:i+16]
    print("  %08X  %-47s  %s" % (ed_rva+i, chunk.hex(' '), ''.join(chr(c) if 32<=c<127 else '.' for c in chunk)))

print("\n--- ALL printable strings inside export dir blob ---")
for m in re.finditer(rb'[ -~]{3,}', raw):
    print("   +%04X %r" % (m.start(), m.group().decode('latin1')))

print("\n--- .rsrc section full hexdump (0x1000 bytes) ---")
rs = [s for s in pe.sections if s.Name.rstrip(b'\0')==b'.rsrc'][0]
rr = data[rs.PointerToRawData: rs.PointerToRawData+rs.SizeOfRawData]
for i in range(0, min(len(rr),0x600), 16):
    chunk = rr[i:i+16]
    asc = ''.join(chr(c) if 32<=c<127 else '.' for c in chunk)
    print("  %08X  %-47s  %s" % (0xB42000+i, chunk.hex(' '), asc))
