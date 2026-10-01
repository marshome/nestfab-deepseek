"""FINAL name recovery = first non-noise dbg-tracer label, falling back to the earliest
   identifier literal.  Handles both entry-label styles: 'Name' and '// Name'."""
import sys, json, re, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

prof = load_prof()
rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json"))
TRACERS = {0x64AEA0, 0x64ABF0, 0x64D9C0, 0x64ACE0, 0x978750, 0x990E80}
for b, p in prof.items():
    if '-> ' in [s for _, s in p.get('strings', [])]: TRACERS.add(b)

ID  = re.compile(r'^(?://\s*)?([A-Za-z_~][A-Za-z0-9_]*(?:::[A-Za-z_~][A-Za-z0-9_]*)*)$')
NOISE = {'Local','Cloud','Start','Keys','final','intermediate','Order','Sheets','Parts',
         'Compact','Run','strategy','strategist','supervisor','sheet','biggest','end',
         'ProbeCancel','unknown_type','geometry','group','order','nesting'}

def labels(rva, maxscan=700):
    """all (addr, label) pairs seen as arguments of dbg tracer calls, in order"""
    insts = list(disasm(rva, count=maxscan))
    out=[]
    for i, ins in enumerate(insts):
        if ins.mnemonic=='call' and ins.operands and ins.operands[0].type==X86_OP_IMM \
           and ins.operands[0].imm in TRACERS:
            for j in range(i-1, max(0,i-40), -1):
                pv=insts[j]
                if pv.mnemonic!='lea' or len(pv.operands)<2: continue
                d,s=pv.operands[0],pv.operands[1]
                if d.type!=X86_OP_REG or MD.reg_name(d.reg) not in ('rcx','rdx','r8','r9'): continue
                if s.type!=X86_OP_MEM or s.mem.base!=X86_REG_RIP: continue
                t=pv.address+pv.size+s.mem.disp
                txt=STRS.get(t)
                if not txt: continue
                m=ID.match(txt)
                if m:
                    out.append((ins.address, m.group(1), txt))
                    break
    return out

def earliest_ident(rva):
    first={}
    for ins in disasm(rva, count=400):
        for op in ins.operands:
            if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
                t=ins.address+ins.size+op.mem.disp
                s=STRS.get(t)
                if s and t not in first:
                    m=ID.match(s)
                    if m and m.group(1) not in NOISE: first[t]=(ins.address,m.group(1),s)
    if not first: return None
    return sorted(first.values(), key=lambda x:x[0])[0]

final={}
for r in rows:
    ls = labels(r['rva'])
    ls = [(a,n,t) for a,n,t in ls if n not in NOISE]
    loose = earliest_ident(r['rva'])
    nm=None
    if ls:
        nm = ls[0][1]
        # if the loose literal is a suffix of a *later* more specific label and the
        # first label is generic, keep the first label anyway (it is the entry label)
    if not nm and loose: nm = loose[1]
    if not nm and r['rva'] in (0x16CB0,0x16CF0,0xAFE0,0x1A7D0,0xB000,0xAFF0): nm=None
    final[r['rva']] = nm
    r['name'] = nm
    r['labels'] = [t for _,_,t in ls][:4]

json.dump(rows, open(r"D:\Nesting\nestfab\re\exports_table.json","w"), indent=1, ensure_ascii=False)
named = sum(1 for r in rows if r['name'])
print("named: %d / %d" % (named, len(rows)))
print("\nUNNAMED:")
for r in rows:
    if not r['name']:
        print("  ord %-11s %08X size=%-5d labels=%s loose=%s" % (','.join(map(str,r['ords'])), r['rva'],
              r['size'], r.get('labels'), earliest_ident(r['rva'])))
dups=collections.Counter(r['name'] for r in rows if r['name'])
print("\nOVERLOADS (same name, different RVA):")
for k,v in sorted(dups.items()):
    if v>1: print("   %-46s x%d  %s" % (k, v, ['%X'%r['rva'] for r in rows if r['name']==k]))
print("\nFINAL NAMES in ordinal order:")
for r in sorted(rows, key=lambda r:r['ords'][0]):
    print("  ord %-11s %08X %-6d %s" % (','.join(map(str,r['ords'])), r['rva'], r['size'], r['name'] or '?'))
