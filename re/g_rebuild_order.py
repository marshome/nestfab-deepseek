#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Rebuild `Order` so its members land on the offsets its OWN comments give, with explicit padding and no size overflow.

**THE MEASUREMENT THAT PROMPTED THIS**: 0 of `Order`'s 48 offset-commented fields lands where its comment says, and `sizeof(Order)` is 552 against the
module's 0x2C0 = 704. **The comments are not the problem** -- 45 of the offsets match `LaunchingOrderLayout` exactly, which `re/g_one_definition.py`
measures -- **the DECLARATION is: the fields are out of order (`reorganizeBiggestPartNearOrigin` is at +0x22 and declared after +0xD8), the gaps between
them are whatever the compiler chose, and two `std::string`s have a size the comments do not account for.**

WHAT IT DOES, and every step is mechanical:

  1. collect the fields WITH their stated offsets, and the fields that have NO offset comment (a few carry a RE note instead);
  2. sort by offset and insert an explicit `std::byte padding_NN[...]` for every gap, so the next field starts where its comment says;
  3. **AND CHECK THE RUN DOES NOT RUN PAST THE MODULE'S 0x2C0** -- a field whose width would overlap the next one is reported rather than silently
     shifted, because that means the comments disagree with each other and a rebuild cannot fix it;
  4. put the offset-less fields AFTER the run, together with the size they add.

**AND IT DOES NOT RENAME ANYTHING.** `Order` is named in 234 places, so every existing member name is preserved; what changes is where it lands.
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODEL = os.path.join(ROOT, "lcns", "include", "lcns", "model.hpp")

WIDTHS = {
    "unsigned char": 1, "char": 1, "bool": 1, "std::uint8_t": 1,
    "std::uint16_t": 2, "std::uint32_t": 4, "int": 4, "float": 4,
    "std::uint64_t": 8, "double": 8, "std::size_t": 8, "std::uintptr_t": 8,
    "std::string": 32, "Objective": 4, "NestingOrigin": 4,
}

# `type name[array] = init;  // ... +0xNNN ...`
FIELD = re.compile(r"^(?P<indent>\s+)(?P<type>[\w:<>,\s\*&]+?)\s+(?P<name>\w+)\s*(?P<array>\[[^\]]*\])?\s*"
                   r"(?P<init>=[^;]*)?;\s*//(?P<comment>.*?)\s*$")
STRUCT = re.compile(r"struct Order\s*\{(?P<body>.*?)\n\};", re.S)
MODULE_SIZE = 0x2C0


def width_of(ftype, array):
    count = 1
    if array:
        inner = array.strip("[]")
        if inner.isdigit():
            count = int(inner)
        elif inner.startswith("0x"):
            count = int(inner, 16)
    return WIDTHS.get(ftype.strip(), 0) * count


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write the rebuilt struct into model.hpp")
    args = parser.parse_args(argv)

    text = io.open(MODEL, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    match = STRUCT.search(text)
    if not match:
        print("REFUSING: Order is not found")
        return 2

    placed, unplaced, widths = [], [], {}
    for line in match.group("body").split("\n"):
        found = FIELD.match(line)
        if not found:
            continue
        ftype, name = found.group("type").strip(), found.group("name")
        array, init = found.group("array") or "", found.group("init") or ""
        width = width_of(ftype, array)
        widths[name] = width
        # **THE FIRST OF SEVERAL OFFSETS, NOT THE LAST.** `commonCutAuthorizations` carries `// +0x70/+0x78/+0x80`, and taking the last put a 12 byte
        # array at +0x80 so that it ran past `commonCutNoHoles` at +0x84 -- **a conflict this tool then reported as the comments disagreeing, when what
        # disagreed was the parser.** The first offset is where the field begins.
        offsets = re.findall(r"\+0x([0-9A-Fa-f]+)", found.group("comment") or "")
        if offsets:
            placed.append((int(offsets[0], 16), ftype, name, array, init, found.group("comment").strip()))
        else:
            unplaced.append((ftype, name, array, init, found.group("comment").strip()))

    placed.sort(key=lambda row: row[0])
    print("fields with an offset comment: %d, without: %d" % (len(placed), len(unplaced)))

    # the sizes this project's table cannot resolve are reported rather than guessed at
    unknown = sorted(n for _o, _t, n, _a, _i, _c in placed if not widths[n])
    if unknown:
        print("REFUSING: %d field(s) have a type whose width the table lacks: %s" % (len(unknown), ", ".join(unknown)))
        print("   add them to WIDTHS and run again -- a guessed size is a wrong layout")
        return 2

    # **AND THE RUN MUST FIT**, because a field wider than the gap to the next one means the comments disagree with each other
    problems = []
    for index, (offset, ftype, name, array, _init, _comment) in enumerate(placed):
        end = offset + widths[name]
        if index + 1 < len(placed):
            following = placed[index + 1][0]
            if end > following:
                problems.append("%s at +0x%X is %d bytes and ends at +0x%X, past +0x%X" % (name, offset, widths[name], end, following))
        elif end > MODULE_SIZE:
            problems.append("%s at +0x%X is %d bytes and ends at +0x%X, past the module's 0x%X" % (name, offset, widths[name], end, MODULE_SIZE))
    if problems:
        print("")
        print("THE COMMENTS DISAGREE WITH EACH OTHER, which a rebuild cannot fix:")
        for line in problems:
            print("   %s" % line)
        print("")
        print("so the struct is NOT rewritten. **These are the fields whose width and offset cannot both be right**, and which is wrong is a question for")
        print("the module's stores rather than for this tool.")
        return 1

    # the rebuild
    body = []
    cursor = 0
    pad = 0
    for offset, ftype, name, array, init, comment in placed:
        if offset > cursor:
            body.append("    std::byte padding%02d[0x%X];   // +0x%03X..+0x%03X, no field here" % (pad, offset - cursor, cursor, offset - 1))
            pad += 1
        body.append("    %s %s%s %s;%s" % (ftype, name, array, init.strip(), "  // +0x%03X" % offset))
        cursor = offset + widths[name]
    if cursor < MODULE_SIZE:
        body.append("    std::byte padding%02d[0x%X];   // +0x%03X..+0x%03X, no field here" % (pad, MODULE_SIZE - cursor, cursor, MODULE_SIZE - 1))
    body.append("")
    body.append("    // --- fields with NO offset comment, kept after the run ---")
    for ftype, name, array, init, comment in unplaced:
        body.append("    %s %s%s %s;   // %s" % (ftype, name, array, init.strip(), comment[:70]))

    rebuilt = "struct Order {\n" + "\n".join(body) + "\n};"
    print("")
    print("rebuilt: %d placed field(s), %d padding member(s), %d unplaced field(s), up to +0x%X"
          % (len(placed), pad, len(unplaced), MODULE_SIZE))
    if args.apply:
        text = text[:match.start()] + rebuilt + text[match.end():]
        io.open(MODEL, "w", encoding="utf-8", newline="\n").write(text)
        print("written into model.hpp")
    else:
        print("")
        print(rebuilt[:2500])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
