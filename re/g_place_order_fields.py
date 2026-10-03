#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Place `Order`'s 45 offset-commented fields at their offsets, in TWO additive steps, and refuse when a step needs a judgement.

**THE FIRST VERSION REWROTE THE STRUCT AND DESTROYED IT.** It emitted a new declaration from the field lines it understood, and `Order` is 335 lines with
`std::vector<Part> parts`, accessor methods and private state that carry no offset comment -- so four files stopped building and the file was reverted with
`git checkout`. **A tool that rewrites a declaration it only partly understands will destroy the parts it does not understand.**

SO THIS IS TWO STEPS AND NEITHER REWRITES:

  STEP 1 -- padding within each RUN. Fields that are already ascending, not overlapping, and separated only by comments keep their lines and get padding
  inserted between them. Everything between two runs, and every line without an offset comment, is left exactly where it is.

  STEP 2 -- and it REFUSES. When a field's comment offset is BELOW the end of the previous one, a gap cannot close it: **relocating a declaration changes the
  struct's meaning, and the tool that does it silently is the tool that destroyed this file once already.** So step 2 reports the list and stops.

**AND THE LIST IS WHAT MAKES STEP 2 SMALL**: the runs are separated by the containers and methods that carry no offset, so a handful of declarations need
moving rather than all 45.

    python -u g_place_order_fields.py
    python -u g_place_order_fields.py --apply
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
FIELD = re.compile(r"^(?P<indent>\s+)(?P<type>[\w:<>,\s\*&]+?)\s+(?P<name>\w+)\s*(?P<array>\[[^\]]*\])?\s*"
                   r"(?P<init>=[^;]*)?;\s*//(?P<comment>.*)$")
STRUCT = re.compile(r"^struct Order \{.*?^\};", re.M | re.S)
MODULE_SIZE = 0x2C0


def width_of(ftype, array):
    count = 1
    if array:
        inner = array.strip("[]")
        count = int(inner, 16) if inner.startswith("0x") else (int(inner) if inner.isdigit() else 1)
    return WIDTHS.get(ftype.strip(), 0) * count


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    text = io.open(MODEL, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    match = STRUCT.search(text)
    if not match:
        print("REFUSING: Order is not found")
        return 2
    lines = match.group(0).split("\n")

    entries = []
    for index, line in enumerate(lines):
        found = FIELD.match(line)
        if not found:
            continue
        offsets = re.findall(r"\+0x([0-9A-Fa-f]+)", found.group("comment"))
        if not offsets:
            continue
        entries.append({"line": index, "offset": int(offsets[0], 16), "type": found.group("type").strip(),
                        "name": found.group("name"), "array": found.group("array") or "",
                        "comment": found.group("comment").strip()})

    unknown = sorted({e["name"] for e in entries if not width_of(e["type"], e["array"])})
    if unknown:
        print("REFUSING: %d field(s) have a type whose width the table lacks: %s" % (len(unknown), ", ".join(unknown)))
        print("   add them to WIDTHS -- a guessed size is a wrong layout")
        return 2

    # **THE RUNS, DEFINED BY THE OFFSETS THEMSELVES.** A new run starts when a field's offset is below the end of the previous field, which is where the
    # declaration order and the offset order disagree and where padding cannot help.
    runs, current = [], [entries[0]]
    for previous, entry in zip(entries, entries[1:]):
        if entry["offset"] < previous["offset"] + width_of(previous["type"], previous["array"]):
            runs.append(current)
            current = [entry]
        else:
            current.append(entry)
    runs.append(current)

    print("fields with an offset comment: %d, in %d run(s) of ascending offsets" % (len(entries), len(runs)))
    for number, run in enumerate(runs):
        first, last = run[0], run[-1]
        print("   run %d: lines %3d..%3d, +0x%03X..+0x%03X, %2d field(s)   %s .. %s"
              % (number, first["line"], last["line"], first["offset"], last["offset"], len(run),
                 first["name"][:22], last["name"][:22]))
    print("")

    if len(runs) > 1:
        print("**%d RUN(S), SO THE DECLARATIONS BETWEEN THEM MUST MOVE BY HAND BEFORE PADDING CAN PLACE THEM.** The fields to move are the FIRST of")
        print("every run after the first, and the offsets they move to are their own comments:")
        for run in runs[1:]:
            print("   %-42s declared at line %3d with offset +0x%03X" % (run[0]["name"], run[0]["line"], run[0]["offset"]))
        print("")
        print("**AND THIS STOPS RATHER THAN MOVING THEM**, because relocating a declaration changes the struct's meaning and the version of this tool that")
        print("did it silently is the one that destroyed this file. Reordering is the work, and it is now a list rather than a search.")
        return 1

    # one run: insert padding between the fields, leaving every original line in place
    insertions = {}
    pad = 0
    cursor = 0
    for entry in entries:
        width = width_of(entry["type"], entry["array"])
        if entry["offset"] > cursor:
            insertions.setdefault(entry["line"], []).append(
                "    std::byte padding%02d[0x%X];   // +0x%03X..+0x%03X, no field here" % (pad, entry["offset"] - cursor, cursor, entry["offset"] - 1))
            pad += 1
        cursor = entry["offset"] + width
    tail = MODULE_SIZE - cursor

    print("padding members to insert: %d, and the run ends at +0x%X against the module's +0x%X (%d byte(s) left)"
          % (pad, cursor, MODULE_SIZE, tail))
    if not args.apply:
        print("(run with --apply to insert it)")
        return 0

    rebuilt = []
    for index, line in enumerate(lines):
        for filler in insertions.get(index, []):
            rebuilt.append(filler)
        rebuilt.append(line)

    # **THE GUARD, BECAUSE THIS OPERATION IS ADDITIVE AND A VERSION THAT WAS NOT DESTROYED THE FILE.** It only INSERTS padding, so the result must have
    # MORE lines than the original and must still contain every original line in order. Both are checked before the write.
    if len(rebuilt) <= len(lines):
        print("REFUSING: the rebuild has %d lines against the original %d, and an ADDITIVE edit must have more" % (len(rebuilt), len(lines)))
        return 2
    without_padding = [line for line in rebuilt if not line.lstrip().startswith("std::byte padding")]
    if without_padding != lines:
        first = next((i for i, (a, b) in enumerate(zip(without_padding, lines)) if a != b), min(len(without_padding), len(lines)))
        print("REFUSING: line %d differs from the original, so this edit is not additive and would drop what it does not understand" % first)
        return 2

    text = text[:match.start()] + "\n".join(rebuilt) + text[match.end():]
    io.open(MODEL, "w", encoding="utf-8", newline="\n").write(text)
    print("inserted %d padding member(s); %d line(s) before, %d after, and every original line is still in place" % (pad, len(lines), len(rebuilt)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
