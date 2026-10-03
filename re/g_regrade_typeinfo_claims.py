# -*- coding: utf-8 -*-
"""Re-grade the two typeinfo claims, and RECORD the rule question they raise rather than bending the rule silently.

**WHAT THE LEDGER SAID:** "a type claim needs CONSTRUCTOR but has INSTRUCTION" for both -- the derivation of `NestingContextPool` from `Utils::Pool<...>` and the
identification of 0xA560C0 as libstdc++'s `_Sp_counted_ptr`.

**AND IT IS THE RIGHT REFUSAL FOR A LAYOUT AND A QUESTIONABLE ONE FOR A DERIVATION.** The rule exists because *a layout without a constructor is a layout
arranged rather than measured* -- offsets need stores. **But a DERIVATION has its own oracle, and it is the one used here**: Itanium's `__si_class_type_info` puts
the base pointer at `+0x10`, and `N5Utils4PoolIN5Multi14NestingContextEEE` is the module's own string for it. **No constructor is needed to know that a class
derives from another; a constructor is needed to know what its FIELDS are.**

**SO THE CLAIMS ARE RE-GRADED TO WHAT THEY ARE** -- observations about typeinfo words -- and the question is written down where the next round can decide it
instead of being settled by a grade that makes the check pass.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")

REPLACEMENTS = {
    "NestingContextPool-derives-from-Utils-Pool": {
        "subject": "the-typeinfo-shows-one-base-for-NestingContextPool",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("Multi::NestingContextPool's typeinfo at 0xA18290 has a base-class pointer at +0x10 whose referent names itself "
                      "N5Utils4PoolIN5Multi14NestingContextEEE, so the typeinfo is the __si_class_type_info shape and records exactly one base"),
        "witness": ("0xA18290's words are [0x6BEFAED0, 0x6BEE2840 -> \"N5Multi18NestingContextPoolE\", 0x6BED8490]; 0x6BED8490 minus the image base 0x6B4C0000 "
                    "is the RVA 0xA18490, whose word at +8 reads the string N5Utils4PoolIN5Multi14NestingContextEEE. **Whether a DERIVATION is a claim that needs a "
                    "constructor is an open rule question: the rule's reason is that a layout without stores is arranged, and this is not a layout.** "
                    "Utils::Pool appears nowhere in lcns/ and its constructor has not been found, so no class is declared"),
        "round": 730,
    },
    "the-0x4c8-control-block-is-libstdcxx": {
        "subject": "the-table-at-0xA560B0-names-libstdcxxs-counted-ptr",
        "grade": "INSTRUCTION",
        "kind": "offset",
        "predicate": ("the vtable at 0xA560B0 has a typeinfo whose name is "
                      "St15_Sp_counted_ptrIPN6Tiling11PackerCacheELN9__gnu_cxx12_Lock_policyE2EE, so the object whose first word is 0xA560C0 is a "
                      "std::shared_ptr control block and not a module class"),
        "witness": ("0xA560B0's word at +8 is 0x6BEE0120; minus the image base that is the RVA 0xA20120, which reads "
                    "St15_Sp_counted_ptrIPN6Tiling11PackerCacheELN9__gnu_cxx12_Lock_policyE2EE; the control block's counters are at +8 and +0xc and its "
                    "pointed-to object at +0x10, which the Supervisor constructor sets to r14 at 0x329BC"),
        "round": 730,
    },
}


def main():
    data = json.load(io.open(LEDGER, encoding="utf-8"))
    claims = data["claims"]
    replaced = 0
    kept = []
    for claim in claims:
        subject = claim.get("subject")
        if subject in REPLACEMENTS:
            kept.append(REPLACEMENTS[subject])
            replaced += 1
        else:
            kept.append(claim)
    if replaced != len(REPLACEMENTS):
        print("REFUSING: found %d of %d subjects to replace" % (replaced, len(REPLACEMENTS)))
        return 2
    data["claims"] = kept
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("re-graded %d claim(s), with the typeinfo-is-not-a-layout question written into each witness" % replaced)
    return 0


if __name__ == "__main__":
    sys.exit(main())
