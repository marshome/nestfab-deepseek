# -*- coding: utf-8 -*-
"""Every access through ANY argument register, so the object register can be found rather than assumed.

**THE TRACKING IN re/g_object_access.py FOLLOWS `rcx` THROUGH `mov` COPIES AND BREAKS WHEN A FUNCTION SPILLS IT TO THE STACK AND RELOADS IT INTO ANOTHER REGISTER** -- which
is why `EquivalentEngine::run` and `CompositeEngine::run` came out with nothing at all. **So this does not track: it prints every access through `rcx`, `rdx`, `r8`, `r9`,
`rbx`, `rsi`, `rdi`, `r12`-`r15`, and lets the pattern be read.**

**A FIELD LOOKS LIKE SEVERAL OFFSETS THROUGH ONE REGISTER**, and an argument is one offset through several -- **so the register with the most distinct offsets is almost always
the object, and that is a measurement rather than a guess.**
"""
import io
import os
import re
import sys

from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[(\w+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]")
REGISTERS = ["rcx", "rdx", "r8", "r9", "rbx", "rsi", "rdi", "rbp", "r12", "r13", "r14", "r15", "rax"]


def main():
    profile = load_prof()
    for argument in sys.argv[1:]:
        address = int(argument, 16)
        size = (profile.get(address) or {}).get("size") or 0
        print("=" * 96)
        print("0x%X  %s bytes" % (address, size))
        per_register = defaultdict(set)
        evidence = {}
        for instruction in disasm(address):
            if instruction.address >= address + size:
                break
            for match in ACCESS.finditer(instruction.op_str):
                base = match.group(1)
                if base not in REGISTERS:
                    continue
                offset = int(match.group(2), 16) if match.group(2) else 0
                per_register[base].add(offset)
                evidence.setdefault((base, offset), "%06X %s" % (instruction.address, instruction.op_str[:42]))
        for base in sorted(per_register, key=lambda r: -len(per_register[r])):
            offsets = sorted(per_register[base])
            if len(offsets) < 2 and base not in ("rcx",):
                continue
            print("  %-5s %2d distinct offset(s): %s" % (base, len(offsets),
                                                          " ".join("+0x%X" % o for o in offsets[:14])))
            for offset in offsets[:6]:
                print("        +0x%-6X %s" % (offset, evidence[(base, offset)]))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
