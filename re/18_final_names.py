"""Final naming: earliest tracer literal (plain, else '//'-stripped), then pool subtraction."""
import sys, re, json, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *
from capstone import CS_AC_READ, CS_AC_WRITE

IDENT = re.compile(r'^[A-Za-z_~][A-Za-z0-9_]*(::[A-Za-z_~][A-Za-z0-9_]*)*$')
NOISE = {'basic_string','vector','string','Local','Cloud','Order','Start','Keys','final',
         'intermediate','pqcs','timer','thread','winsock','iocp','cancel','close','mutex',
         'sha1','WVSH','external_number','geometry','group','order','nesting','source_version',
         'cns_force_cloud','DrawSVG','vertex','edge','Status','nested','Unknown','result'}
def identlike(s):
    return 3 <= len(s) <= 90 and bool(IDENT.match(s)) and s not in NOISE and not s.endswith('_')

REGMAP={}
for n,b in [('rcx','rcx'),('ecx','rcx'),('cx','rcx'),('cl','rcx'),('ch','rcx'),('rdx','rdx'),('edx','rdx'),
            ('dx','rdx'),('dl','rdx'),('dh','rdx'),('r8','r8'),('r8d','r8'),('r8w','r8'),('r8b','r8'),
            ('r9','r9'),('r9d','r9'),('r9w','r9'),('r9b','r9'),('rax','rax'),('eax','rax'),('ax','rax'),
            ('al','rax'),('rsp','rsp'),('esp','rsp'),('rbp','rbp'),('ebp','rbp'),('rsi','rsi'),('esi','rsi'),
            ('rdi','rdi'),('edi','rdi'),('rbx','rbx'),('ebx','rbx'),('r10','r10'),('r11','r11'),
            ('r12','r12'),('r13','r13'),('r14','r14'),('r15','r15')]:
    REGMAP[n]=b

def analyse(rva, limit=6000):
    delta=0; int_read=set(); xmm_read=set(); stk=set(); writes_xmm0=False; n=0; insts=[]
    for ins in disasm(rva, count=limit):
        n+=1; insts.append(ins); m=ins.mnemonic
        if m=='push': delta+=8
        elif m=='pop': delta-=8
        elif m in ('sub','add') and ins.operands and ins.operands[0].type==X86_OP_REG \
             and MD.reg_name(ins.operands[0].reg)=='rsp' and ins.operands[1].type==X86_OP_IMM:
            delta += ins.operands[1].imm if m=='sub' else -ins.operands[1].imm
        for op in ins.operands:
            if op.type==X86_OP_REG:
                nm2=MD.reg_name(op.reg)
                if nm2=='xmm0' and (op.access & CS_AC_WRITE): writes_xmm0=True
                if op.access & CS_AC_READ:
                    f=REGMAP.get(nm2) or (('xmm'+re.match(r'xmm(\d+)',nm2).group(1)) if nm2 and re.match(r'xmm(\d+)',nm2) else None)
                    if f in ('rcx','rdx','r8','r9'): int_read.add(f)
                    elif f and f.startswith('xmm') and int(f[3:])<4: xmm_read.add(f)
            elif op.type==X86_OP_MEM:
                base=MD.reg_name(op.mem.base) if op.mem.base else None
                f=REGMAP.get(base) or (('xmm'+re.match(r'xmm(\d+)',base).group(1)) if base and re.match(r'xmm(\d+)',base) else None)
                if op.access & CS_AC_READ:
                    if f in ('rcx','rdx','r8','r9'): int_read.add(f)
                    elif f and f.startswith('xmm') and int(f[3:])<4: xmm_read.add(f)
                    if f=='rsp' and op.mem.index==0:
                        d=op.mem.disp
                        if d>=delta+0x28 and (d-delta-0x28)%8==0: stk.add((d-delta-0x28)//8)
    return dict(nins=n, int_regs=sorted(int_read), xmm=sorted(xmm_read),
                stack_args=(max(stk)+1) if stk else 0,
                arity=len(int_read)+len(xmm_read)+((max(stk)+1) if stk else 0),
                ret_xmm=writes_xmm0, insts=insts)

def literals_in_order(rva, insts):
    first={}
    for ins in insts:
        for op in ins.operands:
            if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
                t=ins.address+ins.size+op.mem.disp
                s=STRS.get(t)
                if s and t not in first: first[t]=(ins.address,s)
    return [s for a,s in sorted(first.values(), key=lambda x:x[0])]

prof=load_prof(); exp_set=set(EXPORTS)
rows=[]
for rva in sorted(EXPORTS, key=lambda r: EXPORTS[r][0]):
    p=prof.get(rva,{}); a=analyse(rva); lits=literals_in_order(rva, a.pop('insts'))
    plain=[s for s in lits if identlike(s)]
    comm =[s[2:].strip() for s in lits if s.startswith('//') and identlike(s[2:].strip())]
    nm = plain[0] if plain else (comm[0] if comm else None)
    src=None
    for t,s in p.get('strings',[]):
        if (s.endswith('.cpp') or s.endswith('.hpp')) and 'boost' not in s and '\\' not in s and ':' not in s and '/' not in s:
            src=s; break
    callees_exp=sorted({c for c in p.get('callees',[]) if c in exp_set})
    rows.append(dict(ords=EXPORTS[rva], rva=rva, name=nm, size=p.get('size',0), src=src,
                     lits=lits[:6], alias=[s for s in plain+comm if s.startswith('CNS_')][:2],
                     **a, calls=len(p.get('callees',[])), callees_exp=callees_exp,
                     sem=[s for t,s in p.get('strings',[]) if len(s)>=6 and not identlike(s)
                          and not s.startswith('_Z') and 'basic_string' not in s][:8]))

# ---- pool subtraction: rodata identifier names not yet used ----
used=set(r['name'] for r in rows if r['name'])
pool=[s for r,s in sorted(STRS.items()) if 0x9AC000<=r<0x9AF000 and identlike(s)]
unused=[s for s in pool if s not in used and not s.startswith('CNS_')]
print("rodata name pool: %d ; used: %d ; unused: %d" % (len(pool), len(used), len(unused)))
print("\nUNUSED rodata identifiers (candidates for the unnamed exports):")
for s in unused: print("   ", s)

print("\nUNNAMED EXPORTS with their literal sequence:")
for r in rows:
    if not r['name']:
        print("  ord %-11s RVA %08X size=%-5d lits=%s" % (','.join(map(str,r['ords'])), r['rva'], r['size'], r['lits']))

json.dump(rows, open(r"D:\Nesting\nestfab\re\exports_table.json","w"), indent=1, ensure_ascii=False)
print("\nNAMED: %d / %d" % (sum(1 for r in rows if r['name']), len(rows)))
print("\nFINAL TABLE")
print("%-13s %-8s %-6s %-4s %-4s %-4s %s" % ("ordinals","RVA","size","ari","int","xmm","name"))
for r in sorted(rows, key=lambda r:(r['name'] or 'zzz', r['rva'])):
    print("%-13s %08X %-6d %-4d %-4d %-4d %s" % (','.join(map(str,r['ords'])), r['rva'], r['size'],
          r['arity'], len(r['int_regs']), len(r['xmm']), r['name'] or '?'))
