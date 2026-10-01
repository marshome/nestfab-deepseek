"""DECISIVE test: is the LP / pricing / Row machinery instantiated and reachable?
   Full-binary linear scan (independent of prof2.pkl) for
     (a) `lea r64,[rip+X]` targeting any Lp/Prc/Row/CoinLP vtable address point
     (b) 8-byte data words equal to those address points (both LE and halves-swapped)
"""
import sys, json, struct, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

vt = json.load(open(r"D:\Nesting\nestfab\re\vtables.json"))
WANT = ('Lp::', 'Prc::', 'Row::', 'Coin::')
tv = {k: v for k, v in vt.items() if v['demangled'].startswith(WANT)}
ap2name = {}
for k, v in tv.items():
    if v['vtable_rva'] is not None:
        ap2name[v['vtable_rva'] + 16] = v['demangled']
print("address points under test:")
for ap, n in sorted(ap2name.items()):
    print("   %08X  %s" % (ap, n))

# ---------- (a) full-binary linear disassembly scan ----------
print("\n" + "="*100); print("(a) `lea reg,[rip+X]` sites (full linear disasm of code sections)"); print("="*100)
hits = collections.defaultdict(list)
for nm, va, vs, pr, rs, ch in SEC:
    if not (ch & 0x20000000): continue
    for ins in MD.disasm(data[pr:pr+rs], va):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in ap2name:
                    hits[t].append((ins.address, ins.mnemonic, ins.op_str))
for ap in sorted(ap2name):
    hs = hits.get(ap, [])
    print("\n  %08X %-34s %d lea site(s)" % (ap, ap2name[ap], len(hs)))
    for a, m, o in hs[:8]:
        print("      %08X  %s %s   -> enclosing fn %s" % (a, m, o, ('%08X' % owner(a)) if owner(a) else '?'))

# ---------- (b) data words ----------
print("\n" + "="*100); print("(b) 8-byte data words equal to an address point"); print("="*100)
for i in range(0, len(data) - 8):
    v = struct.unpack_from('<Q', data, i)[0]
    sw = (struct.unpack_from('<I', data, i)[0] << 32) | struct.unpack_from('<I', data, i+4)[0]
    for val, how in ((v, 'LE'), (sw, 'swap32')):
        if val in ap2name:
            r = off2rva(i)
            print("  off %08X (rva %s) %-7s = %08X  %s" % (i, r and '%08X' % r, how, val, ap2name[val]))
