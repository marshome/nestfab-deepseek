# -*- coding: utf-8 -*-
"""Record what 0xB4470 is, and the contradiction its discovery exposes."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "the-nester-base-constructor-has-three-fields",
        "grade": "CONSTRUCTOR",
        "kind": "offset",
        "predicate": ("the nester base constructor is 0xB4470, 29 bytes, five callers, and it stores a vtable pointer at +0x00, a pointer from its second argument "
                      "at +0x08, 0x1869F at +0x10 and 0xFFFFFFFF at +0x14"),
        "witness": ("0xB4470's whole body is `lea rax, [rip + 0x987689]` / `mov qword ptr [rcx], rax` / `mov qword ptr [rcx + 8], rdx` / `mov dword ptr [rcx + "
                    "0x10], 0x1869f` / `mov dword ptr [rcx + 0x14], 0xffffffff` / `ret`, so the object register is rcx and the base part is 0x18 bytes. "
                    "**The model's Nester declares none of them**, which is the 0x10 of data `kNestingNesterBaseDataGap` was written to record"),
        "round": 754,
    },
    {
        "subject": "0xB4DA0-is-a-derived-constructor-not-the-base",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("0xB4DA0 is a DERIVED class's constructor that shares the 0xB4470 base, not the base constructor itself, because it does everything 0xB4470 "
                      "does and then moves a qword"),
        "witness": ("0xB4DA0 is 43 bytes with seven callers: it repeats the vtable store, the +0x08 pointer and the two dword defaults, then adds `0B4DAA mov rax, "
                    "qword ptr [r8]`, `0B4DBF mov qword ptr [r8], 0` and `0B4DC6 mov qword ptr [rcx + 0x18], rax`. Reading it as the base added an eighth byte "
                    "pair and moved every derived member 8 bytes too far, which lcns/tests/test_recovered.cpp caught: atSeedP must measure 0x08 and measured 0x18"),
        "round": 754,
    },
    {
        "subject": "the-nester-base-fields-cannot-be-added-yet",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("the three base fields cannot be added to `Nester` while `NestingNester` derives from it and its first own member measures 0x08, because the "
                      "base fields would move that member to 0x18"),
        "witness": ("lcns/tests/test_recovered.cpp asserts atSeedP == 0x08 and kNestingNesterBaseDataGap == 0x10, and `NestingNester`'s own declared layout puts "
                    "seedP immediately after the vptr. **So either this tree's NestingNester does not derive from NestingNester's real base, or the model's Nester "
                    "is not that base** -- and which one is NOT established. The change was reverted rather than forced, and the contradiction is recorded"),
        "round": 754,
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
