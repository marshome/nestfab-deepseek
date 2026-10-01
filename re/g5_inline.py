import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from g1_names import NAMES
from capstone.x86 import *

P = load_prof()

P32 = {'eax': 'rax', 'ebx': 'rbx', 'ecx': 'rcx', 'edx': 'rdx', 'esi': 'rsi', 'edi': 'rdi',
       'r8d': 'r8', 'r9d': 'r9', 'r10d': 'r10', 'r11d': 'r11', 'r12d': 'r12', 'r13d': 'r13',
       'r14d': 'r14', 'r15d': 'r15'}
P16 = {'ax': 'rax', 'bx': 'rbx', 'cx': 'rcx', 'dx': 'rdx', 'si': 'rsi', 'di': 'rdi',
       'r8w': 'r8', 'r9w': 'r9', 'r10w': 'r10', 'r11w': 'r11', 'r12w': 'r12', 'r13w': 'r13',
       'r14w': 'r14', 'r15w': 'r15'}
P8 = {'al': 'rax', 'bl': 'rbx', 'cl': 'rcx', 'dl': 'rdx', 'sil': 'rsi', 'dil': 'rdi'}


def inline_strings(rva, verbose=False):
    """heuristically reconstruct inline-built string literals inside one function"""
    regval = {}
    buf = {}
    out = []
    for ins in disasm(rva):
        m, ops = ins.mnemonic, ins.operands
        if m == 'movabs' and len(ops) == 2 and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_IMM:
            regval[ins.reg_name(ops[0].reg)] = (ops[1].imm & ((1 << 64) - 1)).to_bytes(8, 'little')
        elif m == 'mov' and len(ops) == 2 and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_IMM:
            rn = ins.reg_name(ops[0].reg)
            n = {'eax': 4, 'ebx': 4, 'ecx': 4, 'edx': 4, 'esi': 4, 'edi': 4}.get(rn)
            if rn in P32:
                regval[P32[rn]] = (ops[1].imm & 0xffffffff).to_bytes(4, 'little')
            elif rn in P16:
                regval[P16[rn]] = (ops[1].imm & 0xffff).to_bytes(2, 'little')
            elif rn in P8:
                regval[P8[rn]] = (ops[1].imm & 0xff).to_bytes(1, 'little')
        elif m == 'mov' and len(ops) == 2 and ops[0].type == X86_OP_MEM and ops[1].type == X86_OP_REG:
            base = ins.reg_name(ops[0].mem.base)
            if base == 'rax':
                v = regval.get(ins.reg_name(ops[1].reg))
                if v:
                    sz = ops[0].size
                    v = (v + b'\0' * sz)[:sz]
                    off = ops[0].mem.disp
                    b = buf.setdefault('A', bytearray(64))
                    while len(b) < off + len(v):
                        b.extend(b'\0' * 64)
                    b[off:off + len(v)] = v
        elif m == 'mov' and len(ops) == 2 and ops[0].type == X86_OP_MEM and ops[1].type == X86_OP_IMM:
            base = ins.reg_name(ops[0].mem.base)
            if base == 'rax':
                off = ops[0].mem.disp
                sz = ops[0].size
                v = (ops[1].imm & ((1 << (sz * 8)) - 1)).to_bytes(sz, 'little')
                b = buf.setdefault('A', bytearray(64))
                while len(b) < off + len(v):
                    b.extend(b'\0' * 64)
                b[off:off + len(v)] = v
        elif m == 'call':
            b = buf.get('A')
            if b:
                s = bytes(b).split(b'\0')[0]
                if len(s) >= 4:
                    out.append((ins.address, s.decode('latin1')))
            buf = {}
            regval = {}
    return out


if __name__ == '__main__':
    for a in [int(x, 16) for x in sys.argv[1:]]:
        print('===', hex(a), NAMES.get(a) or P.get(a, {}).get('name'))
        for addr, s in inline_strings(a):
            print('   %x %r' % (addr, s))
