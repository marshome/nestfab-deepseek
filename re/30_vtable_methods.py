"""Name the virtual methods of every internal class by applying the tracer-label rule
   to each vtable slot function."""
import sys, json, re, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

prof = load_prof()
TRACERS = {0x64AEA0, 0x64ABF0, 0x64D9C0, 0x64ACE0, 0x978750, 0x990E80}
for b, p in prof.items():
    if '-> ' in [s for _, s in p.get('strings', [])]: TRACERS.add(b)

ID = re.compile(r'^(?://\s*)?([A-Za-z_~][A-Za-z0-9_]*(?:::[A-Za-z_~][A-Za-z0-9_]*)*)$')
NOISE = {'Local','Cloud','Start','Keys','final','intermediate','Order','Sheets','Parts',
         'Compact','Run','strategy','strategist','supervisor','sheet','biggest','end',
         'ProbeCancel','unknown_type','geometry','group','order','nesting','-> '}

def label(rva):
    insts = list(disasm(rva, count=900))
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
                if m and m.group(1) not in NOISE: return m.group(1), txt
    return None, None

vt = json.load(open(r"D:\Nesting\nestfab\re\vtables.json"))
EX = ('boost::','std::','__gnu_cxx','CryptoPP','Json','Coin','Clp','CoinUtils')
custom = {k:v for k,v in vt.items() if not v['demangled'].startswith(EX)}
cache={}
out=[]
allslots=set()
for k,v in custom.items():
    for s in v['slots']: allslots.add(s)
print("custom vtables: %d ; unique slot functions: %d" % (len(custom), len(allslots)))
for s in sorted(allslots):
    cache[s]=label(s)[0]
named=sum(1 for s in allslots if cache[s])
print("slot functions named: %d / %d" % (named, len(allslots)))

for k,v in sorted(custom.items(), key=lambda kv: kv[1]['demangled']):
    out.append("\n%s   (vtable @%s, %d slots)" % (v['demangled'], v['vtable_rva'] and hex(v['vtable_rva']), len(v['slots'])))
    for i,s in enumerate(v['slots']):
        out.append("    v%-2d %08X  %s" % (i, s, cache[s] or ''))
open(r"D:\Nesting\nestfab\re\vtable_methods.txt","w",encoding='utf-8').write('\n'.join(out))
print("wrote vtable_methods.txt")
print()
print('\n'.join(out[:120]))
