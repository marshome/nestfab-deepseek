import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from g1_names import NAMES
from capstone.x86 import *

P = load_prof()
_pl = {}
for rva, v in P.items():
    _pl[rva] = v

def label_fn(t):
    if t in NAMES:
        return NAMES[t]
    v = _pl.get(t)
    if v and v.get('name'):
        return v['name']
    for f in (t,):
        o = owner(f)
        if o is not None and o in NAMES:
            return 'sub_%x<%s>' % (f, NAMES[o])
    if t in EXPORTS:
        return 'EXPORT_%x' % t
    return 'sub_%x' % t

def annot(t):
    """annotate a target address (rip target)"""
    if t in STRS:
        return 'STR@%x %r' % (t, STRS[t][:90])
    lbl = label_fn(t)
    if lbl.startswith('sub_') or 'EXPORT' in lbl:
        # maybe vtable / data
        tt = norm(u64(rva2off(t))) if rva2off(t) and rva2off(t) + 8 <= len(data) else None
        return '%s [%s]' % (lbl, ('->' + label_fn(tt)) if tt else '?')
    return lbl

def dump(rva, count=None, maxlen=None, flen=True):
    ext = func_extent(rva)
    print('#### %s  rva=%s size=%s ext=%s' % (NAMES.get(rva) or _pl.get(rva, {}).get('name'), hex(rva),
          _pl.get(rva, {}).get('size'), (hex(ext[0]), hex(ext[1])) if ext else None))
    for ins in disasm(rva, maxlen=maxlen, count=count):
        s = '%-8x %-30s' % (ins.address, ins.mnemonic + ' ' + ins.op_str)
        notes = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                notes.append(annot(t))
            elif op.type == X86_OP_IMM and ins.mnemonic in ('call',):
                notes.append(label_fn(op.imm))
        if notes:
            s += '   ; ' + ' | '.join(notes)
        print(s)
