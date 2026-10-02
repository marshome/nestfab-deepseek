# -*- coding: utf-8 -*-
"""Add the RTTI constants to the HAND-WRITTEN nester classes, which the generated file cannot reach.

`class_definitions.hpp` declares the classes nobody had written yet, and folding a constant into it does nothing for `FlipNester`, which lives
in nester.hpp with a name(), a constructor and a run(). **A class that exists gets its constants in its own declaration**, wherever that is --
so this puts `kMangled`, `kVirtualSlots` and `kVtable` into each nester that is hand-written, and then the 12 generated duplicates in
class_definitions.hpp are replaced by nothing at all, because a class that exists does not get a second declaration.
"""
import io
import json
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
NESTER = os.path.join(ROOT, "lcns", "include", "lcns", "nester.hpp")
DEFS = os.path.join(ROOT, "lcns", "include", "lcns", "class_definitions.hpp")


def rtti():
    data = json.loads(io.open(os.path.join(ROOT, "re", "vtables.json"), encoding="utf-8").read())
    out = {}
    for mangled, entry in data.items():
        qualified = (entry.get("demangled") or "").strip()
        if qualified:
            out[qualified.split("::")[-1]] = (mangled, len(entry.get("slots") or []), int(entry["vtable_rva"]))
    return out


def main():
    table = rtti()
    text = io.open(NESTER, encoding="utf-8", newline="").read().replace("\r\n", "\n")

    # EVERY hand-written class in this header gets its RTTI constants, at the top of its public section. The insertion point is the class's
    # own `public:` so the constants sit with the rest of the interface rather than in a table keyed by a string.
    # EVERY hand-written class in this header gets its RTTI constants. THE MATCH ALLOWS A COMMENT AND A NEWLINE between the class head and
    # `public:` -- a first version required them adjacent and reached only 5 of the 17 classes, which is the kind of silent partial result
    # this project keeps recording.
    added = 0
    pattern = re.compile(r"^(class (\w+)\b[^\n]*\n(?:public:\n| \*[^\n]*\n(?:\s*\*[^\n]*\n)*public:\n))", re.M)

    def inject(match):
        nonlocal added
        head, short = match.group(1), match.group(2)
        if short not in table or "kMangled" in text[match.end():match.end() + 1200]:
            return head
        mangled, slots, vtable = table[short]
        added += 1
        return (head
                + '    /** The class\'s RTTI identifiers: the MANGLED name, which is primary evidence, and its virtual count. */\n'
                + '    static constexpr const char* kMangled = "%s";\n' % mangled
                + '    static constexpr unsigned kVirtualSlots = %d;\n' % slots
                + '    static constexpr std::uintptr_t kVtable = 0x%X;\n\n' % vtable)

    text = pattern.sub(inject, text)
    io.open(NESTER, "w", encoding="utf-8", newline="\n").write(text)
    print("added the RTTI constants to %d hand-written classes in nester.hpp" % added)

    # and the generated duplicates go: a class that exists does not get a second declaration
    defs = io.open(DEFS, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    hand = set(re.findall(r"\b(?:class|struct)\s+(\w+)", text))
    removed = 0

    def drop(match):
        nonlocal removed
        body = match.group(0)
        found = re.search(r"class (\w+) \{", body)
        if found and found.group(1) in hand:
            removed += 1
            return ("/** %s -- DECLARED IN nester.hpp, which has its name(), its constructor and its run(). A class that exists does not get a\n"
                    " *  second declaration here. */" % found.group(1))
        return body

    defs = re.sub(r"/\*\* [\w:]+ -- vtable 0x[0-9A-F]+, \d+ virtual slot\(s\)\..*?\n\};", drop, defs, flags=re.S)
    io.open(DEFS, "w", encoding="utf-8", newline="\n").write(defs)
    print("replaced %d generated duplicates with a note" % removed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
