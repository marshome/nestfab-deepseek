import sys, json, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *
prof = load_prof()
rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json"))
name_of = {r['rva']: r['name'] for r in rows if r['name']}
UN = [0x16CB0, 0x16CF0, 0xAFE0, 0x1A7D0, 0xB000, 0xAFF0]

# who references "GetPart" ?
print("who references 'GetPart' (0x9AC810):")
for r,s in STRS.items():
    if s == 'GetPart':
        for b,p in prof.items():
            if any(t==r for t,_ in p.get('strings',[])):
                print("   fn %08X %s" % (b, p.get('name')))
print()

for rva in UN:
    p = prof.get(rva, {})
    print("="*100)
    print("RVA %08X  size=%d  name=%s" % (rva, p.get('size',0), p.get('name')))
    print("  callers: %s" % ', '.join('%08X(%s)'%(c, name_of.get(c,'?')) for c in p.get('callers',[])[:12]))
    print("  callees: %s" % ', '.join('%08X(%s)'%(c, name_of.get(c,'?')) for c in p.get('callees',[])[:12]))
    print("  strings: %s" % [s for _,s in p.get('strings',[])][:8])
    print("  --- disasm ---")
    for i, ins in enumerate(disasm(rva, count=70)):
        note = ''
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS: note = '   ; "%s"' % STRS[t]
                else:
                    # maybe a double/float constant
                    import struct as _s
                    d = _s.unpack_from('<d', data, rva2off(t))[0] if rva2off(t) else None
                    f = _s.unpack_from('<f', data, rva2off(t))[0] if rva2off(t) else None
                    note = '   ; @%08X d=%r f=%r' % (t, d, f)
        print("   %08X  %-8s %-42s%s" % (ins.address, ins.mnemonic, ins.op_str, note))
        if i > 60: print("   ..."); break
