# -*- coding: utf-8 -*-
"""Put the four slot constants into vtable_layout.hpp, which is a real type, and repoint the test at it.

`virtual_methods.hpp` was deleted as a table, and it carried four constants the test uses. **They belong in vtable_layout.hpp**, which describes
the SAME layout and is a type rather than a registry -- so folding them there keeps one description of the vtable layout instead of two.
"""
import io
import os
import sys

ROOT = r"D:\Nesting\nestfab"
LAYOUT = os.path.join(ROOT, "lcns", "include", "lcns", "vtable_layout.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")

CONSTANTS = '''
// ------------------------------------------------------------------------------------------------
// THE SLOT POSITIONS, from the same dump. The first two are the destructor pair for every polymorphic class in this ABI, so slot 2 is the
// first DECLARED virtual -- which is why an Engine's slot 2 is `Run` and a Nester's slot 2 is not.

/** Slot 2, what the engine call site at 0x2516E reaches. */
constexpr unsigned kEngineRunSlotIndex = 2;
constexpr std::uintptr_t kEngineRunSlotAddress = 0x759A80;   // RE 0x759A80 is slot 2 of Engine::InfiniteEngine

/** The destructor pair, by POSITION: the names are this ABI's and not the module's, which is why they are named for where they sit. */
constexpr unsigned kDeletingDestructorSlot = 0;
constexpr unsigned kDestructorSlot = 1;

'''


def main():
    text = io.open(LAYOUT, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "kEngineRunSlotIndex" not in text:
        marker = "static_assert(kVtableAddressPointOffset == 0x10,"
        assert marker in text, "the layout header's first assert is gone"
        text = text.replace(marker, CONSTANTS.lstrip("\n") + marker, 1)
        io.open(LAYOUT, "w", encoding="utf-8", newline="\n").write(text)
        print("added the four slot constants to vtable_layout.hpp")

    body = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    for include in ('#include "lcns/virtual_methods.hpp"\n', '#include "lcns/classes.hpp"\n'):
        if include in body:
            body = body.replace(include, "", 1)
            print("removed %s" % include.strip())
    if '#include "lcns/vtable_layout.hpp"' not in body:
        anchor = '#include "lcns/class_definitions.hpp"\n'
        assert anchor in body, "the class_definitions include is gone"
        body = body.replace(anchor, anchor + '#include "lcns/vtable_layout.hpp"\n', 1)
        print("added the vtable_layout include")
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
