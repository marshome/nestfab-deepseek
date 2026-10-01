"""Compact per-export summary: args used, this-stores, strings, callees, tail."""
import sys, json, collections
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from capstone.x86 import *

EX = json.load(open(REDIR + r'\exports_named.json'))
ORD = {}
for e in EX:
    for o in e['ords']:
        ORD[o] = e
FNAME = {}
for e in EX:
    if e['name']:
        FNAME.setdefault(e['rva'], set()).add(e['name'].rstrip('?'))
P = load_prof()
for r, f in P.items():
    if f.get('name'):
        FNAME.setdefault(r, set()).add(f['name'].rstrip('?'))

STRS_BY_FN = {}
for r, f in P.items():
    STRS_BY_FN[r] = f.get('strings') or []


def summary(rva, name=None):
    f = P.get(rva)
    ins = list(disasm(rva))
    out = []
    out.append('### %s @ 0x%X  size=%d nins=%d' % (name or ','.join(sorted(FNAME.get(rva, ['?']))), rva,
                                                  f['size'] if f else -1, len(ins)))
    # arg registers read before being written
    argregs = ('edx', 'r8d', 'r9d', 'ecx', 'r8', 'r9')
    used = collections.Counter()
    xmm = collections.Counter()
    written = set()
    for i in ins[:60]:
        for op in i.operands:
            if op.type == X86_OP_REG:
                n = i.reg_name(op.reg)
                if i.operands[0].type == X86_OP_REG and i.operands[0].reg == op.reg and i.mnemonic.startswith(('mov', 'lea', 'xor', 'pxor', 'cvtsi')):
                    written.add(n)
                elif n in argregs or n in ('xmm1', 'xmm2', 'xmm3', 'xmm0'):
                    if n not in written:
                        used[n] += 1
    out.append('    arg-regs: %s' % dict(used))
    # this pointer candidate
    thisreg = None
    for i in ins[:12]:
        if i.mnemonic == 'mov' and len(i.operands) == 2:
            d, s = i.operands
            if d.type == X86_OP_REG and s.type == X86_OP_REG and s.reg == X86_REG_RCX:
                thisreg = i.reg_name(d.reg)
                break
    if thisreg is None:
        thisreg = 'rcx'
    stores = []
    for i in ins:
        if len(i.operands) == 2 and i.mnemonic.startswith('mov') and i.operands[0].type == X86_OP_MEM:
            d = i.operands[0]
            if d.mem.base and i.reg_name(d.mem.base) == thisreg and d.mem.index == 0:
                s = i.operands[1]
                v = i.reg_name(s.reg) if s.type == X86_OP_REG else (hex(s.imm) if s.type == X86_OP_IMM else '?')
                stores.append(('%s[%s+0x%X]' % ({1: 'B', 2: 'W', 4: 'D', 8: 'Q'}.get(d.size, '?'), thisreg, d.mem.disp), v))
    out.append('    this=%s stores: %s' % (thisreg, '; '.join('%s<-%s' % t for t in stores) or '(none)'))
    out.append('    strings: %s' % '; '.join('%s@0x%X' % (s[:60], r) for r, s in (f['strings'] if f else [])[:12]))
    calls = [c for c in (f['callees'] if f else [])]
    out.append('    callees: %s' % ', '.join('%s(0x%X)' % (','.join(sorted(FNAME.get(c, ['sub']))), c) for c in calls[:14]))
    out.append('    TAIL:')
    for i in ins[-14:]:
        ann = []
        for op in i.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = i.address + i.size + op.mem.disp
                if t in STRS:
                    ann.append('STR:"%s"' % STRS[t][:40])
        out.append('      %06X %-40s %s' % (i.address, i.mnemonic + ' ' + i.op_str, ' '.join(ann)))
    return '\n'.join(out)


if __name__ == '__main__':
    res = []
    for a in sys.argv[1:]:
        if '=' in a:
            n, r = a.split('=')
            res.append(summary(int(r, 0), n))
        else:
            res.append(summary(int(a, 0)))
    txt = '\n'.join(res)
    open(REDIR + r'\feat\out_sum.txt', 'w', newline='\n').write(txt)
    print(txt)
