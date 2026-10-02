# -*- coding: utf-8 -*-
"""Find the strings a function builds on the stack with immediate stores.

Usage: python g_stack_strings.py 0x69BE80 --all        -> every stack string in that function
       python g_stack_strings.py 0x69BE80 0x69C496     -> the strings near one address

The assertion reporter's callers do not always load their file and method names from read-only data. The compiler builds
short strings in place when they fit in registers, eight bytes at a time and then two and one:

    movabs rdx, 0x69746c756d5c2e2e     ; '..\\multi'
    mov    qword ptr [rax], rdx
    movabs rdx, 0x2e72656b72616d5c     ; '\\marker.'
    mov    qword ptr [rax + 8], rdx
    mov    ecx, 0x7063                 ; 'cp'  -- note the register: NOT the one the movabs used
    mov    word ptr [rax + 0x10], cx
    mov    byte ptr [rax + 0x12], 0x70 ; 'p'
    mov    byte ptr [rdx + rax], 0
    mov    edx, 0x75                   ; 117 = strlen('..\\multi\\marker.cpp')
    call   0x60A620

That is why a pass that decodes only rip-relative literals misses most assertion call sites: the strings are not in the
image at all, they are built. This walks the stores instead of the registers, so the width of each store and the register
that happens to hold the immediate do not matter, and it reports the length register loaded before the call so the result
can be cut to size.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib as LIB               # noqa: E402
from lib import disasm, load_prof  # noqa: E402


def printable(data):
    out = []
    for b in data:
        if b == 0:
            break
        out.append(chr(b) if 32 <= b < 127 else "\\x%02x" % b)
    return "".join(out)


def decode(value, width):
    return printable(value.to_bytes(width, "little"))


WIDTH = {"byte": 1, "word": 2, "dword": 4, "qword": 8}
LOAD = re.compile(r"([a-z0-9]+), (0x[0-9a-f]+|\d+)$")
STORE = re.compile(r"(byte|word|dword|qword) ptr \[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\], ([a-z0-9]+)$")

# The immediate and the store do not have to use the same register name: 'mov ecx, 0x7063' followed by
# 'mov word ptr [rax + 0x10], cx' is the 'cp' of '..\\multi\\marker.cpp'. Without canonicalising, that store looks like a
# store from an unknown register and ends the string three characters early, which is exactly what the first version did.
ALIAS = {}
for _full, _names in {
    "rax": ("eax", "ax", "al", "ah"), "rbx": ("ebx", "bx", "bl", "bh"), "rcx": ("ecx", "cx", "cl", "ch"),
    "rdx": ("edx", "dx", "dl", "dh"), "rsi": ("esi", "si", "sil"), "rdi": ("edi", "di", "dil"),
    "rbp": ("ebp", "bp", "bpl"), "rsp": ("esp", "sp", "spl"),
}.items():
    ALIAS[_full] = _full
    for _n in _names:
        ALIAS[_n] = _full
for _r in range(8, 16):
    ALIAS["r%d" % _r] = "r%d" % _r
    ALIAS["r%dd" % _r] = "r%d" % _r
    ALIAS["r%dw" % _r] = "r%d" % _r
    ALIAS["r%db" % _r] = "r%d" % _r


def scan(body, radius=None):
    """(first instruction address, text, length) for the stack strings in a body."""
    found = []
    pending = {}          # register -> (value, width) from a mov/movabs immediate
    text = ""
    start = None
    base = None
    for index, ins in enumerate(body):
        mload = LOAD.match(ins.op_str) if ins.mnemonic in ("mov", "movabs") else None
        if mload and not ins.op_str.startswith("["):
            value = int(mload.group(2), 0)
            width = 8 if ins.mnemonic == "movabs" else 4
            pending[ALIAS.get(mload.group(1), mload.group(1))] = (value, width)
            continue
        mstore = STORE.match(ins.op_str) if ins.mnemonic.startswith("mov") else None
        if mstore:
            width = WIDTH[mstore.group(1)]
            register = ALIAS.get(mstore.group(4), mstore.group(4))
            this_base = mstore.group(2)
            if register in pending:
                value, load_width = pending.pop(register)
                if start is None:
                    start = ins.address
                    base = this_base
                if this_base == base:
                    text += decode(value, width)
                    continue
                # a store to a different base ends the string
                if text:
                    found.append((start, text, length_after(body, index + 1)))
                start, base, text = ins.address, this_base, decode(value, width)
                continue
            # a store from a register we did not see loaded: the string, if any, ends here
            if text:
                found.append((start, text, length_after(body, index)))
                start, base, text = None, None, ""
            continue
        # any other instruction that is not a no-op ends a run
        if text and ins.mnemonic not in ("nop", "lea"):
            found.append((start, text, length_after(body, index)))
            start, base, text = None, None, ""
    if text:
        found.append((start, text, None))
    if radius is not None:
        found = [f for f in found if abs(f[0] - radius) <= 0x300 or (f[2] and abs(f[0] - radius) <= 0x300)]
    return found


def length_after(body, index):
    for k in range(index, min(index + 12, len(body))):
        m = re.match(r"edx, (0x[0-9a-f]+|\d+)$", body[k].op_str)
        if body[k].mnemonic == "mov" and m:
            return int(m.group(1), 0)
        if body[k].mnemonic == "call":
            return None
    return None


def main(argv):
    if not argv:
        print("give a function rva, for example 0x69BE80")
        return 2
    addr = int(argv[0], 0)
    profile = load_prof()
    size = (profile.get(addr) or {}).get("size") or 0
    body = [i for i in disasm(addr) if i.address < addr + size]
    radius = None
    if len(argv) > 1 and argv[1].startswith("0x"):
        radius = int(argv[1], 0)
    print("0x%X (%s bytes, %d instructions)" % (addr, size, len(body)))
    for iaddr, text, length in scan(body, radius):
        print("    0x%-8X len=%-6s %r" % (iaddr, length, text[:110]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
