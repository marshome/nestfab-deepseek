# -*- coding: utf-8 -*-
"""CORRECT the sret claim: the call sites prove `rcx` is `this`.

**WHAT LAST ROUND CONCLUDED**: "`InfiniteEngine::run` and `EquivalentEngine::run` never dereference `rcx`, so for those two the first argument is an SRET BUFFER and not
`this`."

**WHAT THE CALL SITES SHOW, IN THREE PLACES, ALL THE SAME SHAPE:**

    024040  mov rax, qword ptr [rbx]        ; rax = [rbx] = the vptr
    024043  mov rcx, rbx                    ; **rcx = the object**
    024046  call qword ptr [rax + 0x10]     ; through slot 2

**and the third site is unmistakable about what `rbx` is:**

    024878  lock sub dword ptr [rbx + 8], 1     ; a std::shared_ptr REFERENCE COUNT
    02487D  je 0x24885                          ; released at zero
    024885  mov rax, qword ptr [rbx]
    024888  mov rcx, rbx
    02488B  call qword ptr [rax + 0x10]         ; **and the object is STILL called after the count drops**

**SO `rcx` IS THE OBJECT, `this` IS IN `rcx` as the Itanium C++ ABI requires, and `EngineBase::run`'s first parameter is `this` after all.** The absence of a
dereference in two bodies is an absence of MEMBER USE and not evidence of sret -- **and `mov rax, rbx` in `InfiniteEngine::run` returns `this`, which is what the tree
originally said and what last round's "correction" overrode.**

**AND IT MAKES `DelayedEngine` A CLASS WITH DATA, WHICH IS THE USEFUL PART**: through `rdi` it writes a dword at +0x00, pointers at +0x10, +0x18, +0x20, +0x28, +0x38,
+0x40, +0x48 and +0x50, and dwords at +0x30 and +0x00 again -- **at least 0x54 bytes of members, and its declaration in the port has NONE.**
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

SUBJECT = "two-engines-run-return-by-sret-so-rcx-is-not-this"

CORRECTED = {
    "predicate": ("**WITHDRAWN -- `rcx` IS `this`.** Three call sites show the standard virtual-call shape `mov rax, [rbx]` / `mov rcx, rbx` / `call qword ptr [rax + "
                  "0x10]`, and one of them is preceded by `lock sub dword ptr [rbx + 8], 1` -- a `std::shared_ptr` count -- **so the object is in `rcx` and "
                  "`EngineBase::run`'s first parameter is `this` after all.**"),
    "witness": ("the sites are at 0x24040, 0x24210 and 0x24885, all the same shape; the third has `lock sub dword ptr [rbx + 8], 1` at 0x24878 with a release branch. "
                "**What misled last round is that `InfiniteEngine::run` and `EquivalentEngine::run` never DEREFERENCE `rcx` -- and an absence of member use is not "
                "evidence of sret.** `mov rax, rbx` in `InfiniteEngine::run` therefore returns `this`, which is what this tree originally said. **And the useful "
                "result is that `DelayedEngine` HAS data**: through `rdi` (= `rcx`) it writes a dword at +0x00, pointers at +0x10, +0x18, +0x20, +0x28, +0x38, +0x40, "
                "+0x48 and +0x50, and dwords at +0x30 -- **at least 0x54 bytes, and the port declares none**"),
    "round": 768,
}


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    for claim in data["claims"]:
        if claim.get("subject") == SUBJECT:
            claim.update(CORRECTED)
            print("corrected %s in place" % SUBJECT)
            break
    else:
        print("REFUSING: the claim is not in the ledger")
        return 2

    new = {
        "subject": "the-virtual-call-shape-settles-the-object-register",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("an engine is called through `mov rax, [rbx]` / `mov rcx, rbx` / `call qword ptr [rax + 0x10]`, so the object is in `rcx` and slot 2 takes "
                      "`this` first"),
        "witness": ("three sites, 0x24040, 0x24210 and 0x24885, all the same shape; at 0x24878 the third is preceded by `lock sub dword ptr [rbx + 8], 1` with a "
                    "release branch, which is a `std::shared_ptr` count and identifies `rbx` as an object. **AND NO DIRECT CALL TO ANY ENGINE'S `run` EXISTS**, so "
                    "this call shape is the only evidence there is -- and it is enough"),
        "round": 768,
    }
    if not any(existing.get("subject") == new["subject"] for existing in data["claims"]):
        data["claims"].append(new)
        print("added %s" % new["subject"])
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
