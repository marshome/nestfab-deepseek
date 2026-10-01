import sys, json, struct, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json"))
name_of = {r['rva']: (r['name'] or 'sub_%X' % r['rva']) for r in rows}

def annotate(rva, maxn=100000, out=None):
    L=[]
    ext = func_extent(rva)
    L.append(";; %s  RVA %08X  extent=%s (%d bytes)" % (name_of.get(rva,'?'), rva, ext,
              (ext[1]-ext[0]) if ext else 0))
    for ins in disasm(rva, count=maxn):
        note=''
        for op in ins.operands:
            if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
                t=ins.address+ins.size+op.mem.disp
                if t in STRS: note='"%s"' % STRS[t].replace('"','\\"')
                else:
                    o=rva2off(t)
                    if o is not None:
                        d=struct.unpack_from('<d',data,o)[0]
                        f=struct.unpack_from('<f',data,o)[0]
                        i=struct.unpack_from('<i',data,o)[0]
                        note='@%08X i=%d f=%g d=%g' % (t,i,f,d)
            elif op.type==X86_OP_IMM and ins.mnemonic in ('call','jmp'):
                t=op.imm
                if t in name_of: note='-> %s' % name_of[t]
        L.append("  %08X  %-9s %-46s ; %s" % (ins.address, ins.mnemonic, ins.op_str, note))
    txt='\n'.join(L)
    if out: open(out,'w',encoding='utf-8').write(txt)
    return txt

# struct offsets touched by the small accessors
print("="*100); print("STRUCT OFFSETS in small getters/setters"); print("="*100)
for r in sorted(rows, key=lambda r: r['ords'][0]):
    if r['size'] > 90: continue
    offs=[]
    for ins in disasm(r['rva']):
        for op in ins.operands:
            if op.type==X86_OP_MEM and op.mem.base==X86_REG_RCX and op.mem.disp!=0:
                offs.append(op.mem.disp)
            if op.type==X86_OP_MEM and op.mem.base==X86_REG_RBX and op.mem.disp!=0:
                offs.append(op.mem.disp)
    if offs:
        print("  %-52s %08X  mem[rbx/rcx+ %s]" % (name_of[r['rva']], r['rva'],
              ', '.join('0x%X'%o for o in sorted(set(offs)))))

print()
for rva in (0x2AB0, 0x6100):
    print("annotated listing written:", hex(rva))
    annotate(rva, out=r"D:\Nesting\nestfab\re\listing_%X.txt" % rva)
print("\nlaunch-local excerpt:")
print(annotate(0x2AB0)[:6000])
