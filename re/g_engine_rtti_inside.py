# -*- coding: utf-8 -*-
"""The engine RTTI constants belong INSIDE the engine classes, not in a namespace of the same name.

`namespace InfiniteEngine` collides with `class InfiniteEngine`, and the collision is the point: **a namespace and a class cannot share a name,
and the constants are the class's own.** They go in as static members, which is the same shape every other class in the project uses.
"""
import io
import json
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
ENGINES = os.path.join(ROOT, "lcns", "include", "lcns", "engines.hpp")
FAMILY = ["MultiEngine", "DelayedEngine", "NestingEngine", "InfiniteEngine", "CompositeEngine", "EquivalentEngine", "CloudEngine"]


def main():
    data = json.loads(io.open(os.path.join(ROOT, "re", "vtables.json"), encoding="utf-8").read())
    rtti = {}
    for mangled, entry in data.items():
        qualified = (entry.get("demangled") or "").strip()
        if qualified.startswith("Engine::") and qualified.split("::")[-1] in FAMILY:
            rtti[qualified.split("::")[-1]] = (mangled, len(entry.get("slots") or []), int(entry["vtable_rva"]))

    text = io.open(ENGINES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    # remove the namespace blocks the last attempt wrote
    text = re.sub(r"\n/\*\* \w+'s RTTI identifiers.*?\n\}  // namespace \w+", "", text, flags=re.S)
    if "namespace %s {" % FAMILY[0] in text:
        text = re.sub(r"\nnamespace \w+ \{\nconstexpr const char\* kMangled.*?\n\}  // namespace \w+", "", text, flags=re.S)
    print("removed the namespace blocks")

    added = 0
    for short in FAMILY:
        if short not in rtti:
            continue
        mangled, slots, vtable = rtti[short]
        # the class's own declaration: `class InfiniteEngine : ... {` then `public:`
        pattern = re.compile(r"(class %s\b[^\n]*\{\npublic:\n)" % re.escape(short))
        match = pattern.search(text)
        if not match:
            print("   %s: no class declaration found" % short)
            continue
        if "kMangled" in text[match.end():match.end() + 900]:
            continue
        text = text[:match.end()] + (
            '    /** The class\'s RTTI identifiers, the same three constants every other class carries. */\n'
            '    static constexpr const char* kMangled = "%s";\n' % mangled
            + '    static constexpr unsigned kVirtualSlots = %d;\n' % slots
            + '    static constexpr std::uintptr_t kVtable = 0x%X;\n\n' % vtable
        ) + text[match.end():]
        added += 1
    io.open(ENGINES, "w", encoding="utf-8", newline="\n").write(text)
    print("put the trio INSIDE %d engine classes" % added)
    return 0


if __name__ == "__main__":
    sys.exit(main())
