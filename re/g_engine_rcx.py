# -*- coding: utf-8 -*-
"""Is `rcx` the object or an sret buffer, for each engine's `run`?

**THE DISCRIMINATOR IS WHETHER `rcx` IS EVER DEREFERENCED.** A method's `this` is read: a vtable call, a member store, anything through `[this + N]`. **An sret buffer is
WRITTEN and the object pointer is never touched** -- and the callee returns the buffer address in `rax`, which is what `mov rax, rbx` after `mov rbx, rcx` means.

**AND THE SOURCE IS THE DECLARATION ITSELF**: `EngineBase::run` is declared `void* run(const void*, double, void*, void*)` with four arguments, **while the module passes a
FIFTH on the stack** (`mov rsi, qword ptr [rsp + 0x100]` survives a `sub rsp, 0xa0` only if the argument lives at `+0x100` in the caller's frame). **A method whose first
parameter is `this` and which takes four more arguments has no room for an sret pointer -- so if the module has five arguments, the first is not `this`.**
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

RUNS = [(0x759A80, "InfiniteEngine"), (0x755050, "MultiEngine"), (0x756EC0, "DelayedEngine"),
        (0x757250, "NestingEngine"), (0x75BCC0, "EquivalentEngine"), (0x759B70, "CompositeEngine")]

ACCESS = re.compile(r"\[(r\w+)(?:\s*\+\s*(0x[0-9a-f]+))?\]")


def main():
    profile = load_prof()
    print("%-18s %-10s %-8s %s" % ("engine", "address", "size", "verdict on rcx"))
    for address, label in RUNS:
        size = (profile.get(address) or {}).get("size") or 0
        # which register receives rcx at the top, and is it ever a base?
        holds = set()
        dereferenced = False
        stack_argument = False
        for instruction in disasm(address):
            if instruction.address >= address + size:
                break
            text = instruction.op_str
            copy = re.match(r"^(\w+), rcx$", text)
            if instruction.mnemonic == "mov" and copy:
                holds.add(copy.group(1))
            for match in ACCESS.finditer(text):
                if match.group(1) in holds:
                    dereferenced = True
            if re.search(r"\[rsp \+ 0x1[0-9a-f][0-9a-f]\]", text):
                stack_argument = True
        verdict = ("**rcx IS DEREFERENCED -- it could be `this`**" if dereferenced
                   else "**rcx is NEVER dereferenced -- it is an sret buffer**")
        print("%-18s 0x%-8X %-8s %s%s" % (label, address, size, verdict,
                                          "   (and a stack argument is read)" if stack_argument else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
