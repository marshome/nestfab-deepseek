# -*- coding: utf-8 -*-
"""Read a few `call qword ptr [rax + 0x10]` sites to see what is passed -- above all what `rcx` is.

**THE ENGINES ARE REACHED ONLY THROUGH SLOT 2, SO THE CALL SITE IS THE ONLY PLACE THAT CAN SETTLE THE SIGNATURE.** If `rcx` at such a site is a stack buffer, the first
argument is an sret pointer; if it is an object loaded from a member, it is `this`.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import disasm, load_prof  # noqa: E402


def main():
    profile = load_prof()
    shown = 0
    for address in sorted(profile):
        size = (profile[address] or {}).get("size") or 0
        if not size or size > 2000:
            continue
        body = []
        for instruction in disasm(address):
            if instruction.address >= address + size:
                break
            body.append(instruction)
        for index, instruction in enumerate(body):
            if not (instruction.mnemonic == "call" and instruction.op_str == "qword ptr [rax + 0x10]"):
                continue
            # the eight instructions before the call, which is where the arguments are set
            print("=" * 96)
            print("call site in 0x%X at 0x%X" % (address, instruction.address))
            for item in body[max(0, index - 9):index + 1]:
                marker = "  <-- the call" if item.address == instruction.address else ""
                print("   %06X %-12s %-34s%s" % (item.address, item.mnemonic, item.op_str, marker))
            shown += 1
            break
        if shown >= 3:
            break
    if shown == 0:
        print("no site found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
