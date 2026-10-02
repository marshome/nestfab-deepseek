#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Find every VIRTUAL CALL through a given vtable offset, with the arguments set up before it.

**A SLOT'S SIGNATURE COMES FROM ITS CALL SITES, NOT FROM A GUESS.** Two slots of `Tiling::Evaluator` were annotated `name()` and `evaluate()` before
the tables were measured, and reading slot 3's routine showed a copy constructor instead of a scoring function -- so the names were wrong, and the way
to recover them is to read who calls the slot and with what.

The calling convention this reports against is the module's, which `re/` already records for `Engine::Engine::Run`:

    rcx = the object   rdx = the first argument   r8 = the second   r9 = the third, and a double in xmm2 or xmm3

so a slot called with `rcx` a sub-object, `rdx` a pointer and `r8` a pointer is a method of three arguments, and a value read back with
`movsd xmm0, [rsp + N]` came back on the stack.

**TWO SHAPE MISTAKES WERE MADE WRITING THIS, AND BOTH ARE THE SAME KIND AS READING A TABLE AT THE WRONG BASE** -- assuming a shape that is not the
one present:

  * `op_str` for a virtual call is `qword ptr [rax + 0x10]`. **`call` IS THE MNEMONIC AND IS NOT IN `op_str`**, so a pattern beginning `call qword ptr`
    matched NOTHING and reported zero sites.
  * the offset is OPTIONAL: slot 0 is the bare `qword ptr [rax]`.

    python -u g_virtual_call_sites.py --offset 0x10
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

VIRTUAL = re.compile(r"^qword ptr \[(\w+)(?: \+ (0x[0-9a-f]+))?\]$")
ARGUMENT = re.compile(r"^(rcx|rdx|r8|r9|xmm0|xmm2|xmm3), ")


def instruction_text(register, offset):
    return "qword ptr [%s%s]" % (register, " + 0x%X" % offset if offset else "")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--offset", dest="offset", required=True, help="the vtable offset, e.g. 0x10 for slot 2")
    parser.add_argument("--show", type=int, default=8, help="instructions before the call to print")
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args(argv)
    wanted = int(args.offset, 16)

    profile = load_prof()
    sites = []
    for address, info in profile.items():
        size = info.get("size") or 0
        if not size:
            continue
        window = []
        for instruction in disasm(address):
            if instruction.address >= address + size:
                break
            if instruction.mnemonic == "call":
                match = VIRTUAL.match(instruction.op_str)
                if match:
                    offset = int(match.group(2), 16) if match.group(2) else 0
                    if offset == wanted:
                        sites.append((address, instruction.address, match.group(1), list(window)))
            window.append(instruction)
            if len(window) > args.show:
                window.pop(0)

    print("virtual calls through [reg + 0x%X]: %d" % (wanted, len(sites)))
    print("")
    for function, site, register, window in sites[:args.limit]:
        info = profile.get(function) or {}
        callers = len(set(info.get("callers") or []))
        print("0x%-8X at 0x%-8X  through %s  (function %s bytes, %d callers)"
              % (function, site, register, info.get("size") or 0, callers))
        for instruction in window:
            mark = "   <-- an ARGUMENT register" if ARGUMENT.match(instruction.op_str) else ""
            print("      %06X %-12s %-44s%s" % (instruction.address, instruction.mnemonic, instruction.op_str[:44], mark))
        print("      %06X %-12s %s" % (site, "call", instruction_text(register, wanted)))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
