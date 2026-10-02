# -*- coding: utf-8 -*-
"""Annotate the seven concrete engines with their measured vtables, and record Engine::Engine as the base they all have.

**MEASURED, FROM re/g_class_tables.py:**

    Engine::CloudEngine       0xA3CED0   3 slots   0x755000(70) 0x754FB0(71) 0x26A60(15430)
    Engine::MultiEngine       0xA3CF00   3 slots   0x7559E0(90) 0x755970(100) 0x755050(2329)
    Engine::DelayedEngine     0xA3CF70   3 slots   0x757200(71) 0x7571B0(76) 0x756EC0(750)
    Engine::NestingEngine     0xA3CFA0   3 slots   0x757A70(98) 0x757A10(94) 0x757250(1975)
    Engine::InfiniteEngine    0xA3CFD0   3 slots   0x759B20(71) 0x759AD0(76) 0x759A80(80)
    Engine::CompositeEngine   0xA3D000   3 slots   0x75BC30(137) 0x75BBA0(129) 0x759B70(8230)
    Engine::EquivalentEngine  0xA3D030   3 slots   0x75CB40(126) 0x75CAC0(123) 0x75BCC0(3569)

**so `Engine::Engine` has exactly one virtual of its own, `run`, at slot 2** -- and each concrete engine implements it, which is why the slot DIFFERS in
all seven and the class is abstract. **And the earlier note that 0x755050 is 3795 bytes was wrong; the table says 2329.** The byte counts here come
from the same measurement as the addresses, so they agree with each other.
"""
import io
import sys

ENGINES = r"D:\Nesting\nestfab\lcns\include\lcns\engines.hpp"

# class -> (vtable, destructor slot0, destructor slot1, run slot2 and its size)
TABLE = {
    "CloudEngine": ("0xA3CED0", "0x755000", "0x754FB0", "0x26A60", 15430),
    "MultiEngine": ("0xA3CF00", "0x7559E0", "0x755970", "0x755050", 2329),
    "DelayedEngine": ("0xA3CF70", "0x757200", "0x7571B0", "0x756EC0", 750),
    "NestingEngine": ("0xA3CFA0", "0x757A70", "0x757A10", "0x757250", 1975),
    "InfiniteEngine": ("0xA3CFD0", "0x759B20", "0x759AD0", "0x759A80", 80),
    "CompositeEngine": ("0xA3D000", "0x75BC30", "0x75BBA0", "0x759B70", 8230),
    "EquivalentEngine": ("0xA3D030", "0x75CB40", "0x75CAC0", "0x75BCC0", 3569),
}

BASE_NOTE = '''/** **RE the seven tables below: ONE VIRTUAL, AND IT IS `run`.** Every concrete engine has exactly three slots --
 *
 *      0x755000..0x75CB40   the deleting destructor, 70 to 137 bytes
 *      0x754FB0..0x75CAC0   the destructor
 *      slot 2, DIFFERENT IN ALL SEVEN   `run`, 80 bytes for `InfiniteEngine` and 15430 for `CloudEngine`
 *
 *  -- so **the base's surface is that one method**, and the class is abstract because every derived class implements it. There is no vtable for
 *  `Engine::Engine` ITSELF in re/vtables.json because an abstract base has no instantiated table, which is the same reason the whole base layer was
 *  missing from this tree. **`Engine::InfiniteEngine`'s own constructor is NOT in the profile either** -- the three functions that install its
 *  vtable pointer are its two destructors and another class's constructor, recorded in the ledger. */
'''


def main():
    text = io.open(ENGINES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    changed = 0
    for name, (vtable, slot0, slot1, run, size) in TABLE.items():
        needle = "class %s" % name
        index = text.find(needle)
        if index < 0:
            print("   %-22s not found" % name)
            continue
        # skip a class that already carries its vtable address
        if vtable in text[max(0, index - 700):index]:
            continue
        # back up over the doc comment that belongs to the class, so the table goes ABOVE it
        start = index
        comment = text.rfind("/**", 0, index)
        if comment >= 0 and text.count("*/", comment, index) == 1:
            start = comment
        else:
            while start > 0 and text[start - 1] in " \t":
                start -= 1
            line = text.rfind("\n", 0, start) + 1
            start = line
        note = ("/** RE vtable %s, THREE slots. Slot 0 is the deleting destructor %s, slot 1 the destructor %s, and slot 2 is `run` at %s, %d bytes.\n"
                " *  **The slot-2 address DIFFERS IN ALL SEVEN ENGINES**, which is why slot 2 is the class's one virtual and the base is abstract. */\n"
                % (vtable, slot0, slot1, run, size))
        text = text[:start] + note + text[start:]
        changed += 1

    if "RE the seven tables below" in text:
        print("the Engine::Engine comment is already present")
    else:
        index = text.find("class EngineBase")
        if index < 0:
            print("REFUSING: EngineBase is not found; the engines' base declaration is elsewhere")
        else:
            text = text[:index] + BASE_NOTE + text[index:]
            changed += 1

    io.open(ENGINES, "w", encoding="utf-8", newline="\n").write(text)
    print("annotated %d place(s)" % changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
