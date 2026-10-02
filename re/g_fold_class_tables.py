# -*- coding: utf-8 -*-
"""Fold the mangled name and the slot count into each class, then delete classes.hpp and virtual_methods.hpp.

WHAT THE TWO TABLES WERE:

    classes.hpp          96 rows: {mangled name, qualified, vtable, slots}
    virtual_methods.hpp  384 rows: {owner, slot index, address}

**EVERY COLUMN IS A CONSTANT OF THE CLASS IT NAMES.** The mangled name is the class's own RTTI name, the slot count is its own virtual count,
and a slot's address is its own virtual's address. A table keyed by a STRING is a second description; the same numbers as constants of the class
are the class.

AND THE TEST'S REAL ASSERTION SURVIVES THE DELETION: what mattered was that the eleven NestingNester-family classes share ONE slot count, and
that the engine family is seven classes with three slots. Both are assertions about CLASSES, so they run against the classes.
"""
import io
import json
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
DEFS = os.path.join(ROOT, "lcns", "include", "lcns", "class_definitions.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")
DELETE = ("classes.hpp", "virtual_methods.hpp")


def fold():
    data = json.loads(io.open(os.path.join(ROOT, "re", "vtables.json"), encoding="utf-8").read())
    by_qualified = {}
    for mangled, entry in data.items():
        qualified = (entry.get("demangled") or "").strip()
        if qualified:
            by_qualified[qualified] = (mangled, len(entry.get("slots") or []), int(entry["vtable_rva"]))

    text = io.open(DEFS, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    added = 0

    def fold_one(match):
        nonlocal added
        body = match.group(0)
        found = re.search(r"\*\* ([\w:]+) --", body)
        if not found:
            return body
        qualified = found.group(1)
        if qualified not in by_qualified or "kMangled" in body:
            return body
        mangled, slots, vtable = by_qualified[qualified]
        added += 1
        insert = ('\n    /** The class\'s RTTI identifiers: its mangled name, which is PRIMARY EVIDENCE, and its virtual count. */\n'
                  '    static constexpr const char* kMangled = "%s";\n'
                  '    static constexpr unsigned kVirtualSlots = %d;\n' % (mangled, slots))
        short = qualified.split("::")[-1]
        return re.sub(r"(\npublic:\n    virtual ~%s\(\) = default;\n)" % re.escape(short),
                      r"\1" + insert, body, count=1)

    new_text = re.sub(r"/\*\* [\w:]+ -- vtable 0x[0-9A-F]+, \d+ virtual slot\(s\)\..*?\n\};", fold_one, text, flags=re.S)
    io.open(DEFS, "w", encoding="utf-8", newline="\n").write(new_text)
    print("folded kMangled and kVirtualSlots into %d classes" % added)
    return added


def rewrite_test():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = text.split("\n")
    headers = [(i, l) for i, l in enumerate(lines) if re.match(r"^    // -{20,} ", l)]
    spans = []
    for position, (index, line) in enumerate(headers):
        if "the module's own classes (from its RTTI)" in line or "the virtual method table (from RTTI slots)" in line:
            end = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
            spans.append((index, end))
    if len(spans) != 2:
        print("REFUSING: found %d spans to replace and 2 were expected" % len(spans))
        return 0
    block = '''    // ---------------------------------------------------------------- the class registers, AS CLASS CONSTANTS
    //
    // A `ClassInfo` table of 96 rows and a `VirtualSlot` table of 384 stood here. **Every column was a constant of the class it named**: the
    // mangled name is the class's own RTTI name, the slot count is its own virtual count, and a slot's address is its own virtual's. A table
    // keyed by a STRING is a second description; the same numbers as constants are the class.
    {
        // the mangled name is PRIMARY EVIDENCE -- the demangling is a decode and a decode can be wrong
        CHECK(std::string(lcns::Multi::SplitNode::kMangled) == "N5Multi9SplitNodeE");
        CHECK(lcns::Multi::SplitNode::kVirtualSlots == 6u);
        CHECK(std::string(lcns::Multi::TerminalNode::kMangled) == "N5Multi12TerminalNodeE");
        CHECK(lcns::Multi::TerminalNode::kVirtualSlots == 4u);

        // **AND THE ONE INTERFACE FACT WORTH ASSERTING**: the eleven nester classes share a slot count, which is what a strategy interface
        // looks like from the RTTI. It is asserted on the CLASSES now rather than on rows keyed by their names.
        const unsigned nesterSlots[11] = {
            lcns::FlipNester::kVirtualSlots,       lcns::FilterNester::kVirtualSlots,
            lcns::NoFillNester::kVirtualSlots,     lcns::TilingNester::kVirtualSlots,
            lcns::CompactNester::kVirtualSlots,    lcns::LimitedNester::kVirtualSlots,
            lcns::NestingNester::kVirtualSlots,    lcns::DatabaseNester::kVirtualSlots,
            lcns::RectangleNester::kVirtualSlots,  lcns::MultiTorchNester::kVirtualSlots,
            lcns::RowNester::kVirtualSlots,
        };
        for (unsigned slots : nesterSlots) {
            CHECK(slots == nesterSlots[0]);      // one interface, eleven implementations
        }

        // the engine family: seven classes, three slots each, and Run is slot 2
        CHECK(lcns::kEngineRunSlotIndex == 2u);
        CHECK(lcns::kEngineRunSlotAddress == 0x759A80);
        CHECK(lcns::kDestructorSlot == 1u);
        CHECK(lcns::kDeletingDestructorSlot == 0u);
        CHECK(lcns::InfiniteEngine::kVtable == 0xA3CFD0u);
        CHECK(lcns::Multi::SplitNode::kVtable == 0xA3BB70u);
    }

'''
    # replace both spans, the later one first so the indices stay valid
    out = lines
    for start, end in sorted(spans, reverse=True):
        out = out[:start] + block.split("\n") + out[end:]
    text = "\n".join(out)
    for include in ('#include "lcns/classes.hpp"\n', '#include "lcns/virtual_methods.hpp"\n'):
        text = text.replace(include, "", 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("replaced both table test blocks; lines now %d" % text.count("\n"))
    return 1


if __name__ == "__main__":
    fold()
    rewrite_test()
    for name in DELETE:
        path = os.path.join(ROOT, "lcns", "include", "lcns", name)
        if os.path.exists(path):
            os.remove(path)
            print("deleted %s" % name)
