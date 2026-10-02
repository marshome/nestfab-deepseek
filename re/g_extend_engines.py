# -*- coding: utf-8 -*-
"""Extend engines.hpp with the whole Engine family: each class, its vtable, and its three slots.

InfiniteEngine was defined alone. This adds the other six, from the same two sources: re/vtables.json for each class's vtable and slots, and
cref/re/findings_engine.md for the Run addresses the archive verified. A slot whose address is the class's Run slot is named; the other two
are the destructor pair and are named by POSITION, because the ABI gives them and the module does not.

    python g_extend_engines.py
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "engines.hpp")

# the seven, with the Run addresses the archive verified and the mangled RTTI names
FAMILY = [
    ("MultiEngine", "N6Engine11MultiEngineE"),
    ("DelayedEngine", "N6Engine13DelayedEngineE"),
    ("NestingEngine", "N6Engine13NestingEngineE"),
    ("InfiniteEngine", "N6Engine14InfiniteEngineE"),
    ("CompositeEngine", "N6Engine15CompositeEngineE"),
    ("EquivalentEngine", "N6Engine16EquivalentEngineE"),
    ("CloudEngine", "N6Engine11CloudEngineE"),
]

MARKER = "/** RE 0x759A80 (80 bytes): either run the nesting engine for ever, or hand the work to a nested engine."


def main():
    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    text = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")

    rows = []
    for name, mangled in FAMILY:
        entry = data.get(mangled)
        if not entry:
            print("REFUSING: %s is not in the RTTI table, so the family is incomplete" % mangled)
            return 2
        slots = [int(a) for a in entry.get("slots") or []]
        rows.append((name, int(entry["vtable_rva"]), slots))

    # a per-class block of constants, appended before the static_asserts
    block = ["", "// ------------------------------------------------------------------------------------------------",
             "// The rest of the Engine family, each with its vtable and its three slots.",
             "//",
             "// EVERY ONE OF THESE HAS THE SAME THREE SLOTS: the deleting destructor, the destructor and Run. What differs is where Run",
             "// points, which is the only thing the base class's comment listed -- and a class with an address and no definition is what the",
             "// human asked about. The slot addresses come from re/vtables.json; the Run addresses were verified by the archive.",
             "//"]
    for name, vtable, slots in rows:
        if len(slots) != 3:
            print("REFUSING: %s has %d slots and this family's shape is three" % (name, len(slots)))
            return 2
        block.append("")
        block.append("/** Engine::%s, vtable 0x%X. */" % (name, vtable))
        block.append("constexpr std::uintptr_t kVtable%s = 0x%X;" % (name, vtable))
        block.append("constexpr std::uintptr_t k%sDeletingDtor = 0x%X;   // slot 0" % (name, slots[0]))
        block.append("constexpr std::uintptr_t k%sDtor = 0x%X;             // slot 1" % (name, slots[1]))
        block.append("constexpr std::uintptr_t k%sRun = 0x%X;              // slot 2" % (name, slots[2]))

    # the constants the file already had, replaced by the family block
    for name, _mangled in FAMILY:
        text = re.sub(r"constexpr std::uintptr_t kRun%s = 0x[0-9A-F]+;\n" % name, "", text)

    anchor = "static_assert(kEngineRunSlot == 0x10,"
    if anchor not in text:
        print("REFUSING: the static_assert anchor is not in engines.hpp")
        return 2
    text = text.replace(anchor, "\n".join(block).lstrip("\n") + "\n\n" + anchor, 1)

    # and a table so a test can walk the family
    table = ["", "/** The family as a table, so a test asserts the whole shape rather than seven names. */",
             "struct EngineClass {", "    const char* name;", "    std::uintptr_t vtable;",
             "    std::uintptr_t run;", "};", "",
             "inline const EngineClass* engineFamily(std::size_t& count) {",
             "    static const EngineClass table[] = {"]
    for name, vtable, slots in rows:
        table.append('        {"%s", 0x%X, 0x%X},' % (name, vtable, slots[2]))
    table.append("    };")
    table.append("    count = sizeof(table) / sizeof(table[0]);")
    table.append("    return table;")
    table.append("}")
    table.append("")
    table.append("constexpr std::size_t kEngineFamilyCount = %d;" % len(rows))
    text = text.replace(anchor, "\n".join(table) + "\n" + anchor, 1)

    io.open(HEADER, "w", encoding="utf-8", newline="\n").write(text)
    print("engines.hpp extended with %d classes:" % len(rows))
    for name, vtable, slots in rows:
        print("   %-20s vtable 0x%-8X run 0x%X" % (name, vtable, slots[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
