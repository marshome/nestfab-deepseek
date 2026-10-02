# -*- coding: utf-8 -*-
"""Fold class_constructors.hpp's one real fact into the classes, then delete the table.

WHAT THE FILE WAS: `{qualified, constructor address, vtable, field count, candidates, functionsWriting}` -- six columns of metadata. Its own
header called it "every class's constructor and the fields it writes", and it contains neither a constructor nor a field.

WHERE EACH COLUMN BELONGS, checked rather than assumed:

    vtable            already a constant in every generated class (kVtableRva) and in vtable_layout.hpp
    field count       countable from named_members.hpp, which declares the fields themselves
    candidates        a statistic about MY scan, not a fact about the module -- it says how many functions referenced a slot-0 address
    functionsWriting  likewise
    constructor       **the one real fact**: the address of the function that builds the class

So the address goes INTO the class as a named constant with its instruction, and the table is deleted. **A constant inside the class it belongs
to is C++; the same constant in a row keyed by a string name is a registry**, which is what this file was.
"""
import io
import json
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
DEFS = os.path.join(ROOT, "lcns", "include", "lcns", "class_definitions.hpp")
CTORS = os.path.join(ROOT, "lcns", "include", "lcns", "class_constructors.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")


def main():
    data = json.loads(io.open(os.path.join(ROOT, "re", "all_class_fields.json"), encoding="utf-8").read())
    # the constructor address per class, and the vtable, so both can be folded in together
    by_class = {}
    for entry in data["classes"]:
        if entry.get("constructor"):
            by_class[entry["class"]] = (int(entry["constructor"], 16), int(entry["vtable"], 16))

    text = io.open(DEFS, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    added = 0

    def fold(match):
        nonlocal added
        body = match.group(0)
        qualified = re.search(r"\*\* ([\w:]+) --", body)
        if not qualified:
            return body
        name = qualified.group(1)
        if name not in by_class:
            return body
        address, vtable = by_class[name]
        if "kConstructor" in body:
            return body
        short = name.split("::")[-1]
        added += 1
        insert = ("\n    /** RE 0x%X: the function that BUILDS this class, found by the vtable slot-0 address it installs. */\n"
                  "    static constexpr std::uintptr_t kConstructor = 0x%X;\n"
                  "    static constexpr std::uintptr_t kVtable = 0x%X;\n"
                  % (address, address, vtable))
        # after `public:` and the destructor, which is where a class's own constants belong
        return re.sub(r"(\npublic:\n    virtual ~%s\(\) = default;\n)" % re.escape(short),
                      r"\1" + insert, body, count=1)

    new_text = re.sub(r"/\*\* [\w:]+ -- vtable 0x[0-9A-F]+, \d+ virtual slot\(s\)\..*?\n\};", fold, text, flags=re.S)
    io.open(DEFS, "w", encoding="utf-8", newline="\n").write(new_text)
    print("folded kConstructor and kVtable into %d classes" % added)

    if os.path.exists(CTORS):
        os.remove(CTORS)
        print("deleted class_constructors.hpp")

    body = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = body.find("    // ---------------------------------------------------------------- every class's constructor (generated)")
    end = body.find("    // ---------------------------------------------------------------- the vtable layout (measured at 0xA3CFD0)")
    if start >= 0 and end > start:
        replacement = (
            "    // ---------------------------------------------------------------- every class's constructor, AS A MEMBER\n"
            "    //\n"
            "    // A `ClassConstructor` TABLE stood here: six columns keyed by class name, of which ONE was a fact about the module -- the\n"
            "    // address of the function that builds each class. The other five were the vtable (already a constant in each class), a field\n"
            "    // COUNT (countable from the declared fields) and two statistics about MY SCAN, which are not facts about the module at all.\n"
            "    // **The address is now `kConstructor` inside each class**, which is C++; the same number in a row keyed by a string is a\n"
            "    // registry, and this project already has the registries it needs.\n"
            "    {\n"
            "        using lcns::Multi::SplitNode;\n"
            "        using lcns::Multi::TerminalNode;\n"
            "        CHECK(SplitNode::kConstructor == 0x99910u);       // RE the slot-0 reference that finds it\n"
            "        CHECK(SplitNode::kVtable == 0xA3BB70u);\n"
            "        CHECK(TerminalNode::kConstructor == 0x99360u);\n"
            "        CHECK(TerminalNode::kVtable == 0xA3B570u);\n"
            "        // and a class whose constructor writes no field still knows its constructor, which the table could say only as a row\n"
            "        CHECK(SplitNode::kConstructor != TerminalNode::kConstructor);\n"
            "    }\n\n")
        body = body[:start] + replacement + body[end:]
        print("replaced the table's test block")
    if '#include "lcns/class_constructors.hpp"\n' in body:
        body = body.replace('#include "lcns/class_constructors.hpp"\n', "", 1)
        print("removed the include")
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
