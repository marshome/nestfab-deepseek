import pefile, re, collections, struct
PATH = r"D:\Nesting\nestfab\libcns_dump_64.dll"
data = open(PATH,'rb').read()
pe = pefile.PE(PATH, fast_load=False)

print("="*78); print("DATA DIRECTORIES"); print("="*78)
names = ['EXPORT','IMPORT','RESOURCE','EXCEPTION','SECURITY','BASERELOC','DEBUG','ARCH',
         'GLOBALPTR','TLS','LOAD_CONFIG','BOUND_IMPORT','IAT','DELAY_IMPORT','CLR','RESERVED']
for i,dd in enumerate(pe.OPTIONAL_HEADER.DATA_DIRECTORY):
    if dd.VirtualAddress or dd.Size:
        print("  %-14s RVA=%08X Size=%d" % (names[i] if i<len(names) else '?', dd.VirtualAddress, dd.Size))

print("\n" + "="*78); print("UNIQUE EXPORT ADDRESSES"); print("="*78)
syms = sorted(pe.DIRECTORY_ENTRY_EXPORT.symbols, key=lambda s:s.ordinal)
addrs = collections.Counter(s.address for s in syms)
print("  total export entries :", len(syms))
print("  unique addresses     :", len(addrs))
dup = sum(1 for a,c in addrs.items() if c>1)
print("  addrs shared by >1   :", dup)
# figure out pairing pattern
byord = {s.ordinal: s.address for s in syms}
pairs = [(o, byord.get(o), byord.get(o+1)) for o in range(1, len(syms)+1, 2)]
same = sum(1 for o,a,b in pairs if a==b)
print("  odd/even pairs equal : %d / %d" % (same, len(pairs)))
print("\n  Unique RVA list (sorted):")
ua = sorted(addrs)
for i in range(0, len(ua), 6):
    print("    " + "  ".join("%08X"%x for x in ua[i:i+6]))

print("\n" + "="*78); print("COMPILER / RUNTIME FINGERPRINTS"); print("="*78)
pats = {
 'MSVC   ': rb'Microsoft Visual C\+\+|MSVC|Rich',
 'GCC/MinGW': rb'GCC: \(|GCC [0-9]|mingw|libgcc|__gcc_',
 'Clang  ': rb'clang version|LLVM',
 'Rust   ': rb'rustc|/rustc/|cargo|RUST_BACKTRACE',
 'Go     ': rb'go1\.[0-9]|runtime\.gopanic|golang',
 'Delphi ': rb'Embarcadero|Borland|System\.SysUtils|TObject',
 '.NET   ': rb'mscoree|\.NETFramework',
 'Qt     ': rb'Qt_?[0-9]|qt\.qpa|QApplication|libQt',
 'PDB    ': rb'[A-Za-z]:\\[^"\x00]{4,80}\.pdb',
 'TBB    ': rb'tbb::|oneapi',
 'Boost  ': rb'boost::|libboost',
 'Eigen  ': rb'Eigen::|libeigen',
 'OpenCV ': rb'opencv|cv::',
 'ACIS/Parasolid': rb'ACIS|Parasolid|InterOp',
 'Clipper': rb'Clipper|clipper',
 'CGAL   ': rb'CGAL',
 'Boost.Geometry': rb'boost::geometry',
}
for k,p in pats.items():
    ms = [m for m in re.finditer(p, data)][:3]
    if ms:
        print("  %-16s %d hits e.g. %s" % (k, len(re.findall(p,data)), [hex(m.start()) for m in ms]))

print("\n  --- PDB / source paths found ---")
for m in list(re.finditer(rb'[A-Za-z]:\\[ -~]{6,120}\.(pdb|obj|cpp|c|h|hpp)', data))[:25]:
    print("   ", m.group().decode('latin1'))

print("\n" + "="*78); print("RICH HEADER / DOS STUB"); print("="*78)
dos = data[:pe.DOS_HEADER.e_lfanew]
print("  DOS stub len:", len(dos))
for m in re.finditer(rb'Rich', data[:0x1000]):
    print("  'Rich' @ %08X" % m.start())
rich = data.find(b'Rich')
if rich>0:
    key = struct.unpack_from('<I', data, rich+4)[0]
    print("  Rich key: %08X" % key)
    i=rich
    while i>=0x80:
        v = struct.unpack_from('<I', data, i-8)[0]
        c = struct.unpack_from('<I', data, i-4)[0]
        if v==0 and c==0: break
        print("    id=%6d ver=%6d (0x%04X) count=%d" % (c, v, v, c))
        i-=8
print("  'This program cannot be run in DOS mode' present:",
      b'This program cannot be run in DOS mode' in dos)

print("\n" + "="*78); print(".rsrc CONTENT"); print("="*78)
try:
    for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        print("  type %s" % entry.name if entry.name else "  type id %d" % entry.id)
        for e2 in entry.directory.entries:
            print("     name/id %s" % (e2.name if e2.name else e2.id))
            for e3 in e2.directory.entries:
                d = pe.get_data(e3.data.struct.OffsetToData, min(e3.data.struct.Size, 64))
                print("        lang %s size %d data %s" % (e3.data.lang, e3.data.struct.Size, d[:32].hex(' ')))
except Exception as ex:
    print("  no resource tree:", ex)
