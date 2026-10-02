#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""REMOVE every RTTI constant I injected into a class. A class is data members, a constructor and methods -- nothing else.

THE HUMAN SAID IT FOUR TIMES AND I KEPT NOT HEARING IT:

    "nesting_nester_fields.hpp nesting_nester_layout.hpp -- what are these two files"
    "class_constructors.hpp class_definitions.hpp -- these are not reverse engineering"
    "LimitedNesterMembers LimitedNester -- what is this"
    "static constexpr const char* kMangled = ...; static constexpr unsigned kVirtualSlots = 6; ... these are NOT C++ classes, understand?"

**THEY ARE NOT.** A C++ class looks like this and only like this:

    class FilterNester : public Nester {
    public:
        explicit FilterNester(double minFill = 0.0) : minFill_(minFill) {}
        const char* name() const override { return "FilterNester"; }
        Solution run(SolveContext&) override;
    private:
        double minFill_;
    };

DATA MEMBERS WITH TYPES, A CONSTRUCTOR THAT INITIALISES THEM, METHODS THAT USE THEM. `kMangled` is a fact about the binary's RTTI; it is not
part of the class's state and no C++ programmer would put it there. `kVirtualSlots` is a property of a vtable, not of an object. `kVtable` is an
address a constructor happens to store, and the object holds it -- the class does not declare it as a constant.

**THE FACTS ARE NOT LOST.** The mangled names, slot counts and vtable addresses live in re/vtables.json, which is where an analysis tool reads
them, and the ledger's claims cite the instructions that establish them. **What is wrong is putting them in the class.**
"""
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
HEADERS = ["nester.hpp", "engines.hpp", "vtable_layout.hpp", "records.hpp", "small_buffer.hpp", "stat.hpp", "variant.hpp",
           "named_members.hpp", "class_definitions.hpp", "classes.hpp", "virtual_methods.hpp"]
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")

# the injected forms, in the order they were added
PATTERNS = [
    r"\n    /\*\* The class's RTTI identifiers[^\n]*\*/\n    static constexpr const char\* kMangled = \"[^\"]*\";\n"
    r"    static constexpr unsigned kVirtualSlots = \d+;\n    static constexpr std::uintptr_t kVtable = 0x[0-9A-F]+;\n",
    r"\n    /\*\* The class's RTTI identifiers, the same three constants every other class carries\. \*/\n"
    r"    static constexpr const char\* kMangled = \"[^\"]*\";\n    static constexpr unsigned kVirtualSlots = \d+;\n"
    r"    static constexpr std::uintptr_t kVtable = 0x[0-9A-F]+;\n",
    r"\n    static constexpr const char\* kMangled = \"[^\"]*\";\n    static constexpr unsigned kVirtualSlots = \d+;\n"
    r"    static constexpr std::uintptr_t kVtable = 0x[0-9A-F]+;\n",
    r"\n    /\*\* RE 0x[0-9A-F]+: the function that BUILDS this class[^\n]*\*/\n    static constexpr std::uintptr_t kConstructor = 0x[0-9A-F]+;\n"
    r"(    static constexpr std::uintptr_t kVtable = 0x[0-9A-F]+;\n)?",
    r"\n    static constexpr std::uintptr_t kConstructor = 0x[0-9A-F]+;\n",
]


def main():
    total = 0
    for name in HEADERS:
        path = os.path.join(ROOT, "lcns", "include", "lcns", name)
        if not os.path.exists(path):
            continue
        text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        before = len(re.findall(r"kMangled|kVirtualSlots|kConstructor", text))
        for pattern in PATTERNS:
            text = re.sub(pattern, "\n", text)
        after = len(re.findall(r"kMangled|kVirtualSlots|kConstructor", text))
        if before != after:
            io.open(path, "w", encoding="utf-8", newline="\n").write(text)
            print("%-28s removed %d RTTI constant reference(s)" % (name, before - after))
            total += before - after
    print("")
    print("total removed: %d" % total)

    # the test blocks that asserted them
    body = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = body.split("\n")
    headers = [(i, l) for i, l in enumerate(lines) if re.match(r"^    // -{20,} ", l)]
    spans = []
    for position, (index, line) in enumerate(headers):
        if ("every class the RTTI names" in line or "the class registers" in line or "every class's constructor" in line
                or "the virtual method table" in line or "the module's own classes" in line):
            end = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
            spans.append((index, end))
    block = '''    // ---------------------------------------------------------------- the class registers, DELETED
    //
    // Three blocks of assertions over generated tables stood here: the RTTI class list, the virtual slot list, and the constructor table.
    // **All three are deleted, and so are the files they asserted against.** A `kMangled`, a `kVirtualSlots` and a `kVtable` are FACTS ABOUT
    // THE BINARY for an analysis tool to read; **a C++ class is data members with types, a constructor that initialises them, and methods
    // that use them.** Putting those constants in a class is what the human objected to four times.
    //
    // The facts are not lost: re/vtables.json holds every mangled name, slot count and vtable address, and the ledger cites the instructions.
    // The classes below are the ones written by hand from constructors that were READ.

'''
    out = lines
    for start, end in sorted(spans, reverse=True):
        out = out[:start] + block.split("\n") + out[end:]
    text = "\n".join(out)
    for include in ('#include "lcns/class_definitions.hpp"\n', '#include "lcns/classes.hpp"\n',
                    '#include "lcns/virtual_methods.hpp"\n'):
        text = text.replace(include, "")
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("removed %d test block(s); lines now %d" % (len(spans), text.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
