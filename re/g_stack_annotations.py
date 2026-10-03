# -*- coding: utf-8 -*-
"""Which `RE 0xNNN` annotations in a header cite a STACK store where the member is an object field.

**A FIELD'S WIDTH MUST COME FROM A STORE THROUGH THE OBJECT'S REGISTER.** `launching_order.hpp` byte 0x028 says "narrowest store is 1 byte(s) at RE 0xD062", **and 0xD062 is
`mov byte ptr [rsp + 0x28], 0`** -- the SAME DISPLACEMENT but on the STACK, inside the logging/exception object that the function builds. **So the width was read off a
different object**, and the member is declared one byte where the field it covers is eight.

**AND THIS IS THE SHAPE THE OBJECTIVE NAMES**: a member whose comment cites a stack store. `re/g_full_cpp_audit.py` reports that shape as zero, **so either its test is
narrower than this or the annotation is spelled in a way it does not match** -- either way this measures the real thing directly.

    python -u g_stack_annotations.py lcns/include/lcns/launching_order.hpp
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import disasm  # noqa: E402

ANNOTATION = re.compile(r"RE 0x([0-9A-Fa-f]+)")
STACK = re.compile(r"\[(?:rsp|rbp|esp|ebp)(?:\s*[+-]\s*0x[0-9a-f]+)?\]")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "lcns", "include", "lcns", "launching_order.hpp")
    text = io.open(path, encoding="utf-8", errors="replace").read()

    total = 0
    stack_only = []
    for line in text.split("\n"):
        found = ANNOTATION.search(line)
        if not found:
            continue
        total += 1
        address = int(found.group(1), 16)
        # the first instruction at that address, and whether it touches the stack
        instructions = list(disasm(address, count=3))
        if not instructions:
            continue
        first = instructions[0]
        writes_stack = bool(STACK.search(first.op_str))
        writes_object = bool(re.search(r"\[r(?:si|bx|di|cx|ax|dx|\d+)(?:\s*\+\s*0x[0-9a-f]+)?\]", first.op_str))
        # **`[rbp + N]` IS NOT EVIDENCE OF A STACK STORE, AND THE FIRST VERSION OF THIS TOOL SAID IT WAS.** Both functions it flagged begin `push rbp` /
        # `mov rbp, rcx`, **so rbp holds the OBJECT and `[rbp + 0xc]` is a real field write.** Flagging every rbp reference is a false positive that would have sent a
        # round to "fix" three correct annotations, so rbp is only a stack base when the function does not load it from rcx.
        if writes_stack and re.search(r"\[rbp", first.op_str):
            prologue = list(disasm(address - 0x40, count=24))
            holds_object = any(i.mnemonic == "mov" and i.op_str.replace(" ", "") == "rbp,rcx" for i in prologue)
            if holds_object:
                writes_stack = False
        if writes_stack and not writes_object:
            member = re.match(r"\s*[\w:<>,\s\*&]+?\s+(\w+)", line)
            stack_only.append((address, member.group(1) if member else "?", first.mnemonic, first.op_str))

    print("%s" % os.path.relpath(path, ROOT))
    print("  annotations citing an address:        %d" % total)
    print("  **annotations whose instruction is a STACK store: %d**" % len(stack_only))
    for address, member, mnemonic, op in stack_only[:20]:
        print("     RE 0x%-6X %-22s %-8s %s" % (address, member, mnemonic, op))
    return 0


if __name__ == "__main__":
    sys.exit(main())
