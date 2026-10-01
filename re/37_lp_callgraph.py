"""Robust full-binary call graph (independent of prof2), to decide whether the
   LP / pricing / Row classes are reachable from the nesting engine."""
import sys, json, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

# ---- full linear disassembly, collect calls ----
callers = collections.defaultdict(set)
ncall = 0
for nm, va, vs, pr, rs, ch in SEC:
    if not (ch & 0x20000000): continue
    for ins in MD.disasm(data[pr:pr+rs], va):
        if ins.mnemonic == 'call' and ins.operands and ins.operands[0].type == X86_OP_IMM:
            t = ins.operands[0].imm
            if t:
                o = owner(ins.address) or ins.address
                callers[t].add(o)
                ncall += 1
print("total call instructions scanned: %d ; distinct targets: %d" % (ncall, len(callers)))

prof = load_prof()
rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json", encoding='utf-8'))
name_of = {r['rva']: (r['name'] or '') for r in rows}
def nm(x): return name_of.get(x) or prof.get(x, {}).get('name') or ''

# constructor / use sites of interest
SITES = {
 'Prc::BoxPriceComputer ctor':   [0x4D9AD0, 0x7CA0D0],
 'Prc::HullPriceComputer ctor':  [0x4D9B00, 0x7CA140],
 'Prc::AlphaPriceComputer ctor': [0x4D9B30, 0x7CA1C0],
 'Prc::LinearCombinationPricer': [0x4D9CD0, 0x4D9DE0, 0x4D9F80, 0x7CA5C0],
 'Row::BasicDistancer ctor':     [0x136AE0],
 'Row::Squeezer ctor':           [0x138A20, 0x138BE0, 0x138CA0, 0x138D60],
 'Coin::CoinLP ctor':            [0x267760],
}
print("\n" + "="*100); print("CALLERS OF LP/PRICING/ROW CONSTRUCTORS (robust scan)"); print("="*100)
for label, addrs in SITES.items():
    print("\n  %s" % label)
    for a in addrs:
        cs = sorted(x for x in callers.get(a, []) if x != a)
        print("     %08X  <- %d caller(s): %s" % (a, len(cs),
              ', '.join('%08X(%s)' % (c, nm(c)) for c in cs[:8])))

# climb: who calls the callers?
print("\n" + "="*100); print("SECOND LEVEL (who calls the callers)"); print("="*100)
lvl1 = set()
for addrs in SITES.values():
    for a in addrs: lvl1 |= set(callers.get(a, set()))
lvl2 = collections.Counter()
for c in lvl1:
    for p in callers.get(c, set()): lvl2[p] += 1
for c, k in lvl2.most_common(30):
    print("   %08X x%-3d size=%-6s %-30s strings=%s" % (
        c, k, prof.get(c, {}).get('size'), nm(c), [s for _, s in prof.get(c, {}).get('strings', [])][:3]))
print("\n  level-1 set: %s" % ', '.join('%08X(%s)' % (x, nm(x)) for x in sorted(lvl1)))
