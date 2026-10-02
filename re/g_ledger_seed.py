# -*- coding: utf-8 -*-
"""Seed re/ledger.json from re/LEDGER.md, so the typed store and the readable page agree from the start."""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ledger  # noqa: E402

SEED = [
    ("CONSTRUCTOR", "LaunchingOrder.size", "0x2C0 bytes", "RE 0x14620 allocates 0x2C0 through operator new at 0x998500", "layout", 538),
    ("ORACLE", "LaunchingOrder.automaticStop", "field at +0x240", "export SetAutomaticStop (140) stores at RE 0xE0D9; RE 0x22BC1 reads it", "name", 537),
    ("INSTRUCTION", "LaunchingOrder.multiplicityPreference", "double at +0x010", "RE 0xD255 and RE 0x14668 are movsd", "width", 540),
    ("INSTRUCTION", "LaunchingOrder.origin", "dword at +0x00C", "RE 0xD119, SetOrigin (86)", "offset", 537),
    ("INSTRUCTION", "CnsNode.ownership", "the string at +0x20 is owned iff it is not the node's own +0x30", "RE 0x9308C0 compares before freeing", "offset", 530),
    ("DIFFERENTIAL", "CnsNode.copy_and_release", "0x9302C0 and 0x9308C0 are recovered", "lcns/tests/test_recovered.cpp runs both halves of the ownership rule", "equivalence", 530),
    ("MEASURED", "Module.classes", "75 classes of this module", "re/vtables.json filtered on the MANGLED name, not the decoded one", "constant", 538),
    ("MEASURED", "Multi::RowNester.vtable", "0xA3BB30", "re/vtables.json slot 5 is 0x913E0, the Run body in re/STRATEGY_METHODS.md", "constant", 539),
    ("SHAPE", "parent+0x40.subobject", "a sub-object with fields +0x10..+0x38", "15 functions derive its address with lea; no constructor read", "shape", 539),
    ("SHAPE", "element50.layout", "begins +0x10 +0x18 +0x20", "57 functions compute a 0x50 byte element address; several element registers per body", "shape", 539),
    ("SHAPE", "ToJson.keys", "the keys name the solution's fields", "the keys are oracle-grade strings but the key-to-offset pairing picks the wrong accessor", "shape", 535),
    ("SHAPE", "Multi::Run bodies", "twelve strategies' Run bodies are not recovered", "re/STRATEGY_METHODS.md lists them; their classes are now identifiable", "shape", 539),
]


def main():
    data = ledger.load()
    if data["claims"]:
        print("re/ledger.json already has %d claims" % len(data["claims"]))
        return 0
    for grade, subject, predicate, witness, kind, round_number in SEED:
        entry = ledger.add(data, grade, subject, predicate, witness, round_number)
        entry["kind"] = kind
    ledger.save(data)
    print("seeded %d claims" % len(data["claims"]))
    problems = ledger.check(data)
    for problem in problems:
        print("PROBLEM: %s" % problem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
