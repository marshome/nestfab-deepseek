# -*- coding: utf-8 -*-
"""Record the engine object-access measurements: what worked, what was a false positive, and the tool fix."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "multiengine-has-eight-object-offsets",
        "grade": "CONSTRUCTION",
        "kind": "offset",
        "predicate": ("MultiEngine::run writes its object at +0x00, +0x18, +0x20, +0x28, +0x30, +0x38 and +0x40 and reads +0x08, so it has seven members where the port "
                      "declares none"),
        "witness": ("RE 0x755050, 2329 bytes. `rcx` is the object -- established from the call sites (`mov rax, [rbx]` / `mov rcx, rbx` / `call qword ptr [rax + 0x10]`, "
                    "one of them preceded by `lock sub dword ptr [rbx + 8], 1`). The stores are `755298 mov dword ptr [r13], 0`, `755655 mov qword ptr [r9 + 0x18], 0`, "
                    "`75545E mov qword ptr [r15 + 0x20], rax`, `7554C4 [r15 + 0x28], r12`, `755489 [r15 + 0x30], rax`, `755796 [r15 + 0x38], rdx` and `7554BC [r15 + 0x40], 0`, "
                    "with `7552A0 mov rcx, qword ptr [r13 + 8]` as the read. **What each MEANS is not established**, so offset names are what the class can carry"),
        "round": 769,
    },
    {
        "subject": "r12-and-rbp-are-not-the-object-in-the-two-big-engines",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("in `EquivalentEngine::run` and `CompositeEngine::run` the registers with the most accesses are NOT the object: `r12` is a stack buffer and `rbp` points "
                      "inside a heap object"),
        "witness": ("`759D1D lea r12, [rsp + 0x120]` -- **a stack buffer** -- and `759E12 lea rbp, [rax + 0xb0]` -- **inside another object**; `r12` is then reused at "
                    "`75A769 lea r12, [rsi + 0x68]` and `75B4B8 lea r12, [rcx + rdx*8]`. **The two functions report the SAME 31 offsets through r12 in the same order, "
                    "which is what reading the same stack local from the same source code looks like.** So the object register for those two is still UNFOUND, and "
                    "`re/g_arg_access.py` -- which prints every argument register rather than tracking one -- is what showed this"),
        "round": 769,
    },
    {
        "subject": "a-memory-operand-before-the-comma-is-a-store",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("the object-access mapper called `mov dword ptr [r13], 0` a READ and `mov rax, qword ptr [r15 + 0x20]` a WRITE, because it tested the instruction's "
                      "text shape instead of the operand's position"),
        "witness": ("its first version asked whether the text matched `mov <size> ptr [..]` and treated everything else as a read, **so destination and source came out "
                    "swapped** -- and a store places a field while a load only uses one, which is the distinction the objective asks for. The test is now whether the "
                    "memory operand lies before the comma, and every offset in the report changed kind when it was fixed"),
        "round": 769,
    },
]


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    added = 0
    for claim in CLAIMS:
        if any(existing.get("subject") == claim["subject"] for existing in data["claims"]):
            continue
        data["claims"].append(claim)
        added += 1
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("added %d claim(s); %d total" % (added, len(data["claims"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
