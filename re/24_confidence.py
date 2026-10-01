"""Independent confidence check for recovered names:
   the chosen literal must be loaded into an argument register and passed to a
   dbg::symlog tracer (0x64AEA0 / 0x64ABF0 / 0x64D9C0 / 0x64ACE0) before any
   other call in the function."""
import sys, json, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

TRACERS = {0x64AEA0, 0x64ABF0, 0x64D9C0, 0x64ACE0, 0x978750, 0x990E80}
# also treat any function that itself references "-> " as a tracer
prof = load_prof()
for b, p in prof.items():
    names = [s for _, s in p.get('strings', [])]
    if '-> ' in names: TRACERS.add(b)
print("tracer functions:", len(TRACERS))

rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json"))
hi = mid = lo = 0
bad = []
for r in rows:
    if not r['name']:
        continue
    insts = list(disasm(r['rva'], count=120))
    # find the literal
    tgt = None
    for ins in insts:
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if STRS.get(t) == r['name']:
                    tgt = ins.address; break
        if tgt: break
    if tgt is None:
        lo += 1; bad.append((r['name'], r['rva'], 'literal-not-in-first-120-insns')); continue
    # is it passed to a tracer before any other call?
    idx = next(i for i, ins in enumerate(insts) if ins.address == tgt)
    verdict = 'no-tracer-call-after'
    for ins in insts[idx:idx + 8]:
        if ins.mnemonic == 'call' and ins.operands and ins.operands[0].type == X86_OP_IMM:
            verdict = 'tracer-ok' if ins.operands[0].imm in TRACERS else 'other-call-first'
            break
    # is any non-tracer call made before the literal?
    pre = [ins for ins in insts[:idx] if ins.mnemonic == 'call' and ins.operands
           and ins.operands[0].type == X86_OP_IMM and ins.operands[0].imm not in TRACERS]
    if verdict == 'tracer-ok' and not pre: hi += 1
    elif verdict == 'tracer-ok': mid += 1
    else: lo += 1; bad.append((r['name'], r['rva'], verdict))

print("\nHIGH confidence (literal -> tracer, no earlier non-tracer call): %d" % hi)
print("MED  confidence (literal -> tracer, but an earlier call exists) : %d" % mid)
print("LOW  confidence                                                 : %d" % lo)
for n, rv, v in bad: print("   LOW %-52s %08X  %s" % (n, rv, v))
print("\ntotal named: %d / %d" % (hi + mid + lo, len(rows)))
