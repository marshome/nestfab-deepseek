#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Tell a vtable installer's KIND from the ORDER of what it does, not from whether an atomic appears anywhere.

TWO WRONG CLASSIFIERS BEFORE THIS ONE, and each failure is why the final rule is about ORDER:

  1. "a function that references the vtable's slot-0 address" -- **true of a constructor AND a destructor**, because both install the vtable.
     That is the claim the human caught: `kConstructor = 0x75E0E0` was the class's DESTRUCTOR.

  2. "any atomic operation, tail call to the allocator, or virtual call makes it a destructor" -- **FALSE POSITIVES**. It called
     Multi::NestingNester's constructor 0x342E0 a destructor, because that function's MT19937 seeding loop is followed by a `lock sub` on a
     MEMBER's refcount:

         0x3439A  mov rsi, [rsp + 0x28]        ; a member it took earlier
         0x343A2  je ...
         0x343A4  lock sub dword [rsi + 8], 1  ; decrementing THAT member, not freeing this object

     A constructor that holds a shared_ptr does exactly that. **An atomic anywhere is not the signature.**

  THE SIGNATURE IS THE ORDER. A destructor INSTALLS ITS OWN VTABLE AND THEN RELEASES THINGS; a constructor calls its BASE first and installs
  the vtable afterwards, or has no atomic at all. So the test is: does the FIRST write to the object's +0 precede every atomic, with the
  atomic acting on the object the vtable was installed into?

    python -u g_classify_vtable_installer.py
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

FAMILY = ["MultiEngine", "DelayedEngine", "NestingEngine", "InfiniteEngine", "CompositeEngine", "EquivalentEngine", "CloudEngine"]


def classify(function, profile):
    """(kind, reason) from the ORDER of the vtable install relative to the first atomic, plus a tail call to the allocator."""
    size = (profile.get(function) or {}).get("size") or 0
    if not size:
        return "unknown", "no body in the profile"

    install_at = None            # the address that stores a vtable into the object
    first_atomic = None
    tail_to_free = None
    lines = []
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        lines.append(instruction)
        text = instruction.op_str
        # a store of a rip-relative address into [reg] at offset 0 -- the vtable install. The object register is the FIRST argument's, and
        # the store is to its own +0.
        if instruction.mnemonic == "mov" and re.match(r"^qword ptr \[\w+\], \w+$", text):
            install_at = instruction.address if install_at is None else install_at
        if instruction.mnemonic.startswith("lock") and first_atomic is None:
            first_atomic = instruction.address
        if instruction.mnemonic == "jmp" and "0x9984b0" in text:
            tail_to_free = instruction.address

    if install_at is not None and tail_to_free is not None:
        return "destructor", ("installs its own vtable at 0x%X and TAIL CALLS the allocator at 0x%X, which is the freeing destructor"
                              % (install_at, tail_to_free))
    if install_at is not None and first_atomic is not None and first_atomic < install_at:
        return "destructor", "does an atomic at 0x%X BEFORE installing the vtable at 0x%X" % (first_atomic, install_at)
    if install_at is not None:
        return "constructor", "installs the vtable at 0x%X and neither frees nor releases before it" % install_at
    return "unknown", "no vtable install found, so this is neither"


def main():
    profile = load_prof()
    data = json.loads(io.open(os.path.join(HERE, "all_class_fields.json"), encoding="utf-8").read())

    # THE SELF-CHECK: two functions whose kind is ESTABLISHED by reading them.
    #   0x342E0 is Multi::NestingNester's CONSTRUCTOR -- it seeds a 624 word Mersenne Twister, which is construction and not destruction.
    #   0x75E0E0 is Engine::EquivalentObserver's DESTRUCTOR -- it tail calls the allocator after releasing a refcounted sub-object.
    known = {0x342E0: "constructor", 0x75E0E0: "destructor"}
    print("SELF-CHECK on functions whose kind was established by reading them:")
    ok = True
    for address, expected in known.items():
        kind, reason = classify(address, profile)
        mark = "OK" if kind == expected else "WRONG"
        if kind != expected:
            ok = False
        print("   0x%-8X expected %-12s got %-12s %s" % (address, expected, kind, mark))
        print("              %s" % reason)
    if not ok:
        print("")
        print("REFUSING TO REPORT: the classifier disagrees with a function whose kind is known.")
        return 2
    print("")

    verdicts = {}
    for entry in data["classes"]:
        if not entry.get("constructor"):
            continue
        address = int(entry["constructor"], 16)
        kind, reason = classify(address, profile)
        verdicts[entry["class"]] = (address, kind, reason)

    counts = {}
    for _n, (_a, kind, _r) in verdicts.items():
        counts[kind] = counts.get(kind, 0) + 1
    print("the %d functions the field scan called constructors, by kind:" % len(verdicts))
    for kind in sorted(counts):
        print("   %-12s %d" % (kind, counts[kind]))
    print("")
    for name, (address, kind, reason) in sorted(verdicts.items()):
        if kind != "constructor":
            print("   0x%-8X %-34s %-12s %s" % (address, name[:34], kind.upper(), reason))

    payload = {name: {"address": "0x%X" % address, "kind": kind, "reason": reason}
               for name, (address, kind, reason) in verdicts.items()}
    io.open(os.path.join(HERE, "vtable_installer_kinds.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(payload, indent=1, sort_keys=True))
    print("")
    print("wrote re/vtable_installer_kinds.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
