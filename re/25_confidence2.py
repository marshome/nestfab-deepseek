"""Refined confidence: does the function anywhere pass its recovered name (or "// "+name)
   as an argument to a dbg tracer?"""
import sys, json, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

prof = load_prof()
TRACERS = {0x64AEA0, 0x64ABF0, 0x64D9C0, 0x64ACE0, 0x978750, 0x990E80}
for b, p in prof.items():
    if '-> ' in [s for _, s in p.get('strings', [])]: TRACERS.add(b)

rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json"))
res = collections.Counter(); det=[]
for r in rows:
    if not r['name']:
        res['unnamed'] += 1; continue
    insts = list(disasm(r['rva']))
    # map: address of an instruction that loads a RIP literal -> (literal RVA, string)
    loads = {}
    for ins in insts:
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                loads[ins.address] = t
    # find tracer calls and look back up to 12 insns for a load of name / "// "+name
    ok = False; how = None
    for i, ins in enumerate(insts):
        if ins.mnemonic == 'call' and ins.operands and ins.operands[0].type == X86_OP_IMM \
           and ins.operands[0].imm in TRACERS:
            for j in range(max(0, i - 14), i):
                t = loads.get(insts[j].address)
                if t is None: continue
                s = STRS.get(t)
                if s == r['name']:
                    ok = True; how = 'name->tracer'; break
                if s == '// ' + r['name'] or s == '//' + r['name']:
                    ok = True; how = 'comment->tracer'; break
            if ok: break
    res[how or 'NOT-tracer-linked'] += 1
    if not ok: det.append((r['name'], r['rva'], r['lits'][:3]))

print("name passed to a tracer            :", res['name->tracer'])
print("'// name' passed to a tracer       :", res['comment->tracer'])
print("name not linked to a tracer        :", res['NOT-tracer-linked'])
print("unnamed                            :", res['unnamed'])
print()
for n, rv, l in det: print("   %-52s %08X  lits=%s" % (n, rv, l))
