# -*- coding: utf-8 -*-
"""Record what the `void*` turned out to be: a name collision with a second declaration of `Order`."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "the-void-pointer-was-a-name-collision",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("the export wrappers took `void*` because `lcns/api.hpp` declared `using Order = Order_t*` beside `lcns/model.hpp`'s `struct Order`, so a "
                      "signature saying `Order*` meant `Order_t**` and the generated code could not name the object it was handed"),
        "witness": ("the linker reported `defined: lcns::dll::exports::impl::setLocalMaximumThreads(lcns::Order*, int)` against `referenced: "
                    "lcns::dll::exports::impl::setLocalMaximumThreads(lcns::dll::Order_t**, int)`, which `nm -C` on the two object files confirms. The handle is now "
                    "`struct Order_t; using OrderHandle = Order_t*` and `re/g_opaque_collisions.py` measures the remaining seven collisions"),
        "round": 741,
    },
    {
        "subject": "the-two-local-engine-setters-are-typed",
        "grade": "CONSTRUCTOR",
        "kind": "offset",
        "predicate": ("setLocalMaximumThreads and setLocalMaximumIterations take `Order*` and write `maxThreads` at +0x1F8 and `maxIterations` at +0x1FC, rather "
                      "than taking `void*` and casting to LocalEngineCarrier"),
        "witness": ("LocalEngineCarrier's four fields and Order's are the same types at the same offsets -- std::uint32_t at +0x1F8 and +0x1FC, std::uint8_t at "
                    "+0x200 and +0x201 -- and the test now asserts `order.maxIterations` directly instead of memcpy at a hand-written offset. RE 0xD3D5 and "
                    "0xD3E7 store at +0x1F8 and 0xD417 stores at +0x1FC"),
        "round": 741,
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
