# -*- coding: utf-8 -*-
"""Correct last round's placement claim and add what this round measured.

**WHAT WAS WRONG:** the claim said the constructor installs `Multi::NoFitMapCanceller` at `[rbx + 0x478]` and `Multi::NestingContextPool` at `[rbx + 0x4C8]`.
**Neither is right.** This round's trace of the same function shows the two installs write through `rax`, which holds a FRESH 0x10 byte allocation:

    0x3290C  lea rax, [rip + 0xa0909d]   ; 0xA3B9B0 = Multi::NestingContextPool's vtable
    0x32913  mov ecx, 0x10               ; and the object is allocated on its own
    0x32AE9  lea rsi, [rip + 0xa08e00]   ; 0xA3B8F0 = Multi::NoFitMapCanceller's vtable
    0x32AD7  mov ecx, 0x10               ; likewise
    0x32AFC  mov qword [rax], rsi        ; +0x00 = the vtable
    0x32AFF  mov qword [rax + 8], rdx    ; +0x08 = THE OWNER, from `mov rdx, [rbx + 8]` at 0x32AE5

**and `[rbx + 0x478]` is an 0x18 byte sub-object while `[rbx + 0x4C8]` is a `std::shared_ptr`** whose 0x18 byte control block holds
`_M_use_count = 1`, `_M_weak_count = 1` and `_M_ptr = r14`, installed from 0xA560C0. **The error was reading vtable installs without asking WHICH base register
they were written through** -- which is the same rule the objective states as "对象寄存器必须先确立".
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")
SUBJECT = "Supervisors-state-object-is-0x530-and-4-nested-types"

REPLACEMENT = {
    "subject": "Supervisors-state-and-the-two-0x10-byte-cancellers",
    "grade": "CONSTRUCTOR",
    "kind": "offset",
    "predicate": ("Multi::Supervisor's constructor 0x32700 allocates a 0x530 byte state object and stores it at the Supervisor's +8, and separately allocates TWO "
                  "0x10 byte objects, `Multi::NestingContextPool` at 0x32913 and `Multi::NoFitMapCanceller` at 0x32AD7, each `{vptr at +0, OWNER at +8}` whose "
                  "+8 receives the Supervisor itself"),
    "witness": ("0x032720 mov ecx,0x530 is the only site in the module asking for that size and 0x032AD2 mov qword [r12+8],rbx stores it where the destructor's "
                "0x030B71 mov rsi,[rcx+8] reads; 0x3290C lea rax,[rip+0xa0909d] gives 0x32913+0xA0909D = 0xA3B9B0 = NestingContextPool's vtable and 0x32913 mov "
                "ecx,0x10 its size; 0x32AE9 lea rsi,[rip+0xa08e00] gives 0x32AF0+0xA08E00 = 0xA3B8F0 = NoFitMapCanceller's vtable and 0x32AD7 mov ecx,0x10 its "
                "size; 0x32AFC and 0x32AFF write the vtable and then the owner, which 0x32AE5 mov rdx,[rbx+8] took from the Supervisor. The earlier claim that "
                "these were installed at [rbx+0x478] and [rbx+0x4C8] was WRONG -- +0x478 is an 0x18 byte sub-object and +0x4C8 is a std::shared_ptr whose control "
                "block is installed from 0xA560C0 -- because the installs were read without establishing which base register they used"),
    "round": 729,
}


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    claims = data["claims"]
    kept = [c for c in claims if c.get("subject") != SUBJECT]
    if len(kept) == len(claims):
        print("REFUSING: the claim is not found by that subject")
        return 2
    kept.append(REPLACEMENT)
    data["claims"] = kept
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("replaced: the two cancellers are separate 0x10 byte allocations with the Supervisor as their owner at +8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
