# -*- coding: utf-8 -*-
"""Which offsets each engine touches through its object register -- so a field's OWNER can be decided by agreement.

**THE OBJECT REGISTER IS THE ONE THAT RECEIVES `rcx`**, directly (`mov r13, rcx` at 0x755072, `mov rdi, rcx` at 0x756EEA) or through the spill slot (`mov rsi, qword ptr
[rsp + 0x210]` at 0x75BDD8, `mov rdi, qword ptr [rsp + 0x410]` at 0x75AD1D). **A field all five touch is the base's; a field one touches is that class's** -- and that
decision needs no constructor, which is the point, because there is none to read.
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

ENGINES = [(0x755050, "MultiEngine"), (0x756EC0, "DelayedEngine"), (0x757250, "NestingEngine"),
           (0x75BCC0, "EquivalentEngine"), (0x759B70, "CompositeEngine")]
ACCESS = re.compile(r"\[(\w+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]")


def object_registers(address, size):
    """the registers that receive rcx, directly or from the spill slot.

    **`rax` IS EXCLUDED ON PURPOSE.** It receives `rcx` in two of these functions and is then immediately reused as scratch -- `lea rax, [rbx + 0x30]` -- **so counting it
    invents fields that belong to whatever `rax` happens to point at.** The proof that it must go is `CompositeEngine`: with `rax` in the set it reports SIX object
    registers and 21 offsets, and a function has one object.
    """
    holders = set()
    spill_slots = set()
    for instruction in disasm(address):
        if instruction.address >= address + size:
            break
        copy = re.match(r"^(\w+), rcx$", instruction.op_str)
        if instruction.mnemonic == "mov" and copy:
            holders.add(copy.group(1))
        spill = re.match(r"^qword ptr \[rsp \+ (0x[0-9a-f]+)\], rcx$", instruction.op_str)
        if instruction.mnemonic == "mov" and spill:
            spill_slots.add(spill.group(1))
    if spill_slots:
        for instruction in disasm(address):
            if instruction.address >= address + size:
                break
            for slot in spill_slots:
                reload = re.match(r"^(\w+), qword ptr \[rsp \+ %s\]$" % slot, instruction.op_str)
                if instruction.mnemonic == "mov" and reload:
                    holders.add(reload.group(1))
    holders.discard("rax")
    return holders


def main():
    profile = load_prof()
    # **THE ONE RELIABLE OBJECT REGISTER PER ENGINE, NAMED RATHER THAN DISCOVERED.** The discovery above is what showed that `CompositeEngine` cannot be done this way --
    # it hands `rcx` to several registers and then REUSES `rcx` as scratch (`759D4D` uses `rax`, `759D76` reads through it again), so a heuristic over "registers that ever
    # received rcx" collects registers that received it and then stopped being it. **These five are the ones the prologues establish**, and `CompositeEngine`'s is left
    # out because it does not have one this method can name -- **which is recorded instead of guessed.**
    NAMED = [(0x755050, "MultiEngine", "r13"), (0x756EC0, "DelayedEngine", "rdi"),
             (0x757250, "NestingEngine", "r15"), (0x75BCC0, "EquivalentEngine", "rsi"),
             (0x757250, "NestingEngine (again)", "r15")]
    NAMED = [(0x755050, "MultiEngine", "r13"), (0x756EC0, "DelayedEngine", "rdi"),
             (0x757250, "NestingEngine", "r15"), (0x75BCC0, "EquivalentEngine", "rsi")]
    per_engine = {}
    for address, label, register in NAMED:
        size = (profile.get(address) or {}).get("size") or 0
        offsets = {}
        for instruction in disasm(address):
            if instruction.address >= address + size:
                break
            text = instruction.op_str
            for match in re.finditer(r"\[%s(?:\s*\+\s*(0x[0-9a-f]+))?\]" % register, text):
                offset = int(match.group(1), 16) if match.group(1) else 0
                store = "," in text and match.start() < text.index(",")
                offsets.setdefault(offset, ("W" if store else "R") + " %06X %s" % (instruction.address, text[:36]))
        per_engine[label] = offsets
        print("%-18s through %-4s %2d offset(s): %s" % (label, register, len(offsets),
                                                        " ".join("+0x%X" % o for o in sorted(offsets))))
    print("")
    print("**AND THE RANGE ALL FOUR AGREE ON IS THE BASE's:**")
    common = set.intersection(*[set(offsets) for offsets in per_engine.values()]) if per_engine else set()
    for offset in sorted(common):
        print("+0x%-6X" % offset)
        for label, offsets in per_engine.items():
            print("        %-18s %s" % (label, offsets[offset]))
    print("")
    print("**and the offsets only SOME touch, which are NOT shown to be the base's:**")
    for offset in sorted({o for offs in per_engine.values() for o in offs} - common):
        who = [label for label, offs in per_engine.items() if offset in offs]
        print("+0x%-6X %s" % (offset, " ".join(who)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
