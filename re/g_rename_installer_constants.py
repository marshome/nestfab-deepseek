# -*- coding: utf-8 -*-
"""Rename the mis-named constants in the classes, from the classifier's verdict.

THE DEFECT THE HUMAN FOUND, and the whole reason this exists: `static constexpr std::uintptr_t kConstructor = 0x75E0E0` where 0x75E0E0 is the
class's DESTRUCTOR. **A constant whose NAME asserts more than its evidence is the same defect as a member named after its offset**, and it is
worse here because a reader trusts it.

So each class's constant is renamed to what the classifier established, and where the classifier cannot tell, the constant is `kVtableInstaller`
and says so. **An honest unknown beats a confident wrong name.**
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KINDS = os.path.join(HERE, "vtable_installer_kinds.json")

OLD = ('    /** RE 0x%X: the function that BUILDS this class, found by the vtable slot-0 address it installs. */\n'
       '    static constexpr std::uintptr_t kConstructor = 0x%X;')

NEW = {
    "constructor": (
        '    /** RE 0x%X: the CONSTRUCTOR. It installs the vtable at the address below and neither frees nor releases before doing so --\n'
        '     *  which is what distinguishes it from the destructor, whose own vtable install is followed by a release. The classification\n'
        '     *  and its self-check are in re/g_classify_vtable_installer.py. */\n'
        '    static constexpr std::uintptr_t kConstructor = 0x%X;\n'
        '    static constexpr std::uintptr_t kVtableInstaller = 0x%X;'),
    "destructor": (
        '    /** RE 0x%X: **THIS IS NOT THE CONSTRUCTOR.** It is the DESTRUCTOR: it installs the vtable and then RELEASES, by an atomic\n'
        '     *  refcount decrement or a tail call to the allocator. A destructor installs the vtable too, which is why a detector that looked\n'
        '     *  only for the install could not tell them apart. Classified in re/g_classify_vtable_installer.py. */\n'
        '    static constexpr std::uintptr_t kDestructor = 0x%X;\n'
        '    static constexpr std::uintptr_t kVtableInstaller = 0x%X;'),
    "unknown": (
        '    /** RE 0x%X: a function that installs this class\'s vtable, and the evidence does NOT say whether it CONSTRUCTS or DESTROYS.\n'
        '     *  **An honest unknown beats a confident wrong name** -- the first version of this constant was called `kConstructor` and was the\n'
        '     *  destructor. Classified in re/g_classify_vtable_installer.py. */\n'
        '    static constexpr std::uintptr_t kVtableInstaller = 0x%X;'),
}


def main():
    kinds = json.loads(io.open(KINDS, encoding="utf-8").read())
    paths = [os.path.join(ROOT, "lcns", "include", "lcns", name)
             for name in ("class_definitions.hpp", "nester.hpp", "engines.hpp")]
    totals = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        changed = 0
        for name, info in kinds.items():
            address = int(info["address"], 16)
            kind = info["kind"]
            old = OLD % (address, address)
            if old not in text:
                continue
            new = NEW[kind] % ((address, address, address) if kind == "constructor"
                               else ((address, address) if kind == "destructor" else (address,)))
            text = text.replace(old, new, 1)
            changed += 1
            totals[kind] = totals.get(kind, 0) + 1
        if changed:
            io.open(path, "w", encoding="utf-8", newline="\n").write(text)
            print("%s: %d constant(s) renamed" % (os.path.basename(path), changed))
    print("")
    for kind in sorted(totals):
        print("   %-12s %d" % (kind, totals[kind]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
