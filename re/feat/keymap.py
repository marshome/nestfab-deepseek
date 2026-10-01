"""Map serialization keys -> internal getter/setter offsets.

We parse the annotated dump (out_dis.txt, produced by dmp.py) for
  lea rdx, [rip + X]   STR:"<key>"
and take the last CALL in the following window.  That callee is the internal
getter/setter; disassemble it and read the [reg+disp] it touches.
"""
import sys, re, collections
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from capstone.x86 import *

lines = [''.join(c if 32 <= ord(c) < 127 else '.' for c in L)
         for L in open(REDIR + r'\feat\out_dis.txt', encoding='utf-8', errors='replace')]
callees = {}

for i, L in enumerate(lines):
    m = re.search(r'STR:"([^"]*)"', L)
    if not m:
        continue
    key = m.group(1)
    calls = []
    for j in range(i + 1, min(i + 14, len(lines))):
        c = re.search(r'CALL (?:sub_)?([0-9A-F]+)', lines[j])
        if c:
            calls.append(int(c.group(1), 16))
    if not calls:
        continue
    tgt = calls[-1]
    if tgt not in callees:
        callees[tgt] = key

def offsets_of(fn):
    """return list of (kind, op, [base+disp], src) for a small function"""
    res = []
    try:
        ins = list(disasm(fn, maxlen=400))
    except Exception:
        return res
    for i in ins:
        if len(i.operands) == 2 and i.mnemonic.startswith('mov'):
            d, s = i.operands
            if d.type == X86_OP_MEM and d.mem.base != 0 and d.mem.index == 0:
                bn = i.reg_name(d.mem.base)
                if bn in ('rcx', 'rdx', 'rsi', 'rdi', 'rbx', 'rbp'):
                    src = None
                    if s.type == X86_OP_REG:
                        src = i.reg_name(s.reg)
                    elif s.type == X86_OP_IMM:
                        src = hex(s.imm)
                    res.append(('%s[%s+0x%X]' % ({1: 'B', 2: 'W', 4: 'D', 8: 'Q'}.get(d.size, '?'), bn, d.mem.disp), src, i.address))
    return res

# group by key
bykey = collections.defaultdict(list)
for fn, key in callees.items():
    bykey[key].append(fn)

seen = {}
out = []
for key in sorted(bykey):
    for fn in sorted(bykey[key]):
        o = offsets_of(fn)
        # choose stores where base reg is the first arg (rcx) - most setters
        filt = [x for x in o if x[0][1:4] == 'rcx']
        out.append('%-38s  fn=0x%06X  %s' % (key, fn, '; '.join('%s<-%s' % (a, b) for a, b, c in (filt or o)[:6])))
open(REDIR + r'\feat\out_keymap.txt', 'w').write('\n'.join(out))
print('\n'.join(out))
