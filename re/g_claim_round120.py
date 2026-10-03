# -*- coding: utf-8 -*-
"""Record what the engine family's vtables and copy constructor establish."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "the-engine-base-is-EngineEngine-not-EngineBase",
        "grade": "DERIVATION",
        "kind": "call",
        "predicate": "the engine base class is `Engine::Engine` -- its mangled name is N6Engine6EngineE -- and the port's `EngineBase` is a name this project invented for it",
        "witness": "re/vtables.json holds every engine under the N6Engine prefix: N6Engine14InfiniteEngineE, N6Engine11MultiEngineE, N6Engine13DelayedEngineE, N6Engine13NestingEngineE, N6Engine16EquivalentEngineE, N6Engine11CloudEngineE, N6Engine15CompositeEngineE. **There is NO entry ending in `6EngineE`**, which is consistent with the note in lcns/engines.hpp: an abstract base has no vtable of its own, which is also why the whole base layer was missing from this tree",
        "round": 764,
    },
    {
        "subject": "every-engine-has-exactly-three-vtable-slots",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": "each of the seven engine classes has exactly three vtable slots -- a deleting destructor, a destructor and `run` -- so the base's whole surface is the one virtual the port declares",
        "witness": "re/vtables.json gives 3 slots for all seven, and their slot 2 values differ: InfiniteEngine 0x759A80, MultiEngine 0x755050, DelayedEngine 0x756EC0, NestingEngine 0x757250, EquivalentEngine 0x75BCC0, CloudEngine 0x26A60, CompositeEngine 0x759B70. **The assertion in lcns/engines.hpp that slot 2 differs in all seven is therefore CHECKED rather than asserted**",
        "round": 764,
    },
    {
        "subject": "the-engine-base-object-is-0x20-bytes",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": "the engine base object carries a vptr and three pointers -- 0x20 bytes -- so the port's empty `EngineBase` is missing data",
        "witness": "RE 0x754DE0, 74 bytes, three callers, is a COPY/MOVE constructor for a 0x20 object: `mov qword ptr [rcx], 0`, then `mov r8, [rdx]`, then `mov [rcx], r8` and `mov rax, [rdx + 8]` / `[rdx + 0x10]` / `[rdx + 0x18]` each stored to the same offset of rcx -- **it copies the vptr too, which is what a copy constructor does and a base constructor does not.** **The fields' MEANINGS are not established**, so this is recorded as a size and not as three named members",
        "round": 764,
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
