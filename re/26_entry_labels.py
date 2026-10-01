"""Rigorous name recovery: take the argument of the FIRST dbg tracer call in the function.
   Strip a leading '//' (the codebase uses both 'Name' and '// Name' entry labels)."""
import sys, json, re, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

prof = load_prof()
rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json"))

TRACERS = {0x64AEA0, 0x64ABF0, 0x64D9C0, 0x64ACE0, 0x978750, 0x990E80}
for b, p in prof.items():
    if '-> ' in [s for _, s in p.get('strings', [])]: TRACERS.add(b)

ID = re.compile(r'^(?://\s*)?([A-Za-z_~][A-Za-z0-9_]*(::[A-Za-z_~][A-Za-z0-9_]*)*)$')
NOISE = {'Launching local engines','Order valid','Start','Keys'}

def entry_label(rva, maxscan=400):
    insts = list(disasm(rva, count=maxscan))
    for i, ins in enumerate(insts):
        if ins.mnemonic == 'call' and ins.operands and ins.operands[0].type == X86_OP_IMM \
           and ins.operands[0].imm in TRACERS:
            # walk back: literal loaded into rcx (1st arg) or rdx (2nd)
            for j in range(i-1, max(0, i-18), -1):
                pv = insts[j]
                if pv.mnemonic != 'lea': continue
                if not pv.operands: continue
                dst = pv.operands[0]; src = pv.operands[1]
                if dst.type != X86_OP_REG: continue
                dname = MD.reg_name(dst.reg)
                if dname not in ('rcx','rdx'): continue
                if src.type != X86_OP_MEM or src.mem.base != X86_REG_RIP: continue
                t = pv.address + pv.size + src.mem.disp
                s = STRS.get(t)
                if not s: continue
                if s in NOISE: continue
                m = ID.match(s)
                if m: return m.group(1), s, ins.address, pv.address
    return None, None, None, None

changes = []
for r in rows:
    nm, raw, cat, loadat = entry_label(r['rva'])
    old = r['name']
    status = 'same' if nm == old else ('NEW' if nm else 'none')
    if status != 'same':
        changes.append((r['rva'], ','.join(map(str, r['ords'])), old, nm, raw, cat))

print("recovered %d names from first-tracer-call rule" % sum(1 for r in rows if entry_label(r['rva'])[0]))
print("\nDIFFERENCES vs previous rule (%d):" % len(changes))
for rva, ords, old, new, raw, cat in changes:
    print("  ord %-11s %08X  %-42s -> %-42s  (label=%r tracer=%s)" % (ords, rva, old or '?', new or '?', raw, cat and '%08X'%cat))

# apply
for r in rows:
    nm, raw, cat, loadat = entry_label(r['rva'])
    if nm:
        r['name'] = nm; r['label'] = raw; r['tracer'] = cat
json.dump(rows, open(r"D:\Nesting\nestfab\re\exports_table.json","w"), indent=1, ensure_ascii=False)
print("\nnamed after update: %d / %d" % (sum(1 for r in rows if r['name']), len(rows)))
dups = collections.Counter(r['name'] for r in rows if r['name'])
print("names shared by >1 export (C++ overloads):")
for k,v in dups.most_common():
    if v>1: print("   %-46s %d  RVAs=%s" % (k, v, ['%X'%r['rva'] for r in rows if r['name']==k]))
