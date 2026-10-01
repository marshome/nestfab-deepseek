import sys, re, json, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
prof = load_prof()
rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json"))

print("="*100); print("UNNAMED EXPORTS: referenced strings + callees"); print("="*100)
for r in rows:
    if r['name']: continue
    rva = r['rva']; p = prof.get(rva, {})
    print("\n ord %-11s RVA %08X size=%d cands=%s" % (','.join(map(str,r['ords'])), rva, r['size'], r['cands'][:6]))
    print("    strings:")
    for t,s in p.get('strings',[])[:18]:
        print("        %08X %r" % (t,s))
    print("    callees(exported): %s" % [hex(c) for c in r['callees_exp']])
    print("    first insns:", ' ; '.join('%s %s'%(i.mnemonic,i.op_str) for i in list(disasm(rva,count=6))))

print("\n"+"="*100); print("THE CNS_ ALIAS QUESTION — disasm of 0xB600 and 0xBA50"); print("="*100)
for rva in (0xB600, 0xBA50, 0xCEC0):
    print("\n--- RVA %08X ---" % rva)
    for i,ins in enumerate(disasm(rva, count=40)):
        note=''
        for op in ins.operands:
            from capstone.x86 import X86_OP_MEM, X86_REG_RIP
            if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
                t=ins.address+ins.size+op.mem.disp
                if t in STRS: note='   ; "%s"' % STRS[t]
        print("   %08X  %-8s %-40s%s" % (ins.address, ins.mnemonic, ins.op_str, note))
