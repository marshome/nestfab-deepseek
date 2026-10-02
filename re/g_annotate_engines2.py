# -*- coding: utf-8 -*-
"""Annotate the remaining engines, and fix the byte count I had written wrong in CompositeEngine's body.

**THE MEASURED TABLES, from re/g_class_tables.py:**

    Engine::CloudEngine       0xA3CED0   3 slots   0x755000(70) 0x754FB0(71) 0x26A60(15430)
    Engine::MultiEngine       0xA3CF00   3 slots   0x7559E0(90) 0x755970(100) 0x755050(2329)
    Engine::DelayedEngine     0xA3CF70   3 slots   0x757200(71) 0x7571B0(76) 0x756EC0(750)
    Engine::NestingEngine     0xA3CFA0   3 slots   0x757A70(98) 0x757A10(94) 0x757250(1975)
    Engine::EquivalentEngine  0xA3D030   3 slots   0x75CB40(126) 0x75CAC0(123) 0x75BCC0(3569)

**AND ONE NUMBER IN THE TREE WAS WRONG**: `engines.cpp` says RE 0x755050 "is 3795 bytes" and the table says **2329**. The byte counts below come from
the same measurement as the addresses, so they agree with each other, and the wrong one is corrected where it stands.
"""
import io
import sys

ENGINES = r"D:\Nesting\nestfab\lcns\include\lcns\engines.hpp"
SOURCE = r"D:\Nesting\nestfab\lcns\src\engines.cpp"

TABLE = {
    "MultiEngine": ("0xA3CF00", "0x7559E0", "0x755970", "0x755050", 2329),
    "DelayedEngine": ("0xA3CF70", "0x757200", "0x7571B0", "0x756EC0", 750),
    "NestingEngine": ("0xA3CFA0", "0x757A70", "0x757A10", "0x757250", 1975),
    "EquivalentEngine": ("0xA3D030", "0x75CB40", "0x75CAC0", "0x75BCC0", 3569),
    "CloudEngine": ("0xA3CED0", "0x755000", "0x754FB0", "0x26A60", 15430),
}


def main():
    text = io.open(ENGINES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    changed = 0
    for name, (vtable, slot0, slot1, run, size) in TABLE.items():
        needle = "class %s" % name
        index = text.find(needle)
        if index < 0:
            print("   %-18s not found" % name)
            continue
        # INSERT THE ADDRESS INTO THE CLASS'S OWN DOC COMMENT rather than adding a second one, because a second comment about the same class is the
        # duplication this project checks for
        comment = text.rfind("/**", 0, index)
        if comment >= 0 and text.count("*/", comment, index) == 1:
            block = text[comment:index]
            if "vtable 0x" in block:
                continue
            if "Not read." in block:
                block = block.replace(
                    "Not read.",
                    "Not read. **RE vtable %s, THREE slots**: 0x%s is the deleting destructor, 0x%s the destructor, and slot 2 is `run` at\n *  0x%s, %d bytes -- **the slot-2 address DIFFERS IN ALL SEVEN ENGINES**, which is why slot 2 is the class's one virtual." %
                    (vtable, slot0, slot1, run, size))
                text = text[:comment] + block + text[index:]
                changed += 1
                continue
        print("   %-18s has no single doc comment to extend" % name)

    io.open(ENGINES, "w", encoding="utf-8", newline="\n").write(text)
    print("annotated %d engine(s)" % changed)

    source = io.open(SOURCE, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "3795 bytes" in source:
        source = source.replace("3795 bytes", "2329 bytes, MEASURED -- an earlier note said 3795 and the table says 2329")
        io.open(SOURCE, "w", encoding="utf-8", newline="\n").write(source)
        print("corrected RE 0x755050's byte count in engines.cpp")
    return 0


if __name__ == "__main__":
    sys.exit(main())
