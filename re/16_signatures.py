"""Final export table: name (earliest tracer literal), signature (Win64 ABI), call graph, strings."""
import sys, re, collections, json
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *
from capstone import CS_AC_READ, CS_AC_WRITE

IDENT = re.compile(r'^[A-Za-z_~][A-Za-z0-9_]*(::[A-Za-z_~][A-Za-z0-9_]*)*$')
NOISE = {'basic_string','vector','string','Local','Cloud','Order','Start','Keys','final',
         'intermediate','pqcs','timer','thread','winsock','iocp','cancel','close','mutex',
         'sha1','WVSH','AUATUWVSH','external_number','geometry','group','order','nesting',
         'source_version','cns_force_cloud','typeinfo','DrawSVG','vertex','edge'}
def identlike(s):
    return 3 <= len(s) <= 90 and bool(IDENT.match(s)) and s not in NOISE

REGMAP = {}
for n,base in [('rcx','rcx'),('ecx','rcx'),('cx','rcx'),('cl','rcx'),('ch','rcx'),
               ('rdx','rdx'),('edx','rdx'),('dx','rdx'),('dl','rdx'),('dh','rdx'),
               ('r8','r8'),('r8d','r8'),('r8w','r8'),('r8b','r8'),
               ('r9','r9'),('r9d','r9'),('r9w','r9'),('r9b','r9'),
               ('rax','rax'),('eax','rax'),('ax','rax'),('al','rax'),
               ('rsp','rsp'),('esp','rsp'),('rbp','rbp'),('ebp','rbp'),
               ('rsi','rsi'),('esi','rsi'),('rdi','rdi'),('edi','rdi'),
               ('rbx','rbx'),('ebx','rbx'),('r10','r10'),('r11','r11'),
               ('r12','r12'),('r13','r13'),('r14','r14'),('r15','r15')]:
    REGMAP[n] = base
def rf(reg):
    n = MD.reg_name(reg)
    if n is None: return None
    m = re.match(r'xmm(\d+)', n)
    if m: return 'xmm'+m.group(1)
    return REGMAP.get(n)

def analyse(rva, limit=4000):
    delta = 0
    int_read = set(); xmm_read = set(); stack_args = set()
    writes_xmm0 = False
    n = 0
    insts = []
    for ins in disasm(rva, count=limit):
        n += 1; insts.append(ins)
        m = ins.mnemonic
        if m == 'push': delta += 8
        elif m == 'pop': delta -= 8
        elif m in ('sub','add') and ins.operands and ins.operands[0].type == X86_OP_REG \
             and rf(ins.operands[0].reg) == 'rsp' and ins.operands[1].type == X86_OP_IMM:
            delta += ins.operands[1].imm if m == 'sub' else -ins.operands[1].imm
        for op in ins.operands:
            if op.type == X86_OP_REG and (op.access & CS_AC_WRITE) and rf(op.reg) == 'xmm0':
                writes_xmm0 = True
            if op.type == X86_OP_MEM:
                b = rf(op.mem.base)
                if b == 'rsp' and op.mem.index == 0 and (op.access & CS_AC_READ):
                    d = op.mem.disp
                    if d >= delta + 0x28 and (d - delta - 0x28) % 8 == 0:
                        stack_args.add((d - delta - 0x28)//8)
                if op.access & CS_AC_READ and op.mem.base:
                    f = rf(op.mem.base)
                    if f in ('rcx','rdx','r8','r9'): int_read.add(f)
                    elif f and f.startswith('xmm') and int(f[3:]) < 4: xmm_read.add(f)
            elif op.type == X86_OP_REG and (op.access & CS_AC_READ):
                f = rf(op.reg)
                if f in ('rcx','rdx','r8','r9'): int_read.add(f)
                elif f and f.startswith('xmm') and int(f[3:]) < 4: xmm_read.add(f)
    return dict(nins=n, int_regs=sorted(int_read), xmm=sorted(xmm_read),
                stack_args=(max(stack_args)+1) if stack_args else 0,
                arity=len(int_read)+len(xmm_read)+((max(stack_args)+1) if stack_args else 0),
                ret_xmm=writes_xmm0, insts=insts)

def tracer_name(rva, p, insts):
    """the function's own __func__ string = the identifier-like literal whose
       RIP-relative load occurs EARLIEST in the function body."""
    first = {}
    for ins in insts:
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                s = STRS.get(t)
                if s and identlike(s) and t not in first:
                    first[t] = ins.address
    if not first: return None, []
    ordered = sorted(first.items(), key=lambda kv: kv[1])
    cands = [STRS[t] for t, _ in ordered]
    # Prefer the earliest; if a "CNS_x" appears within the first 3 literals alongside "x", keep CNS_x
    top = cands[:3]
    for s in top:
        if s.startswith('CNS_') and s[4:] in cands: return s, cands
    return cands[0], cands

prof = load_prof()
exp_set = set(EXPORTS)
rows = []
for rva in sorted(EXPORTS, key=lambda r: EXPORTS[r][0]):
    p = prof.get(rva, {})
    a = analyse(rva)
    nm, cands = tracer_name(rva, p, a.pop('insts'))
    src = None
    for r, s in p.get('strings', []):
        if (s.endswith('.cpp') or s.endswith('.hpp')) and 'boost' not in s and '\\' not in s and ':' not in s and '/' not in s:
            src = s; break
    # which other EXPORTS does it call
    callees_exp = sorted({c for c in p.get('callees', []) if c in exp_set})
    sem = [s for r, s in p.get('strings', [])
           if len(s) >= 6 and not identlike(s) and not s.startswith('_Z')
           and not re.fullmatch(r'[A-Za-z0-9_ ]{0,5}', s)]
    rows.append(dict(ords=EXPORTS[rva], rva=rva, name=nm, cands=cands, size=p.get('size',0),
                     src=src, **a, calls=len(p.get('callees', [])), ind=p.get('ind',0),
                     callees_exp=callees_exp, sem=sem[:8]))

json.dump(rows, open(r"D:\Nesting\nestfab\re\exports_table.json", "w"), indent=1, ensure_ascii=False)
print("%-13s %-8s %-6s %-4s %-4s %-4s %-5s %s" % ("ordinals","RVA","size","ari","int","xmm","stk","name"))
for r in rows:
    print("%-13s %08X %-6d %-4d %-4d %-4d %-5d %s%s" %
          (','.join(map(str, r['ords'])), r['rva'], r['size'], r['arity'],
           len(r['int_regs']), len(r['xmm']), r['stack_args'], r['name'] or '?',
           ('   cands=' + str(r['cands'][:3])) if not r['name'] and r['cands'] else ''))
print("\nrows: %d ; named: %d" % (len(rows), sum(1 for r in rows if r['name'])))
print("names unique: %d / %d" % (len(set(r['name'] for r in rows if r['name'])), sum(1 for r in rows if r['name'])))
