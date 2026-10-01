import sys, os, json
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from cl_util import *

OUT = r"D:\Nesting\nestfab\re\dis"
os.makedirs(OUT, exist_ok=True)

def dump(rva, fn=None, maxn=100000):
    p = PROF.get(rva)
    if not p or p.get('start') != rva:
        p = None
    end = p['end'] if p else rva + 4096
    fn = fn or f"{rva:06x}"
    path = os.path.join(OUT, fn + ".txt")
    lines = []
    lines.append(f"### fn {rva:#x} name={nm(rva)} end={end:#x} size={end-rva}")
    if p:
        lines.append("STRINGS: " + ", ".join(f"{hex(a)}:{s!r}" for a, s in p.get('strings', [])))
        lines.append("CALLERS: " + ", ".join(f"{hex(c)}:{nm(owner(c))}" for c in (p.get('callers') or [])))
        lines.append("CALLEES: " + ", ".join(f"{hex(c)}:{nm(owner(c))}" for c in sorted(set(p.get('callees') or []))))
    lines.append("")
    n = 0
    for ins in disasm(rva, maxlen=end - rva):
        annot = ''
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                a = ins.address + ins.size + op.mem.disp
                if a in STRS:
                    annot += '  ; "%s"' % STRS[a].replace('\n', '\\n')[:110]
                else:
                    annot += '  ; DATA %#x' % a
        if ins.mnemonic == 'call' or ins.mnemonic == 'jmp':
            try:
                t = int(ins.op_str, 16)
                o = owner(t)
                annot += '  ; -> %s %s' % (hex(t), nm(o) if o else '')
            except Exception:
                pass
        lines.append(f"  {ins.address:08x}  {ins.bytes.hex():<20s} {ins.mnemonic:7s} {ins.op_str}{annot}")
        n += 1
        if n > maxn: break
    open(path, 'w', encoding='utf-8').write("\n".join(lines))
    return path, n

TASKS = [
 (0x26a60, 'cloudengine_run'),
 (0x2ab0,  'launch_local'),
 (0x3310,  'launch_limited_local'),
 (0x3360,  'launch_estimate_local'),
 (0x6100,  'launch_computation'),
 (0x104d0, 'wait_termination'),
 (0x10650, 'wait_next_solution'),
 (0x107e0, 'get_computation_status'),
 (0x10880, 'cancel_computation'),
 (0x10920, 'terminate_computation'),
 (0xb540,  'async_cancel_all'),
 (0xc010,  'getpcid'),
 (0xd430,  'unlock_lo'),
 (0xe180,  'unlock_sntl'),
 (0xe1f0,  'unlock_oxy'),
 (0xe260,  'unlock_pcid'),
]
for rva, fn in TASKS:
    path, n = dump(rva, fn)
    print(f"{fn:26s} {rva:#08x} nins={n} -> {path}")
