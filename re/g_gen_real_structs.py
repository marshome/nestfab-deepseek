#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Emit a REAL struct per class, from the stores its constructor performs -- the conversion the human asked for.

WHAT THIS REPLACES. `class_definitions.hpp` declares 46 classes with nothing but a destructor and a comment about slot 2. That is a
placeholder: it says a name exists. **This emits members**, placed by the instructions that write them and typed by the WIDTH of the store,
which is what the machine code actually determines.

HOW A TYPE IS DECIDED, and it is not a guess:

    `mov qword ptr [rbx + 0x18], rax`   -> a pointer-width member, so void* unless the source register says otherwise
    `mov dword ptr [rbx + 0x28], eax`   -> std::uint32_t
    `movsd qword ptr [rbx + 0x30], xmm6`-> double, because movsd is a SCALAR DOUBLE move
    `mov byte ptr [rbx + 0x38], 1`      -> std::uint8_t

and an offset no store reaches is emitted as `std::byte unplaced_at_XXXX[N]`, NAMED AS UNPLACED rather than filled with a plausible member.
**An offset with no instruction is not a field**, and a struct that says so is more honest than one that guesses.

    python g_gen_real_structs.py [--classes 8] [--out lcns/include/lcns/class_layouts.hpp]
"""
import argparse
import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof, rip_targets  # noqa: E402
import g_class_fields  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFAULT_OUT = os.path.join(ROOT, "lcns", "include", "lcns", "class_layouts.hpp")

STORE = re.compile(r"^(byte|word|dword|qword) ptr \[(\w+)(?: \+ (0x[0-9a-f]+))?\], (.+)$")

# THE WIDTH IS THE TYPE, and movsd overrides it because a scalar double move is a double whatever its width.
WIDTH_TYPE = {"byte": "std::uint8_t", "word": "std::uint16_t", "dword": "std::uint32_t", "qword": "void*"}


def types_for(function, profile):
    """{offset: (type, width, instruction address, instruction)} for one function's stores through the object."""
    size = (profile.get(function) or {}).get("size") or 0
    if not size:
        return {}
    found = {}
    for instruction in disasm(function):
        if instruction.address >= function + size:
            break
        match = STORE.match(instruction.op_str)
        if not match:
            continue
        width, _base, offset, source = match.group(1), match.group(2), match.group(3), match.group(4)
        if offset is None:
            continue
        where = int(offset, 16)
        if where < 8:
            continue                    # +0 is the vtable and +8 upward is the first data; below 8 is not this class's own field
        kind = WIDTH_TYPE[width]
        if instruction.mnemonic == "movsd":
            kind = "double"
        elif width == "qword" and source.startswith("xmm"):
            kind = "double"
        found.setdefault(where, (kind, width, instruction.address, "%s %s" % (instruction.mnemonic, instruction.op_str)))
    return found


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--classes", type=int, default=8)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    profile = load_prof()
    data = json.loads(io.open(os.path.join(HERE, "all_class_fields.json"), encoding="utf-8").read())

    # THE CLASSES WITH THE MOST FIELDS FIRST, because each one is a struct that will actually be filled rather than a shell.
    ranked = sorted([e for e in data["classes"] if e["fields"] >= 3], key=lambda e: -e["fields"])[:args.classes]

    blocks = []
    report = []
    for entry in ranked:
        qualified = entry["class"]
        ctor = int(entry["constructor"], 16) if entry["constructor"] else None
        if ctor is None:
            continue
        fields = types_for(ctor, profile)
        if len(fields) < 3:
            continue
        namespace = qualified.rsplit("::", 1)[0] if "::" in qualified else ""
        short = qualified.split("::")[-1]
        report.append((qualified, ctor, int(entry["vtable"], 16), len(fields)))

        lines = []
        lines.append("/** %s -- RE the constructor at 0x%X, vtable 0x%s. %d placed member(s)."
                     % (qualified, ctor, entry["vtable"][2:], len(fields)))
        lines.append(" *")
        lines.append(" *  EVERY MEMBER IS PLACED BY AN INSTRUCTION and typed by the WIDTH of its store; an offset nothing writes is emitted")
        lines.append(" *  as a named `unplaced` region rather than filled with a plausible member. **An offset with no instruction is not a")
        lines.append(" *  field.**")
        lines.append(" */")
        lines.append("struct %sLayout {" % short)
        previous = 8
        for where in sorted(fields):
            kind, width, address, text = fields[where]
            if where > previous:
                lines.append("    std::byte unplaced_%04X[0x%X]{};   // +0x%X .. +0x%X: NO INSTRUCTION PLACES A FIELD HERE"
                             % (previous, where - previous, previous, where))
            lines.append("    %-16s = {};%s// +0x%X, RE 0x%X: %s"
                         % (kind, " " * max(0, 24 - len(kind)), where, address, text))
            previous = where + (8 if kind in ("void*", "double") else 4)
        lines.append("};")
        lines.append("")
        blocks.append("\n".join(lines))

    header = ["// lcns/include/lcns/class_layouts.hpp -- the classes the constructor scan could place members for, as REAL STRUCTS.",
              "//",
              "// GENERATED by re/g_gen_real_structs.py. **This is the answer to a placeholder**: class_definitions.hpp declared these classes",
              "// with nothing but a destructor, and a member is what the instructions actually determine. Each member carries the store that",
              "// places it and the width that types it; an offset no store reaches is a named `unplaced` region.",
              "//",
              "// %d classes, %d placed members between them." % (len(report), sum(r[3] for r in report)),
              "#pragma once",
              "",
              "#include <cstddef>",
              "#include <cstdint>",
              "",
              "namespace lcns {",
              ""]
    text = "\n".join(header + blocks + ["}  // namespace lcns", ""])
    io.open(args.out, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote %s" % args.out)
    print("  classes: %d" % len(report))
    for qualified, ctor, vtable, count in report:
        print("   %-34s ctor 0x%-8X vtable 0x%-8X %2d members" % (qualified[:34], ctor, vtable, count))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
