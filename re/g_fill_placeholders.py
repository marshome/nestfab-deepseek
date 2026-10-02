#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Replace the placeholder declarations with classes that HAVE members, using the constructor field scan.

THE DEFECT THIS FIXES, measured: class_definitions.hpp declares 46 classes whose entire body is `virtual ~X() = default;` plus a comment
naming slot 2. **That is a name, not a class** -- the audit in re/g_audit_cpp.py counts exactly that shape as a placeholder, because it is what
a generator emits when it knows a class exists and nothing about it.

AND THE CONTENT IS ALREADY COMPUTED. re/all_class_fields.json holds, for 28 classes, the offsets their constructors write and the instruction
that writes each. **A member placed by an instruction is what a class is supposed to contain**, so it is generated into the declaration rather
than left in a table beside it.

WHAT IS NOT DONE, deliberately: a class with no placed fields keeps its placeholder body **and says so in its comment**, because an empty
class and a class whose fields are unknown look the same in C++ and are very different claims. A class that a hand-written header already
declares is SKIPPED -- one class, one description.
"""
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

OUT = os.path.join(ROOT, "lcns", "include", "lcns", "class_definitions.hpp")
STORE = re.compile(r"^(byte|word|dword|qword) ptr \[(\w+)(?: \+ (0x[0-9a-f]+))?\], (.+)$")
WIDTH_TYPE = {"byte": "std::uint8_t", "word": "std::uint16_t", "dword": "std::uint32_t", "qword": "void*"}


def members_of(constructor, profile):
    """[(offset, type, address, instruction)] for the stores through the object, from 8 upward."""
    size = (profile.get(constructor) or {}).get("size") or 0
    if not size:
        return []
    found = {}
    for instruction in disasm(constructor):
        if instruction.address >= constructor + size:
            break
        match = STORE.match(instruction.op_str)
        if not match:
            continue
        width, _base, offset, source = match.group(1), match.group(2), match.group(3), match.group(4)
        if offset is None:
            continue
        where = int(offset, 16)
        if where < 8:
            continue
        kind = WIDTH_TYPE[width]
        if instruction.mnemonic == "movsd" or (width == "qword" and source.startswith("xmm")):
            kind = "double"
        found.setdefault(where, (kind, instruction.address, "%s %s" % (instruction.mnemonic, instruction.op_str)))
    return [(where, found[where][0], found[where][1], found[where][2]) for where in sorted(found)]


def main():
    profile = load_prof()
    data = json.loads(io.open(os.path.join(HERE, "all_class_fields.json"), encoding="utf-8").read())
    by_class = {entry["class"]: entry for entry in data["classes"]}

    # WHICH SHORT NAMES A HAND-WRITTEN HEADER ALREADY DECLARES, so a class that exists is not declared twice
    hand = set()
    for path in glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "**", "*.hpp"), recursive=True):
        if os.path.basename(path) in ("class_definitions.hpp", "classes.hpp", "class_constructors.hpp",
                                      "virtual_methods.hpp", "parameter_report.hpp", "option_keys.hpp"):
            continue
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in re.finditer(r"\b(?:class|struct)\s+(\w+)", text):
            hand.add(match.group(1))

    text = io.open(OUT, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    # every placeholder body, replaced by one with members where the scan placed any
    pattern = re.compile(r"/\*\* ([\w:]+) -- vtable 0x([0-9A-F]+), (\d+) virtual slot\(s\)\. \*/\n"
                         r"class (\w+) \{\npublic:\n    virtual ~\w+\(\) = default;\n\n"
                         r"    // Slot 2, the first DECLARED virtual, is (0x[0-9A-F]+)([^\n]*)\n\};")

    stats = {"filled": 0, "kept": 0, "skipped": 0}
    filled_names = []

    def replace(match):
        qualified, vtable, slots, short, slot2, note = match.groups()
        if short in hand:
            stats["skipped"] += 1
            return ("/** %s -- vtable 0x%s, %s virtual slot(s). DECLARED ELSEWHERE: a hand-written header defines it, so this file must not. */"
                    % (qualified, vtable, slots))
        entry = by_class.get(qualified)
        constructor = int(entry["constructor"], 16) if entry and entry["constructor"] else None
        found = members_of(constructor, profile) if constructor else []
        if not found:
            stats["kept"] += 1
            return ("/** %s -- vtable 0x%s, %s virtual slot(s).\n"
                    " *\n"
                    " *  **NO MEMBER IS PLACED YET**: no constructor candidate writes a field at this class's own offsets, so the body below is a\n"
                    " *  declaration and NOT a claim that the class is empty. An empty class and one whose fields are unknown look the same in C++\n"
                    " *  and are different claims, which is why this says so.\n"
                    " *  Slot 2, the first DECLARED virtual, is %s%s. */\n"
                    "class %s {\npublic:\n    virtual ~%s() = default;\n};" % (qualified, vtable, slots, slot2, note, short, short))
        stats["filled"] += 1
        filled_names.append(qualified)
        lines = ["/** %s -- vtable 0x%s, %s virtual slot(s)." % (qualified, vtable, slots),
                 " *",
                 " *  THE MEMBERS ARE PLACED BY ITS CONSTRUCTOR 0x%X, each with the store that puts it there and the width that types it." % constructor,
                 " *  An offset no store reaches is a named `unplaced` region, because **an offset with no instruction is not a field**.",
                 " *",
                 " *  Slot 2, the first DECLARED virtual, is %s%s. */" % (slot2, note),
                 "class %s {" % short,
                 "public:",
                 "    virtual ~%s() = default;" % short,
                 ""]
        previous = 8
        seen = {}
        for where, kind, address, text in found:
            if where > previous:
                lines.append("    std::byte unplaced_%04X[0x%X]{};   // +0x%X .. +0x%X: no instruction places a field here"
                             % (previous, where - previous, previous, where))
            # THE NAME SAYS WHAT IS KNOWN AND NOT MORE. The store gives a POSITION and a WIDTH; nothing read gives a meaning, so the member is
            # named for its offset rather than given a plausible identifier. **A name needs an oracle** -- the module's own string, or a setter
            # whose instruction is the field's -- and a generated name that reads like a domain term would hide that it has none.
            name = "at_%04x" % where
            while name in seen:
                name += "_"
            seen[name] = where
            lines.append("    %-14s %-12s = {}; // +0x%X, RE 0x%X: %s" % (kind, name, where, address, text))
            previous = where + (8 if kind in ("void*", "double") else 4)
        lines.append("};")
        return "\n".join(lines)

    new_text, count = pattern.subn(replace, text)
    if count != 46:
        print("REFUSING: the placeholder pattern matched %d classes and 46 were expected, so the file has changed shape" % count)
        return 2
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(new_text)
    print("rewrote class_definitions.hpp")
    print("  classes given members: %d" % stats["filled"])
    print("  left as declarations with a stated reason: %d" % stats["kept"])
    print("  not declared, because a hand-written header has them: %d" % stats["skipped"])
    print("")
    for name in filled_names[:12]:
        print("   %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
