import sys, json, collections, struct
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json"))
name_of = {r['rva']: (r['name'] or 'sub_%X'%r['rva']) for r in rows}

def offsets(rva):
    """offsets touched through the first-argument pointer (rcx / a copy of it)"""
    offs=set(); aliases={'rcx'}; 
    for ins in disasm(rva, count=400):
        # track copies of rcx into other regs
        if ins.mnemonic=='mov' and len(ins.operands)==2:
            a,b=ins.operands
            if a.type==X86_OP_REG and b.type==X86_OP_REG:
                an=MD.reg_name(a.reg); bn=MD.reg_name(b.reg)
                if bn in aliases: aliases.add(an)
        for op in ins.operands:
            if op.type==X86_OP_MEM and op.mem.base and MD.reg_name(op.mem.base) in aliases:
                offs.add(op.mem.disp)
    return offs

print("="*100); print("HANDLE FINGERPRINTS  (offsets reached through the first argument)"); print("="*100)
info={}
for r in rows:
    o=offsets(r['rva'])
    info[r['rva']]=o
    big=sorted(x for x in o if x>0x30)
    print("  %-52s %08X  n=%-3d max=0x%-5X %s" % (name_of[r['rva']], r['rva'], len(o),
          max(o) if o else 0, ' '.join('0x%X'%x for x in big[:12])))

# cluster: functions that touch Order-only offsets (0xF8/0xF9/0x100/0x1b0/0x248/0x268/0x288)
ORDER_MARK={0xF8,0xF9,0x100,0x1B0,0x1B8,0x1C0,0x248,0x268,0x288,0x1F8,0x22,0x23,0x41,0x48,0x50}
print("\n" + "="*100); print("FUNCTIONS TOUCHING ORDER-LIKE OFFSETS"); print("="*100)
for r in sorted(rows, key=lambda r:r['ords'][0]):
    o=info[r['rva']]
    hit=sorted(o & ORDER_MARK)
    if len(hit)>=2:
        print("  ord %-11s %-52s %s" % (','.join(map(str,r['ords'])), name_of[r['rva']],
              ' '.join('0x%X'%x for x in hit)))
