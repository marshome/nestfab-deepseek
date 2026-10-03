# -*- coding: utf-8 -*-
"""Record the two things the engine `run` bodies establish about the base's SIGNATURE."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "two-engines-run-return-by-sret-so-rcx-is-not-this",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("`InfiniteEngine::run` and `EquivalentEngine::run` never dereference `rcx`, and write a return buffer through it -- `mov [rcx], 0`, `[rcx + 0x10]`, "
                      "`[rcx + 0x18]`, `[rcx + 0x30]` -- so for those two the first argument is an SRET BUFFER and not `this`"),
        "witness": ("0x756EC0 `DelayedEngine::run` after `mov rdi, rcx` writes `dword ptr [rdi], 0` at 0x756F1C, `[rdi + 0x10]` at 0x756F2F, `[rdi + 0x18]` at 0x756F37, "
                    "moves the fifth argument in at 0x756F87 and takes `lea r8, [rdi + 0x30]` at 0x756FBC. **The four engines that DO dereference rcx cannot be told "
                    "apart from `this` by this test**, so the family is split and the split is recorded rather than averaged"),
        "round": 767,
    },
    {
        "subject": "engine-run-takes-five-arguments-not-four",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("every engine's `run` reads an argument from the stack, so it takes a FIFTH argument beyond the four registers, while the port's "
                      "`EngineBase::run(const void*, double, void*, void*)` declares four"),
        "witness": ("`0x759A94 mov r9, qword ptr [rsp + 0x60]` in `InfiniteEngine::run` -- **read AFTER the prologue's `sub rsp, 0x30` and `push rbx`, so it cannot be a "
                    "local**; and every one of the six reads a `[rsp + N]` above its own frame. **A method with a `this` and four more arguments has no room for an sret "
                    "pointer**, which is why the two findings are one problem: the port's signature has four arguments AND treats the first as `this`"),
        "round": 767,
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
