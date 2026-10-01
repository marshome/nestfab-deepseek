"""Map internal (non-exported) tracer-labelled functions to RVAs."""
import sys, json, re, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

prof = load_prof()
TRACERS = {0x64AEA0, 0x64ABF0, 0x64D9C0, 0x64ACE0, 0x978750, 0x990E80}
for b, p in prof.items():
    if '-> ' in [s for _, s in p.get('strings', [])]: TRACERS.add(b)

ID = re.compile(r'^\s*(?://\s*)?([A-Za-z_~][A-Za-z0-9_]*(?:::[A-Za-z_~][A-Za-z0-9_]*)*)\s*$')
NOISE = {'Local','Cloud','Start','Keys','final','intermediate','Order','Sheets','Parts',
         'Compact','Run','strategy','strategist','supervisor','sheet','biggest','end',
         'ProbeCancel','unknown_type','geometry','group','order','nesting'}

def label(rva):
    insts = list(disasm(rva, count=1200))
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

rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json", encoding='utf-8'))
exp = {r['rva']: r['name'] for r in rows}

# candidate internal name strings: identifier-like literals in rodata not used as export names
used = set(v for v in exp.values() if v)
cands = collections.defaultdict(list)
for r, s in STRS.items():
    if not (0x9A0000 <= r < 0x9B0000): continue
    m = ID.match(s)
    if not m: continue
    n = m.group(1)
    if n in used or n in NOISE or len(n) < 3 or n.startswith('__'): continue
    if n.startswith(('CNS_','Add','Get','Set')) and n in used: continue
    if '::' in n and n.split('::')[0] in ('std','boost','__gnu_cxx','Json','CryptoPP','Coin','Clp'): continue
    cands[n].append(r)

# which functions reference each candidate?
found = {}
for b, p in prof.items():
    if b in exp: continue
    refs = {t for t, _ in p.get('strings', [])}
    for n, rs in cands.items():
        if any(r in refs for r in rs):
            found.setdefault(n, []).append(b)

print("candidate internal names referenced by >=1 non-export function: %d" % len(found))
resolved = {}
for n, fns in sorted(found.items()):
    for fn in fns[:6]:
        lab, raw = label(fn)
        if lab == n:
            resolved[n] = fn
            break
print("resolved to a unique function via entry tracer label: %d" % len(resolved))
lines = []
for n in sorted(resolved):
    fn = resolved[n]
    p = prof.get(fn, {})
    lines.append("%-46s %08X  size=%-6d callers=%d" % (n, fn, p.get('size', 0), len(p.get('callers', []))))
open(r"D:\Nesting\nestfab\re\internal_names.txt", "w", encoding='utf-8').write('\n'.join(lines))
print('\n'.join(lines))
