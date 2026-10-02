# -*- coding: utf-8 -*-
"""What the callers of an error reporter pass as file and method names.

Usage: python g_arg_labels.py 0x60A620 [window] [limit]

0x60A620 is the module's internal error reporter -- 680 callers, and its own literals are
'*** INTERNAL ERROR: please contact support ***', ': error ' and '(assertion failed in '. A function that takes a file name
and a method name and is called from 680 places is a naming oracle: the caller loads those two strings just before the
call, so the name of an otherwise anonymous function can be read out of its own call site rather than guessed from its
shape.

The head of 0x60A620 shows the arguments:

    mov r13, rcx    ; the first argument
    mov [rsp+0x298], edx
    mov r12, r8     ; the third
    mov r15, r9     ; the fourth

so the first, third and fourth arrive in registers and are used later in the body, while the second is spilled. For each
call site this prints every rip-relative literal the caller loads in the `window` instructions before the call, in order,
with the register it went into, because that order is what tells the file name from the method name. Literals loaded
anywhere in the caller's body are printed too, marked as such, since a name built earlier is still that caller's.

This writes nothing. The point is to turn 680 anonymous functions into 680 named ones in one run.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import lib as LIB               # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

IMAGE = LIB.data if isinstance(LIB.data, (bytes, bytearray)) else LIB.data()


def printable(data, limit=96):
    out = []
    for b in data:
        if b == 0:
            break
        if 32 <= b < 127:
            out.append(chr(b))
        else:
            break
    return "".join(out)[:limit]


def string_at(rva, limit=96):
    try:
        off = rva2off(rva)
    except Exception:
        return None
    if off is None or off < 0 or off >= len(IMAGE):
        return None
    text = printable(IMAGE[off:off + limit], limit)
    return text if len(text) >= 3 else None


def rip_literals(body, first, last):
    """(address, register, target, text) for each rip-relative literal load in body[first:last]."""
    out = []
    for index in range(first, min(last, len(body))):
        ins = body[index]
        m = re.search(r"\[rip [+-] 0x([0-9a-f]+)\]", ins.op_str)
        if not m:
            continue
        disp = int(m.group(1), 16)
        if "[rip - " in ins.op_str:
            disp = -disp
        nxt = body[index + 1].address if index + 1 < len(body) else ins.address + 8
        target = nxt + disp
        text = string_at(target)
        if text:
            register = ins.op_str.split(",")[0].strip()
            out.append((ins.address, register, target, text))
    return out


def main(argv):
    if not argv:
        print("give the reporter's rva, for example 0x60A620")
        return 2
    target = int(argv[0], 0)
    window = int(argv[1]) if len(argv) > 1 else 24
    limit = int(argv[2]) if len(argv) > 2 else 10 ** 6
    profile = load_prof()

    callers = []
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        for index, ins in enumerate(body):
            if ins.mnemonic != "call":
                continue
            m = re.search(r"0x([0-9a-f]+)", ins.op_str)
            if m and int(m.group(1), 16) == target:
                callers.append((addr, body, index))
    callers.sort()

    print("0x%X: %d call sites in %d distinct functions" % (target, len(callers), len(set(c[0] for c in callers))))
    print("")
    shown = 0
    for addr, body, index in callers:
        if shown >= limit:
            break
        shown += 1
        size = (profile.get(addr) or {}).get("size")
        near = rip_literals(body, max(0, index - window), index)
        far = [x for x in rip_literals(body, 0, index) if x not in near]
        print("=== caller 0x%X (%s B, call at 0x%X)" % (addr, size, body[index].address))
        if near:
            print("  passed at the call site, in order:")
            for iaddr, reg, taddr, text in near:
                print("    0x%-8X %-6s -> 0x%-8X %r" % (iaddr, reg, taddr, text))
        else:
            print("  nothing loaded in the last %d instructions" % window)
        if far:
            print("  loaded elsewhere in the caller:")
            for iaddr, reg, taddr, text in far[-4:]:
                print("    0x%-8X %-6s -> 0x%-8X %r" % (iaddr, reg, taddr, text))
        print("")
    if shown < len(callers):
        print("... %d more call sites" % (len(callers) - shown))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
