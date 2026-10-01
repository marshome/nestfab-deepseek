import sys, json, re
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from capstone.x86 import *

EX = json.load(open(REDIR + r'\exports_named.json'))
FNAME = {}
for e in EX:
    if e['name']:
        FNAME.setdefault(e['rva'], set()).add(e['name'].rstrip('?'))
P = load_prof()
for r, f in P.items():
    if f.get('name'):
        FNAME.setdefault(r, set()).add(f['name'].rstrip('?'))

# __func__ string -> maybe a function name
def note(t):
    s = []
    if t in STRS:
        s.append('STR:"%s"' % STRS[t][:70])
    if t in FNAME:
        s.append('FN:' + ','.join(sorted(FNAME[t])))
    o = owner(t)
    if o is not None and o in FNAME:
        s.append('infn@0x%X:' % o + ','.join(sorted(FNAME[o])))
    return ' ; '.join(s)

def show(rva, lo=None, hi=None, maxn=100000):
    ext = func_extent(rva)
    print('=== 0x%X (0x%X-0x%X) %s' % (rva, ext[0], ext[1], sorted(FNAME.get(rva, []))))
    n = 0
    for ins in disasm(rva):
        if lo is not None and ins.address < lo: continue
        if hi is not None and ins.address >= hi: break
        n += 1
        if n > maxn: break
        ann = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ann.append(note(t))
            elif op.type == X86_OP_IMM and op.imm > 0x1000 and ins.mnemonic.startswith('call'):
                t = norm(op.imm) or op.imm
                ann.append('CALL ' + (','.join(sorted(FNAME[t])) if t in FNAME else 'sub_%X' % t))
        print('  %06X  %-42s %s' % (ins.address, ins.mnemonic + ' ' + ins.op_str, ' | '.join(a for a in ann if a)))

if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 1:
        show(int(a[0], 0))
    elif len(a) == 3:
        show(int(a[0], 0), int(a[1], 0), int(a[2], 0))
    else:
        for x in a:
            show(int(x, 0))
