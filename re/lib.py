"""Shared helper library for analysing libcns_dump_64.dll.

Usage:
    import sys; sys.path.insert(0, r"D:/Nesting/nestfab/re")
    from lib import *

Everything in this binary is RVA-addressed *inside the file*:
    file offset == RVA inside section 'BAB0' (VA 0x1000, raw ptr 0x1000)
    rva2off() / off2rva() handle all sections.
ImageBase = 0x6B4C0000.  Pointers found in data may be either plain RVAs
(this is a memory dump, so most RTTI/vtable pointers have been rebased to
absolute VAs) - use norm() to normalise either form to an RVA.
"""
import pefile, struct, re, collections, pickle, bisect, json

DLL   = r"D:\Nesting\nestfab\libcns_dump_64.dll"
REDIR = r"D:\Nesting\nestfab\re"

data = open(DLL, 'rb').read()
pe   = pefile.PE(DLL, fast_load=False)
IB   = pe.OPTIONAL_HEADER.ImageBase          # 0x6B4C0000
SEC  = [(s.Name.rstrip(b'\0').decode('latin1'), s.VirtualAddress,
         max(s.Misc_VirtualSize, s.SizeOfRawData), s.PointerToRawData,
         s.SizeOfRawData, s.Characteristics) for s in pe.sections]

def rva2off(rva):
    for n, va, vs, pr, rs, ch in SEC:
        if va <= rva < va + vs:
            return pr + (rva - va)
    return None

def off2rva(off):
    for n, va, vs, pr, rs, ch in SEC:
        if pr <= off < pr + rs:
            return va + (off - pr)
    return None

def norm(v):
    """normalise a stored 64-bit pointer to an RVA (or None)"""
    if v == 0:
        return None
    for c in (v, v - IB):
        if 0x1000 <= c < 0x2000000 and rva2off(c) is not None:
            return c
    return None

def get(off, n):
    return data[off:off + n]

def u32(off):  return struct.unpack_from('<I', data, off)[0]
def u64(off):  return struct.unpack_from('<Q', data, off)[0]

# ---- all C strings, keyed by RVA ----
def load_strings(minlen=3):
    out = {}
    cur = bytearray(); start = 0
    for i, b in enumerate(data):
        if 32 <= b < 127:
            if not cur: start = i
            cur.append(b)
        else:
            if len(cur) >= minlen:
                r = off2rva(start)
                if r is not None: out[r] = cur.decode('latin1')
            cur = bytearray()
    return out
STRS = load_strings()

# ---- function table from .pdata ----
def load_funcs():
    rva = pe.OPTIONAL_HEADER.DATA_DIRECTORY[3].VirtualAddress
    size = pe.OPTIONAL_HEADER.DATA_DIRECTORY[3].Size
    o = rva2off(rva)
    f = []
    for i in range(size // 12):
        b, e, u = struct.unpack_from('<III', data, o + i * 12)
        if b: f.append((b, e, u))
    f.sort()
    return f
FUNCS = load_funcs()
FSTARTS = [f[0] for f in FUNCS]

def owner(rva):
    """RVA of the function containing rva (per .pdata), or None"""
    i = bisect.bisect_right(FSTARTS, rva) - 1
    if i >= 0 and FUNCS[i][0] <= rva < FUNCS[i][1]:
        return FUNCS[i][0]
    return None

def func_extent(rva):
    for b, e, u in FUNCS:
        if b == rva: return (b, e)
    return None

# ---- exports (ordinal -> rva; names were stripped by the packer) ----
EXPORTS = collections.OrderedDict()          # rva -> [ordinals]
for s in sorted(pe.DIRECTORY_ENTRY_EXPORT.symbols, key=lambda x: x.ordinal):
    EXPORTS.setdefault(s.address, []).append(s.ordinal)

# ---- xref profile: written by 12_xref.py ----
def load_prof():
    """The profile, with the `callers` lists de-self-referenced on load.

    **74% OF THE FUNCTIONS IN THIS PROFILE LIST THEMSELVES AS THEIR OWN CALLER**, and the cause is a granularity mismatch:

        the `callees` list holds CALL-SITE ADDRESSES, not callee function starts -- 0x1050's begins 0x109b 0x10c9 0x1120, all INSIDE 0x1050 itself
        the reverse pass in re/12_xref.py attributes each call to `owner(target)`, so a call that stays within one function is attributed to that function

    **so a function appears to call itself whenever it has an intra-function reference**, which is why the ratio is a prevalence and not one bad entry. **The two
    lists are also different sizes for the same reason** -- 128184 callee edges against 77941 caller edges -- because the reverse pass drops targets whose owner
    cannot be resolved.

    **SO A SELF-REFERENCE IS REMOVED AND NOTHING ELSE IS TOUCHED.** A function calling itself is information for no question this project asks -- call-graph ranking,
    reachability, who-references-this -- and it is what made 0x62F280 look like the module's most-called function with 10418 callers while its own list holds 5209.
    **The honest fix is a profile whose `callees` names FUNCTIONS, and that needs the generator; this makes the existing data usable in the meantime without
    pretending it is more than it is.**
    """
    profile = pickle.load(open(REDIR + r"\prof2.pkl", "rb"))
    for start, entry in profile.items():
        callers = entry.get("callers")
        if callers and start in callers:
            entry["callers"] = [c for c in callers if c != start]
    return profile

def get_prof():
    return load_prof()

# ---- capstone ----
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP
MD = Cs(CS_ARCH_X86, CS_MODE_64)
MD.detail = True

def disasm(rva, maxlen=None, count=None):
    """yield instructions of the function starting at rva"""
    ext = func_extent(rva)
    end = ext[1] if ext else rva + 4096
    if maxlen: end = min(end, rva + maxlen)
    o = rva2off(rva)
    if o is None: return
    n = 0
    for ins in MD.disasm(data[o:o + (end - rva)], rva):
        yield ins
        n += 1
        if count and n >= count: return

def rip_targets(rva):
    """set of RVAs referenced by RIP-relative operands inside function rva"""
    t = set()
    for ins in disasm(rva):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t.add(ins.address + ins.size + op.mem.disp)
    return t

def strings_of(rva):
    """[(rva, string)] referenced by the function at rva"""
    return sorted((t, STRS[t]) for t in rip_targets(rva) if t in STRS)
