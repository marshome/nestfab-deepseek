# -*- coding: utf-8 -*-
"""Delete the generated XMembers structs. They are a SECOND description of classes that already exist, and their offsets cannot be reproduced.

THE HUMAN FOUND THE DEFECT TWICE -- `NestingNesterLayout` and now `LimitedNesterMembers` beside `LimitedNester`. The pattern is the same: I
generated a struct from a constructor scan without asking whether the class already existed.

**AND THIS TIME THE STRUCTS ARE WRONG EVEN AS STRUCTS, for a reason already measured on NestingNester**: the module writes a field at +0x18
while the C++ class places it at +0x08, because the module's base occupies 0x10 bytes this project's `Nester` does not have. **A struct whose
members sit at module offsets inside a C++ object that cannot reproduce those offsets is a false declaration**, and `static_assert` cannot even
catch it because the struct has no base.

WHAT IS DELETED: lcns/include/lcns/named_members.hpp, 24 structs.
WHAT IS KEPT: every name, offset and instruction stays in re/all_class_fields.json and re/param_fields2.json, and the LEDGER keeps the claim.

**A name that cannot yet be placed in a class belongs in the table it came from. That is the same rule as "no oracle, no member", applied one
step further: no reproducible offset, no member either.**
"""
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
MEMBERS = os.path.join(ROOT, "lcns", "include", "lcns", "named_members.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")


def main():
    if os.path.exists(MEMBERS):
        os.remove(MEMBERS)
        print("deleted named_members.hpp")

    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    # remove the include
    for include in ('#include "lcns/named_members.hpp"\n',):
        if include in text:
            text = text.replace(include, "", 1)
            print("removed the include")

    # remove every block that references one of the deleted structs, by line range
    lines = text.split("\n")
    kept = []
    index = 0
    removed_blocks = 0
    while index < len(lines):
        line = lines[index]
        # a block header followed by a body containing a deleted name: drop from the header to the closing brace at the same indent
        if re.match(r"^    // -{20,} ", line) and "the members an ORACLE names" in line:
            depth = 0
            start = index
            index += 1
            while index < len(lines):
                depth += lines[index].count("{") - lines[index].count("}")
                if depth == 0 and "{" in "\n".join(lines[start:index + 1]):
                    index += 1
                    break
                index += 1
            removed_blocks += 1
            continue
        kept.append(line)
        index += 1
    text = "\n".join(kept)
    # and the mechanical block that named and instantiated the structs
    text = re.sub(r"        // EVERY GENERATED MEMBER STRUCT IS NAMED.*?\n        \}\n\n", "", text, flags=re.S)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("removed %d test block(s); lines now %d" % (removed_blocks, text.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
