# -*- coding: utf-8 -*-
"""Every DIRECT call to an engine's `run`, so the call site can say what the arguments are.

**NOTHING REFERENCES AN ENGINE VTABLE, SO THE CALL MUST BE FOUND FROM THE OTHER END.** A direct `call` to a `run` address would name the object explicitly; **and if there
is no direct call either, then the engines are reached ONLY through a vtable that nothing in this image installs** -- which would mean the callers are outside the module
and the signature cannot be settled from this dump at all.
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

RUNS = {0x759A80: "InfiniteEngine", 0x755050: "MultiEngine", 0x756EC0: "DelayedEngine",
        0x757250: "NestingEngine", 0x75BCC0: "EquivalentEngine", 0x759B70: "CompositeEngine"}


def main():
    profile = load_prof()
    print("direct `call <run>` sites, and indirect calls through slot +0x10:")
    print("")
    for target, label in sorted(RUNS.items()):
        direct = []
        indirect = []
        for address in sorted(profile):
            size = (profile[address] or {}).get("size") or 0
            if not size or size > 4000 or address == target:
                continue
            for instruction in disasm(address):
                if instruction.address >= address + size:
                    break
                if instruction.mnemonic == "call":
                    if instruction.op_str == "0x%x" % target:
                        direct.append(address)
                    elif instruction.op_str == "qword ptr [rax + 0x10]":
                        indirect.append(address)
        print("%-18s run 0x%-8X  %d direct call(s) %s   |   %d site(s) call [rax + 0x10]"
              % (label, target, len(direct), [hex(d) for d in direct[:4]], len(indirect)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
