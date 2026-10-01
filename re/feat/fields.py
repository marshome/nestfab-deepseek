import sys, json, re, collections
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

def analyze(rva):
    """find base regs holding rcx at entry, then stores through them"""
    ins = list(disasm(rva))
    base = {}   # reg -> True if currently holds the this-pointer
    init = None
    stores = []
    # first pass: which reg gets rcx in the prologue
    cands = set()
    for i in ins[:40]:
        if i.mnemonic == 'mov' and len(i.operands) == 2:
            d, s = i.operands
            if d.type == X86_OP_REG and s.type == X86_OP_REG and s.reg == X86_REG_RCX:
                cands.add(i.reg_name(d.reg))
    for i in ins:
        if i.mnemonic.startswith('mov') and len(i.operands) == 2:
            d, s = i.operands
            if d.type == X86_OP_MEM and d.mem.base != 0:
                bn = i.reg_name(d.mem.base)
                if bn in cands and d.mem.index == 0:
                    sz = {1: 'B', 2: 'W', 4: 'D', 8: 'Q'}.get(d.size, str(d.size))
                    val = None
                    if s.type == X86_OP_IMM:
                        val = hex(s.imm)
                    elif s.type == X86_OP_REG:
                        val = i.reg_name(s.reg)
                    stores.append((i.address, '%s[%s+0x%X]' % (sz, bn, d.mem.disp), val))
    return cands, stores

if __name__ == '__main__':
    out = []
    for rva in sorted(EX and {e['rva'] for e in EX}):
        n = sorted(FNAME.get(rva, ['?']))
        if not any(k in n[0] for k in ('Set', 'Get', 'Add', 'Force', 'Create')):
            continue
        c, st = analyze(rva)
        if not st:
            continue
        out.append('0x%06X %-42s bases=%s' % (rva, ','.join(n)[:42], sorted(c)))
        for a, dst, val in st:
            out.append('        %06X  %-22s = %s' % (a, dst, val))
    open(REDIR + r'\feat\out_fields.txt', 'w', newline='\n').write('\n'.join(out))
    print('\n'.join(out))
