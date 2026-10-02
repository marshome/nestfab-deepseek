#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Emit class members an ORACLE names -- with the MIPLIB benchmark names EXCLUDED, which the first version left in.

WHAT THE FIRST VERSION DID WRONG, and it is a defect of long standing in this project: it drew names from re/param_fields2.json without
separating the two kinds of string that file's sites reference. **The module answers to option names AND it contains 49 benchmark instance
names**, the archive recorded the split in re/param_split.json (`parameters` versus `data`), and I ignored it -- so the generator emitted
`void* air03` and `void* bell5` as members of Tiling::SqueezeMultiTiler.

    from re/param_split.json:  parameters = {adaptative_price_max_random, beam_..., ...}   <- the module's VOCABULARY
                               data       = [air03, air04, bell5, blend2, cap6000, ...]     <- MIPLIB instances it BENCHMARKS

**A name is an oracle only when it is a name the module ANSWERS TO.** A benchmark's name is a string it contains, and the difference is exactly
the one this project has recorded before.

    python g_gen_named_members.py [--out lcns/include/lcns/named_members.hpp]
"""
import argparse
import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import STRS, disasm, load_prof  # noqa: E402

STORE = re.compile(r"^(byte|word|dword|qword) ptr \[(\w+)(?: \+ (0x[0-9a-f]+))?\], (.+)$")

# THE TYPE, AND WHERE IT COMES FROM. The store gives a WIDTH; the oracle's NAME gives the semantics. Neither alone is enough, which is why the
# first version's `void* nb_iterations_first` was wrong twice over.
#
# ORDER MATTERS, AND THE FIRST ATTEMPT GOT IT WRONG: `"ratio" in name` matched `nb_iterations_before_rotate_compact_postop` and typed a count
# as a double. **The prefix is checked before the substring**, because a prefix is what the module's own vocabulary uses to classify a name.
#
#   `nb_*`      a COUNT    -> the width's unsigned integer
#   `enable_*`  a FLAG     -> the width's unsigned integer
#   `*ratio*` or `*frequency*` at the END   -> double, because those are measurements
#   and anything else keeps the width's integer type, NOT a pointer.
#
# **A POINTER TYPE IS A CLAIM and the evidence does not support one here**: `mov qword ptr [rcx + 0x38], r9` copies eight bytes from a source
# object and says nothing about whether they are an address.
WIDTH_INT = {"byte": "std::uint8_t", "word": "std::uint16_t", "dword": "std::uint32_t", "qword": "std::uint64_t"}
WIDTH_BYTES = {"byte": 1, "word": 2, "dword": 4, "qword": 8}

# THE NAMES THAT CANNOT BE MEMBERS AS THEY STAND. `default` is a keyword; `data`, `size` and `begin` collide with std::array's own members
# when the struct is used; a name with a space or a `<<` is not an identifier at all. **The oracle's name is kept in the comment** and the
# member gets a legal form, because discarding the name would discard the oracle.
CXX_KEYWORDS = {"default", "class", "new", "delete", "operator", "template", "typename", "this", "true", "false",
                "int", "long", "short", "float", "double", "char", "bool", "void", "switch", "case", "for", "while",
                "return", "break", "continue", "if", "else", "do", "goto", "try", "catch", "throw", "namespace", "using"}


def type_for(width, name):
    for prefix in ("nb_", "enable_", "use_", "default_", "max_", "min_"):
        if name.startswith(prefix):
            return WIDTH_INT[width]
    # and the SUFFIX for a measurement, which is where those words actually appear
    if name.endswith(("ratio", "frequency", "tolerance")) or "_ratio" in name or "_frequency" in name:
        return "double"
    return WIDTH_INT[width]

# AN OPTION NAME IS A snake_case IDENTIFIER. This is a second filter on top of the parameters/data split, because the split's `parameters` set
# is authoritative and a name that is not an identifier-shaped word is a string the module happens to contain.
IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$")
SAFE = re.compile(r"[^A-Za-z0-9_]")


def identifier_for(name):
    """A legal C++ member name for an oracle name that is not one, with the oracle's own kept in the comment by the caller."""
    cleaned = SAFE.sub("_", name).strip("_")
    if not cleaned or not cleaned[0].isalpha():
        cleaned = "m_" + cleaned
    if cleaned in CXX_KEYWORDS:
        cleaned = "m_" + cleaned
    return cleaned


def oracle_names():
    """{offset: set of OPTION names}, from the module's own vocabulary and nothing else."""
    split = json.loads(io.open(os.path.join(HERE, "param_split.json"), encoding="utf-8").read())
    vocabulary = set(split.get("parameters") or {})
    benchmarks = set(split.get("data") or [])
    print("the module's vocabulary: %d parameter names; benchmarks set aside: %d" % (len(vocabulary), len(benchmarks)))

    data = json.loads(io.open(os.path.join(HERE, "param_fields2.json"), encoding="utf-8").read())
    by_offset = collections.defaultdict(set)
    kept = dropped_benchmark = dropped_shape = 0
    for _site, rows in data["sites"].items():
        for row in rows:
            name_rva, offset = row.get("name_rva"), row.get("offset")
            if name_rva is None or offset is None:
                continue
            address = int(name_rva, 16) if isinstance(name_rva, str) else int(name_rva)
            name = STRS.get(address)
            if not name:
                continue
            if name in benchmarks:
                dropped_benchmark += 1
                continue
            if name not in vocabulary or not IDENTIFIER.match(name):
                dropped_shape += 1
                continue
            by_offset[int(offset) if isinstance(offset, int) else int(offset, 16)].add(name)
            kept += 1
    print("  kept as the module's vocabulary: %d pairs" % kept)
    print("  dropped as benchmark names:      %d" % dropped_benchmark)
    print("  dropped as not identifier-shaped or not in the vocabulary: %d" % dropped_shape)
    return by_offset


