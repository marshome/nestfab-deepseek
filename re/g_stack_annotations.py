# -*- coding: utf-8 -*-
"""Find every header annotation whose `RE 0xNNN` cites an instruction that WRITES THE STACK, where the line declares an object member.

**THE OBJECT REGISTER HAS TO BE ESTABLISHED FIRST, WHICH IS THE PROJECT'S OWN RULE.** A store is evidence for a field's width only when its base register is the object.
`launching_order.hpp` byte 0x028 said "1 byte at RE 0xD062" and 0xD062 is `mov byte ptr [rsp + 0x28], 0` -- **the same displacement on the STACK** -- so an object member
was given a width read off a different object.

**AND `[rbp + N]` IS NOT STACK UNLESS `rbp` IS THE FRAME.** The first version of this check flagged three correct annotations because both functions begin
`push rbp` / `mov rbp, rcx`, **so rbp holds the object.** The function's start now comes from the PROFILE rather than from a fixed window, and the prologue is read from
there -- **a check that flags correct code sends a round to break it, so the false positive is the thing to eliminate first.**
"""
import glob
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import disasm, load_prof  # noqa: E402

ANNOTATION = re.compile(r"RE 0x([0-9A-Fa-f]+)")
OBJECT_BASE = re.compile(r"\[(r(?:si|bx|di|cx|ax|dx|8|9|1[0-5]))(?:\s*\+\s*(0x[0-9a-f]+))?\]")
STACK_BASE = re.compile(r"\[(rsp|esp)(?:\s*[+-]\s*0x[0-9a-f]+)?\]")
RBP_BASE = re.compile(r"\[rbp(?:\s*[+-]\s*0x[0-9a-f]+)?\]")


def owner_of(address, functions):
    for start in functions:
        size = functions[start]
        if size and start <= address < start + size:
            return start
    return None


def prologue_loads_rbp_from_rcx(start, functions):
    """Does the function at `start` put the OBJECT in rbp? Then `[rbp + N]` is a field write."""
    size = functions.get(start) or 0
    count = 0
    for instruction in disasm(start):
        if (size and instruction.address >= start + size) or count > 14:
            break
        count += 1
        if instruction.mnemonic == "mov":
            operands = instruction.op_str.replace(" ", "")
            if operands in ("rbp,rcx", "rbx,rcx", "rsi,rcx", "rdi,rcx"):
                return operands.split(",")[0]
    return None


def main():
    functions = {address: (entry.get("size") or 0) for address, entry in load_prof().items()}
    headers = sorted(glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "*.hpp")))

    defects = []
    stack_annotations = 0
    total = 0
    for path in headers:
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for number, line in enumerate(text.split("\n"), 1):
            found = ANNOTATION.search(line)
            if not found:
                continue
            total += 1
            address = int(found.group(1), 16)
            instructions = list(disasm(address, count=1))
            if not instructions:
                continue
            first = instructions[0]
            if not first.mnemonic.startswith("mov"):
                continue
            if STACK_BASE.search(first.op_str):
                stack_annotations += 1
                member = re.match(r"\s*[\w:<>,\s\*&]+?\s+(\w+)", line)
                defects.append((os.path.basename(path), number, address, member.group(1) if member else "?", first.mnemonic, first.op_str, "rsp"))
                continue
            if RBP_BASE.search(first.op_str) or OBJECT_BASE.search(first.op_str):
                start = owner_of(address, functions)
                if start is None:
                    continue
                register = prologue_loads_rbp_from_rcx(start, functions)
                # the base in the instruction, and whether that base was loaded from rcx
                base = re.search(r"\[(\w+)", first.op_str)
                basename = base.group(1) if base else ""
                if basename == "rbp" and register != "rbp":
                    stack_annotations += 1
                    member = re.match(r"\s*[\w:<>,\s\*&]+?\s+(\w+)", line)
                    defects.append((os.path.basename(path), number, address, member.group(1) if member else "?",
                                    first.mnemonic, first.op_str, "rbp not from rcx"))

    print("headers scanned:                     %d" % len(headers))
    print("annotations citing an address:       %d" % total)
    print("**annotations that WRITE THE STACK:  %d**" % len(defects))
    for name, number, address, member, mnemonic, op, why in defects:
        print("   %-24s:%-5d RE 0x%-6X %-22s %-8s %-34s (%s)" % (name, number, address, member, mnemonic, op, why))
    return 0


if __name__ == "__main__":
    sys.exit(main())
