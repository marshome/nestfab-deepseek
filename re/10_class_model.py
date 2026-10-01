import json, collections, re, pefile, struct
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

vt = json.load(open(r"D:\Nesting\nestfab\re\vtables.json"))
syms = sorted(pe.DIRECTORY_ENTRY_EXPORT.symbols, key=lambda s:s.ordinal)
exports = collections.OrderedDict()
for s in syms:
    exports.setdefault(s.address, []).append(s.ordinal)

print("unique exports: %d" % len(exports))

EXCLUDEPFX = ('boost::','std::','__gnu_cxx','CryptoPP','Json','Coin','Clp','CoinUtils',
              '_Rb_tree','_Vector','_Hashtable','_Deque','_List','_Sp_counted','_Task','_Funct','_Bind','_Mem_fn')
def is_custom(d):
    return not d.startswith(EXCLUDEPFX) and '<' not in d.split('::')[0]

# namespace histogram of vtables
ns = collections.Counter()
for name,v in vt.items():
    d = v['demangled']
    if is_custom(d):
        ns[d.split('::')[0]] += 1
print("\ncustom-namespace vtables:")
for k,c in ns.most_common(): print("   %-16s %d" % (k,c))

print("\n" + "="*78); print("CUSTOM CLASS MODEL (namespace -> class -> #virtuals)"); print("="*78)
by_ns = collections.defaultdict(list)
for name,v in vt.items():
    d = v['demangled']
    if is_custom(d):
        by_ns[d.split('::')[0]].append((d, v['vtable_rva'], v['slots']))
for k in sorted(by_ns):
    print("\n### %s (%d classes)" % (k, len(by_ns[k])))
    for d, vr, slots in sorted(by_ns[k]):
        tag = ''
        if any(s in exports for s in slots): tag = '  <== CONTAINS EXPORT'
        print("   %-58s vt=%08X slots=%2d%s" % (d, vr, len(slots), tag))

print("\n" + "="*78); print("EXPORTS THAT ARE VIRTUAL METHODS"); print("="*78)
slot2class = {}
for name,v in vt.items():
    d=v['demangled']
    for i,s in enumerate(v['slots']):
        slot2class.setdefault(s, []).append("%s::v%d" % (d,i))
hit=0
for a in sorted(exports):
    if a in slot2class:
        hit+=1
        print("  %08X ord=%-4s  %s" % (a, ','.join(map(str,exports[a])), ' | '.join(slot2class[a][:3])))
print("  -> %d of %d exports are vtable slots" % (hit, len(exports)))

print("\n" + "="*78); print("ALL EXPORT RVAs (ordinal pairs, sorted by ordinal)"); print("="*78)
for a in sorted(exports, key=lambda x: exports[x][0]):
    print("  ord %-9s RVA %08X" % (','.join(map(str,exports[a])), a))