def stores_of(constructor, profile):
    size = (profile.get(constructor) or {}).get("size") or 0
    if not size:
        return {}
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
        found.setdefault(where, (width, instruction.address, "%s %s" % (instruction.mnemonic, instruction.op_str)))
    return found


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(ROOT, "lcns", "include", "lcns", "named_members.hpp"))
    args = parser.parse_args(argv)

    profile = load_prof()
    names = oracle_names()
    print("")
    data = json.loads(io.open(os.path.join(HERE, "all_class_fields.json"), encoding="utf-8").read())

    emitted = named_total = 0
    every_name = set()
    blocks = []
    for entry in sorted(data["classes"], key=lambda e: -e["fields"]):
        if not entry["constructor"] or entry["fields"] < 2:
            continue
        constructor = int(entry["constructor"], 16)
        stores = stores_of(constructor, profile)
        named = {where: names[where] for where in stores if where in names}
        if not named:
            continue
        qualified = entry["class"]
        # A SUBSTITUTED TEMPLATE PARAMETER IS NOT A CLASS OF THE MODULE. `<subst>::...` names appear in the RTTI because the binary was built
        # without the template's arguments, and this repository excludes them everywhere else -- a first version of this generator did not, and
        # emitted `struct <<subst>>Members`, which is not a declaration at all.
        if "<" in qualified or "subst" in qualified:
            continue
        short = qualified.split("::")[-1]
        named_total += sum(len(v) for v in named.values())
        every_name |= {n for v in named.values() for n in v}
        emitted += 1
        lines = ["/** %s -- vtable 0x%s. ONLY THE MEMBERS AN ORACLE NAMES." % (qualified, entry["vtable"][2:]),
                 " *",
                 " *  A field with no name does not belong in a class: `at_0010` is a position wearing a name-shaped label. Every other offset",
                 " *  this class's constructor 0x%X writes is a named unplaced region, and the class waits for a name rather than inventing one." % constructor,
                 " */",
                 "struct %sMembers {" % short]
        previous = 8
        seen = set()
        for where in sorted(stores):
            width, address, _text = stores[where]
            if where in named:
                if where > previous:
                    lines.append("    std::byte unplaced_%04X[0x%X]{};   // +0x%X .. +0x%X: no name is known for these bytes"
                                 % (previous, where - previous, previous, where))
                for name in sorted(named[where]):
                    # AN ORACLE NAME IS NOT ALWAYS A LEGAL IDENTIFIER, AND TWO OFFSETS CAN SHARE ONE. `data` is a std::array method, and
                    # `default` is a keyword; a name that repeats within one struct is a redeclaration. **The name is the ORACLE's and is kept
                    # where it can be used**, and made legal or unique where it cannot, with the original in the comment.
                    legal = identifier_for(name)
                    unique = legal
                    suffix = 2
                    while unique in seen:
                        unique = "%s_%d" % (legal, suffix)
                        suffix += 1
                    seen.add(unique)
                    declared = type_for(width, name)
                    note = "" if unique == name else "  (oracle name: %s)" % name
                    lines.append("    %-10s %-44s = {}; // +0x%X, RE 0x%X%s" % (declared, unique, where, address, note))
                previous = where + WIDTH_BYTES[width]
        lines.append("};")
        lines.append("")
        blocks.append("\n".join(lines))

    text = "\n".join([
        "// lcns/include/lcns/named_members.hpp -- the class members an ORACLE names, and nothing else.",
        "//",
        "// GENERATED by re/g_gen_named_members.py. **A field with no name does not belong in a class.** Every member below is named by an option",
        "// key the module ANSWERS TO -- its own vocabulary -- paired with the offset its lookup result is stored into. **The MIPLIB benchmark",
        "// names are excluded**: the module CONTAINS those strings and does not answer to them, which re/param_split.json records and a first",
        "// version of this generator ignored, emitting `void* air03` as a member of Tiling::SqueezeMultiTiler.",
        "//",
        "// %d classes, %d named members, %d distinct names. See lcns/docs/WHAT_IS_NORMAL_CPP.md." % (emitted, named_total, len(every_name)),
        "#pragma once",
        "",
        "#include <cstddef>",
        "#include <cstdint>",
        "",
        "namespace lcns {",
        "",
    ] + blocks + ["}  // namespace lcns", ""])
    io.open(args.out, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote %s" % args.out)
    print("  classes with a NAMED member: %d" % emitted)
    print("  named members: %d over %d distinct names" % (named_total, len(every_name)))
    print("")
    for name in sorted(every_name)[:14]:
        print("   %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
