import pefile, datetime, hashlib, os, sys

PATH = r"D:\Nesting\nestfab\libcns_dump_64.dll"

pe = pefile.PE(PATH, fast_load=False)

print("=" * 78)
print("FILE:", PATH)
print("SIZE:", os.path.getsize(PATH), "bytes")
print("MD5 :", hashlib.md5(open(PATH,'rb').read()).hexdigest())
print("SHA256:", hashlib.sha256(open(PATH,'rb').read()).hexdigest())
print("=" * 78)

print("\n--- FILE HEADER ---")
print("Machine            : %04X" % pe.FILE_HEADER.Machine,
      {0x14c:'i386', 0x8664:'AMD64', 0xaa64:'ARM64'}.get(pe.FILE_HEADER.Machine,'?'))
print("NumberOfSections   :", pe.FILE_HEADER.NumberOfSections)
print("TimeDateStamp      :", pe.FILE_HEADER.TimeDateStamp,
      datetime.datetime.utcfromtimestamp(pe.FILE_HEADER.TimeDateStamp).isoformat() + "Z")
print("PointerToSymbolTbl :", pe.FILE_HEADER.PointerToSymbolTable)
print("NumberOfSymbols    :", pe.FILE_HEADER.NumberOfSymbols)
print("SizeOfOptionalHdr  :", pe.FILE_HEADER.SizeOfOptionalHeader)
print("Characteristics    : %04X" % pe.FILE_HEADER.Characteristics)

print("\n--- OPTIONAL HEADER ---")
oh = pe.OPTIONAL_HEADER
print("Magic              : %04X" % oh.Magic, "(PE32+)" if oh.Magic==0x20b else "(PE32)")
print("Subsystem          :", oh.Subsystem, {2:'GUI',3:'CONSOLE'}.get(oh.Subsystem,'?'))
print("DllCharacteristics : %04X" % oh.DllCharacteristics,
      "ASLR" if oh.DllCharacteristics & 0x40 else "",
      "DYNAMIC_BASE" if oh.DllCharacteristics & 0x40 else "",
      "NX" if oh.DllCharacteristics & 0x100 else "",
      "HIGH_ENTROPY_VA" if oh.DllCharacteristics & 0x20 else "",
      "CFG" if oh.DllCharacteristics & 0x4000 else "")
print("ImageBase          : %016X" % oh.ImageBase)
print("AddressOfEntryPoint: %08X" % oh.AddressOfEntryPoint, "(RVA)")
print("SizeOfImage        : %08X" % oh.SizeOfImage)
print("SizeOfHeaders      : %08X" % oh.SizeOfHeaders)
print("CheckSum           : %08X" % oh.CheckSum)
print("Sections           :", oh.NumberOfRvaAndSizes, "data directories")
print("DllName (export)   :", getattr(pe,'export_dir',None) and pe.DIRECTORY_ENTRY_EXPORT.name)

print("\n--- SECTIONS ---")
print("%-10s %10s %10s %10s %10s  %s" % ("Name","VirtAddr","VirtSize","RawPtr","RawSize","Flags"))
for s in pe.sections:
    n = s.Name.rstrip(b'\x00').decode('latin1')
    ch = s.Characteristics
    flags = []
    if ch & 0x20000000: flags.append('X')
    if ch & 0x80000000: flags.append('W')
    if ch & 0x40000000: flags.append('R')
    if ch & 0x00000020: flags.append('CODE')
    if ch & 0x00000040: flags.append('IDATA')
    if ch & 0x00000080: flags.append('UDATA')
    if ch & 0x02000000: flags.append('DISCARD')
    print("%-10s %10X %10X %10X %10X  %s" % (n, s.VirtualAddress, s.Misc_VirtualSize,
          s.PointerToRawData, s.SizeOfRawData, ','.join(flags)))
    print("           entropy=%.3f" % s.get_entropy())

print("\n--- EXPORTS ---")
if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
    ed = pe.DIRECTORY_ENTRY_EXPORT
    print("DLL Name    :", ed.name.decode() if ed.name else None)
    print("OrdinalBase :", ed.struct.Base)
    print("NumFuncs    :", ed.struct.NumberOfFunctions)
    print("NumNames    :", ed.struct.NumberOfNames)
    print("Total symbols:", len(ed.symbols))
else:
    print("NO EXPORT DIRECTORY")
