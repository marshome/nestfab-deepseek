import pefile, re, collections

PATH = r"D:\Nesting\nestfab\libcns_dump_64.dll"
data = open(PATH,'rb').read()
pe = pefile.PE(PATH, fast_load=True)

print("="*78); print("EXPORT DIRECTORY DETAIL"); print("="*78)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT']])
ed = pe.DIRECTORY_ENTRY_EXPORT.struct
dd = pe.OPTIONAL_HEADER.DATA_DIRECTORY[0]
print("ExportDir RVA=%08X Size=%d" % (dd.VirtualAddress, dd.Size))
print("Name RVA=%08X  OrdinalBase=%d  #Funcs=%d  #Names=%d" % (ed.Name, ed.Base, ed.NumberOfFunctions, ed.NumberOfNames))

# figure out which section the exports live in
def sec_of(rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.Name.rstrip(b'\x00').decode('latin1')
    return '?'

print("\nExport table section:", sec_of(dd.VirtualAddress))

syms = sorted(pe.DIRECTORY_ENTRY_EXPORT.symbols, key=lambda s: s.ordinal)
print("\n%-6s %-10s %-10s %s" % ("Ord","RVA","Section","Name"))
rvamin=None; rvamax=0
for s in syms:
    rvamin = s.address if rvamin is None else min(rvamin,s.address)
    rvamax = max(rvamax,s.address)
print("RVA range of exports: %08X .. %08X" % (rvamin, rvamax))
print("First 40:")
for s in syms[:40]:
    print("%-6d %08X  %-8s %s" % (s.ordinal, s.address, sec_of(s.address), s.name))
print("Last 10:")
for s in syms[-10:]:
    print("%-6d %08X  %-8s %s" % (s.ordinal, s.address, sec_of(s.address), s.name))

print("\n" + "="*78); print("IMPORTS"); print("="*78)
pe2 = pefile.PE(PATH, fast_load=False)
if hasattr(pe2,'DIRECTORY_ENTRY_IMPORT'):
    for m in pe2.DIRECTORY_ENTRY_IMPORT:
        print("  %s  (%d imports)" % (m.dll.decode(), len(m.imports)))
        for imp in m.imports[:12]:
            print("      %s" % (imp.name.decode() if imp.name else "ord#%d"%imp.ordinal))
        if len(m.imports)>12: print("      ... +%d more" % (len(m.imports)-12))
else:
    print("  (none parsed)")
print("Import dir RVA/Size: %08X / %d" % (pe2.OPTIONAL_HEADER.DATA_DIRECTORY[1].VirtualAddress,
                                           pe2.OPTIONAL_HEADER.DATA_DIRECTORY[1].Size))

print("\n" + "="*78); print("UPX / PACKER SIGNATURES"); print("="*78)
for pat in [b'UPX!', b'UPX0', b'UPX1', b'UPX2', b'$Info: This file is packed with the UPX',
            b'upx.sf.net', b'NRV', b'MPRESS', b'ASPack', b'Themida', b'VMProtect']:
    idxs=[m.start() for m in re.finditer(re.escape(pat), data)][:6]
    if idxs: print("  %-45s @ %s" % (pat.decode('latin1'), [hex(i) for i in idxs]))

print("\nASCII strings mentioning packer/version near 'UPX!':")
for m in re.finditer(rb'UPX!', data):
    print("  off %08X: %r" % (m.start(), data[m.start():m.start()+64]))
