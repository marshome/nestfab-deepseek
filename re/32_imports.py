"""Identify import thunks by resolving `jmp qword ptr [rip+X]` to the IAT slots,
   then find the callers of the `acos` thunk (angle computation)."""
import sys, struct, collections, json
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

# IAT slot addresses from the import descriptors (derived in 02_exports_imports analysis)
IAT = {
 'KERNEL32!LoadLibraryA':0xB42328,'KERNEL32!GetProcAddress':0xB42330,
 'KERNEL32!VirtualProtect':0xB42338,'KERNEL32!VirtualAlloc':0xB42340,
 'KERNEL32!VirtualFree':0xB42348,
 'ADVAPI32!CryptGenRandom':0xB42358,
 'IPHLPAPI!GetAdaptersInfo':0xB42368,
 'winpthread!nanosleep':0xB42378,
 'msvcrt!acos':0xB42388,
 'PSAPI!GetProcessMemoryInfo':0xB42398,
 'USER32!MessageBoxA':0xB423A8,
 'WS2_32!bind':0xB423B8,
}
slot2name = {v:k for k,v in IAT.items()}

# find thunks: `jmp qword ptr [rip+disp]` whose target is one of the IAT slots
md = MD
thunks = {}
sec = [s for s in SEC if s[5] & 0x20000000]
for name, va, vs, pr, rs, ch in sec:
    code = data[pr:pr+rs]
    for ins in md.disasm(code, va):
        if ins.mnemonic == 'jmp' and ins.operands:
            op = ins.operands[0]
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in slot2name:
                    thunks[ins.address] = slot2name[t]
print("import thunks resolved: %d" % len(thunks))
for a, n in sorted(thunks.items()):
    print("   %08X  %s" % (a, n))

prof = load_prof()
print("\ncallers of each thunk (enclosing function RVA):")
for a, n in sorted(thunks.items(), key=lambda kv: kv[1]):
    callers = sorted({c for c, p in prof.items() if a in p.get('callees', [])})
    print("\n  %-34s thunk=%08X  callers=%d" % (n, a, len(callers)))
    for c in callers[:25]:
        p = prof.get(c, {})
        ss = [s for _, s in p.get('strings', [])][:2]
        print("      %08X size=%-6d %s" % (c, p.get('size', 0), ss))
    if len(callers) > 25: print("      ... +%d more" % (len(callers)-25))
