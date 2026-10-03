# -*- coding: utf-8 -*-
"""WITHDRAW the engine-base-size claim: 0x754DE0 is not evidenced to be an engine constructor.

**WHAT WAS CLAIMED**: "the engine base object carries a vptr and three pointers -- 0x20 bytes -- so the port's empty `EngineBase` is missing data", witnessed by RE 0x754DE0
copying a vptr and three qwords.

**WHAT IS ACTUALLY ESTABLISHED**: 0x754DE0 does those stores. **What is NOT established is that it has anything to do with the engine base**, and this round's refs scan
found that **no function anywhere in the image references any of the seven engine vtables** -- so nothing installs them and 0x754DE0 cannot be reached from one.

**AND THE POSITIVE COUNTER-EVIDENCE IS STRONGER THAN THE ABSENCE**: 0x754DE0's three callers are 2021, 1357 and 417 bytes, and `0x8F2AF0` -- the smallest -- begins
`mov qword ptr [rcx], 0` and is a large general routine. **A `mov [rcx], 0` followed by three qword copies is what a `std::function`, a `std::shared_ptr` or any
three-pointer value type does**, and connecting it to the engine base was a shape match.

**SO THE CLAIM IS CORRECTED IN PLACE, NOT DELETED.** The wrong half is named and the right half is kept: the base class's NAME and its THREE-SLOT surface are measured
from mangled names and vtable contents, and the size is not.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

WRONG = "the-engine-base-object-is-0x20-bytes"

CORRECTED = {
    "predicate": ("**WITHDRAWN -- the 0x20-byte claim is NOT supported.** RE 0x754DE0 copies a vptr and three qwords, and NOTHING establishes that it is an engine "
                  "constructor: no function in the image references any of the seven engine vtables, so nothing installs them, and 0x754DE0's three callers are "
                  "2021, 1357 and 417 bytes of general code. **The engine base's SIZE is therefore unknown**, and the port's empty `EngineBase` is not shown to be "
                  "missing data."),
    "witness": ("RE 0x754DE0 stores `mov qword ptr [rcx], 0`, reads the source's vptr and copies `[rdx]`, `[rdx + 8]`, `[rdx + 0x10]` and `[rdx + 0x18]` into rcx -- **but "
                "its callers are 0x754490 (2021 B), 0x8F21B0 (1357 B) and 0x8F2AF0 (417 B, and it opens with its own `mov qword ptr [rcx], 0`)**, none of which is an "
                "engine. And re/g_engine_vtable_refs.py finds **0 referencing functions for each of the seven engine vtables**. **A `mov [rcx], 0` plus three qword "
                "copies is a three-pointer value type, and matching that shape to an engine was the same error this project keeps finding: a pattern that fits where "
                "the mechanism was never traced.** The file also records what IS established: the base is `Engine::Engine`, and every engine has exactly three slots"),
    "round": 765,
}


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    for claim in data["claims"]:
        if claim.get("subject") != WRONG:
            continue
        claim.update(CORRECTED)
        print("corrected %s in place" % WRONG)
        break
    else:
        print("REFUSING: the claim to correct is not in the ledger")
        return 2
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
