# -*- coding: utf-8 -*-
"""Every access through a function's OBJECT register, grouped by offset, with the instruction that makes it.

**THE OBJECT REGISTER IS `rcx` AT ENTRY** -- established for the engines from the call sites: `mov rax, qword ptr [rbx]` / `mov rcx, rbx` / `call qword ptr [rax + 0x10]`,
with a `std::shared_ptr` count beside one of them. **So this follows `rcx` into whatever register receives it, and prints what is read and written through it**, which is
the raw material for a class's members.

**AND IT SEPARATES READS FROM WRITES**, because a store places a field and a load only uses one -- **the distinction the objective asks for when it says a member needs an
instruction that PUTS it there.**

    python -u g_object_access.py 0x755050 [0x757250 ...]
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
# **A MEMORY OPERAND BEFORE THE COMMA IS A DESTINATION AND ONE AFTER IT IS A SOURCE.**
#
# The first version asked whether the instruction's TEXT started with `mov ... ptr` and called everything else a read -- **so `mov dword ptr [r13], 0` came out as a
# READ and `mov rax, qword ptr [r15 + 0x20]` came out as a WRITE.** A store places a field and a load only uses one, **and the objective asks for the instruction that
# PUTS a member there**, so the two cannot be confused. The test is the OPERAND POSITION, not the mnemonic's shape.


def main():
    profile = load_prof()
    for argument in sys.argv[1:]:
        address = int(argument, 16)
        entry = profile.get(address) or {}
        size = entry.get("size") or 0
        print("=" * 96)
        print("0x%X  %s bytes" % (address, size))
        print("=" * 96)

        holds = {"rcx"}
        writes = defaultdict(list)
        reads = defaultdict(list)
        for instruction in disasm(address):
            if instruction.address >= address + size:
                break
            text = instruction.op_str
            for match in ACCESS.finditer(text):
                base = match.group(1)
                if base not in holds:
                    continue
                offset = int(match.group(2), 16) if match.group(2) else 0
                # the comma separates destination from source, so the operand's position says which this is
                is_store = "," in text and match.start() < text.index(",")
                where = writes if is_store else reads
                if len(where[offset]) < 2:
                    where[offset].append("%06X %s" % (instruction.address, text[:44]))
            copy = re.match(r"^(\w+), (\w+)$", text)
            if instruction.mnemonic == "mov" and copy:
                destination, source = copy.group(1), copy.group(2)
                if source in holds:
                    holds.add(destination)
                elif destination in holds:
                    holds.discard(destination)
        all_offsets = sorted(set(writes) | set(reads))
        print("%-8s %-6s %s" % ("offset", "kind", "instruction"))
        for offset in all_offsets:
            kind = ("write" if offset in writes else "") + ("+read" if offset in reads else "")
            detail = (writes.get(offset) or reads.get(offset))[0]
            print("+0x%-6X %-8s %s" % (offset, kind, detail))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
