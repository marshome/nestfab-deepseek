# -*- coding: utf-8 -*-
"""Record the family map, the unresolved size contradiction, and the test that checks nothing."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

CLAIMS = [
    {
        "subject": "the-nester-family-has-two-layers-and-the-typeinfo-says-which",
        "grade": "DERIVATION",
        "kind": "call",
        "predicate": "four nesters derive from Multi::CompositeNester and two derive straight from Multi::Nester, read from each vtable's __si_class_type_info base pointer",
        "witness": ("the typeinfo names and base pointers: LimitedNester (vtable 0xA3B660) -> N5Multi15CompositeNesterE; FlipNester (0xA3B4A0) -> the same; "
                    "MultiTorchNester (0xA3B8B0) -> the same; FilterNester (0xA3B500) -> the same; NestingNester (0xA3B6A0) -> N5Multi6NesterE; DatabaseNester "
                    "(0xA3B750) -> the same. lcns/include/lcns/base_chain.hpp already recorded this split, and each of the four also calls the CompositeNester "
                    "constructor 0xB4DA0"),
        "round": 757,
    },
    {
        "subject": "the-nester-sizes-do-not-add-up-yet",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("the module allocates 0x28 bytes for FlipNester and MultiTorchNester, while Nester (0x18, three fields) plus a CompositeNester std::vector "
                      "(0x18) plus their own members is at least 0x30, so one of the two is wrong and it is NOT established which"),
        "witness": ("RE 0x2C953 and RE 0x2C591 are `mov ecx, 0x28` then `call 0x998500` then `call 0x4B570` and `0x780E0`; and 0xB4470 writes three fields after "
                    "the vptr, ending at 0x18. Declaring the CompositeNester inheritance makes FlipNester 0x30 bytes in the model, eight more than the module "
                    "allocates, so the four declarations were REVERTED rather than shipped knowingly too large"),
        "round": 757,
    },
    {
        "subject": "the-nester-size-test-compares-a-constant-to-itself",
        "grade": "INSTRUCTION",
        "kind": "call",
        "predicate": ("lcns/tests/test_recovered.cpp asserts each nester's allocation size against a constant defined from the same instruction and never compares "
                      "the model's sizeof, so a class larger than the module allocates passes"),
        "witness": ("the assertions are `CHECK(kFlipNesterBytes == 0x28)`, `CHECK(kLimitedNesterBytes == 0x48)` and so on, where those names are `inline constexpr` "
                    "in engine.hpp with the same value; declaring the CompositeNester inheritance makes sizeof(FlipNester) 0x30 and the suite still passes"),
        "round": 757,
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
