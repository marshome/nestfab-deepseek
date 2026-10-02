#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Split field_accessors.hpp: the TRIVIAL accessors go, the NAMED OPERATIONS stay.

THE HUMAN ASKED ABOUT THE FILE, AND IT HELD TWO THINGS THAT LOOK ALIKE AND ARE NOT:

    TRIVIAL -- a memcpy wrapper whose name is its own offset and the RVA it came from:
        inline std::uint32_t getDword00_52F920(const void* object) {
            std::uint32_t value = 0;
            std::memcpy(&value, static_cast<const unsigned char*>(object) + 0x00, sizeof(value));
            return value;
        }
        **96 of these. They are a calling convention, not a program**, and an accessor at +0x60 of "the object" is a function about an object
        that has not been identified.

    NAMED -- a function whose name says what it DOES, and which the tests exercise for a reason:
        constructCandidate_22E30, moduleSwitch_1BF00, engineFetch_1BF40, initEmptyContainer_51BFC0,
        notNullMember_822590, assignTimer_5F3900, clear..., setDouble..., getPtr...

**THE SECOND KIND IS REVERSE ENGINEERING AND THE FIRST IS NOT.** So the trivial ones are deleted and the named ones are kept in a header of
their own, where a reader sees a function called `moduleSwitch` instead of `getByte00_1BF00`.

    python -u g_split_field_accessors.py
"""
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "field_accessors.hpp")
KEEP = os.path.join(ROOT, "lcns", "include", "lcns", "dll_operations.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")

# A NAME THAT DESCRIBES AN OPERATION rather than an offset. These are the ones the tests exercise for a reason, and each is kept.
OPERATION = re.compile(
    r"^(construct|moduleSwitch|engineFetch|initEmptyContainer|notNullMember|assignTimer|clear|copy|setDouble|getPtr|getByte00_5C4CD0"
    r"|getPtr00_4FC1D0|getPtr00_5FC7E0|getPtr00_4FC200|getPtr08_5C4CE0|setA0_4F7390|set00_895F80)")


def main():
    text = io.open(HEADER, encoding="utf-8", errors="replace").read()
    # split into function blocks by their doc comment
    blocks = re.split(r"\n(?=/\*\* RE 0x)", text)
    kept, dropped = [], []
    for block in blocks:
        found = re.search(r"inline [\w:<> ]+ (\w+)\(", block)
        if not found:
            continue
        name = found.group(1)
        if OPERATION.match(name):
            kept.append(block.rstrip())
        else:
            dropped.append(name)
    print("kept as OPERATIONS: %d" % len(kept))
    print("dropped as TRIVIAL: %d" % len(dropped))
    print("")
    for block in kept:
        name = re.search(r"inline [\w:<> ]+ (\w+)\(", block).group(1)
        print("   %s" % name)

    header = ["// lcns/include/lcns/dll_operations.hpp -- the module's named operations, kept when the trivial accessors were deleted.",
              "//",
              "// field_accessors.hpp held TWO KINDS OF THING and they are not the same:",
              "//",
              "//   TRIVIAL   a memcpy wrapper named after its own offset and the RVA it came from -- `getDword00_52F920`. **A calling convention,",
              "//             not a program**, and 96 of them were deleted: an accessor at +0x60 of `the object` is a function about an object that",
              "//             has not been identified.",
              "//   NAMED     a function whose name says what it DOES: `moduleSwitch`, `engineFetch`, `constructCandidate`, `assignTimer`. **This",
              "//             is reverse engineering**, and it is kept.",
              "//",
              "// Each keeps the RVA it was read from, because the address is the evidence; the trivial ones are deleted, and every offset they",
              "// carried is in re/all_class_fields.json and the ledger instead.",
              "#pragma once",
              "",
              "#include <cstdint>",
              "#include <cstring>",
              "",
              "namespace lcns {",
              "namespace dll {",
              "namespace accessors {",
              ""]
    io.open(KEEP, "w", encoding="utf-8", newline="\n").write("\n".join(header) + "\n" + "\n\n".join(kept) + "\n\n}  // namespace accessors\n}  // namespace dll\n}  // namespace lcns\n")
    print("")
    print("wrote %s" % KEEP)
    os.remove(HEADER)
    print("deleted field_accessors.hpp")

    body = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    body = body.replace('#include "lcns/field_accessors.hpp"', '#include "lcns/dll_operations.hpp"')
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(body)
    print("test_boxacc.cpp now includes dll_operations.hpp")
    return 0


if __name__ == "__main__":
    sys.exit(main())
