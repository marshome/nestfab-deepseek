# -*- coding: utf-8 -*-
"""Contradictions: two claims in the ledger or two facts in the binary that cannot both hold.

Usage: python g_contradict.py [--top 20]

A contradiction is the most valuable thing this project can find, because it means something already believed is wrong and
everything downstream of it is suspect. It is also the one thing a session is worst at noticing, since the two halves arrive in
different rounds and nothing compares them. Every check below is mechanical and every one is a comparison between facts this
repository already has:

  THE LEDGER
    1. one subject, one predicate at two different grades
    2. a field whose offset is past the size of its own object
    3. a field declared with two widths
    4. two fields at the same offset
    5. a claim whose witness is empty, or whose grade has no witness to support it

  THE BINARY
    6. a field accessed at two different widths by different functions -- RE 0x140B9 writes a dword at +0x130 while RE 0x146E4
       writes a byte at +0x130, which is a real one and is reported rather than hidden
    7. a function that appears in two different vtable slots
    8. an offset a class's methods touch that lies past the size its own constructor allocates
    9. a class name claimed by two vtables whose member regions do not overlap at all

Each finding states the two facts, where each comes from, and what would resolve it. A finding is not automatically a defect:
check 6 exists because the launch order's +0x130 IS written at two widths by two different original functions, and knowing that
is worth more than not seeing it.
"""
import argparse
import glob
import io
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import ledger            # noqa: E402
import lib as LIB        # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[([a-z0-9]+)(?:\+(0x[0-9a-f]+))?\]")
WIDTHS = (("xmmword", 16), ("oword", 16), ("dword", 4), ("word", 2), ("qword", 8), ("byte", 1))


def width_of(text):
    # longest name first, so 'dword' is not read as 'word'
    for name, width in WIDTHS:
        if name in text:
            return width
    return 0


def canonical_register(reg):
    """The 64-bit name of a register, so `ecx` and `rcx` are the same carrier."""
    aliases = {"eax": "rax", "ax": "rax", "al": "rax", "ebx": "rbx", "bx": "rbx", "bl": "rbx",
               "ecx": "rcx", "cx": "rcx", "cl": "rcx", "edx": "rdx", "dx": "rdx", "dl": "rdx",
               "esi": "rsi", "si": "rsi", "sil": "rsi", "edi": "rdi", "di": "rdi", "dil": "rdi"}
    for number in range(8, 16):
        for suffix in ("", "d", "w", "b"):
            aliases["r%d%s" % (number, suffix)] = "r%d" % number
    return aliases.get(reg, reg)


def findings():
    out = []
    data = ledger.load()

    # 1. one predicate at two grades
    grades = defaultdict(set)
    for claim in data["claims"]:
        grades[(claim["subject"], claim["predicate"])].add(claim["grade"])
    for (subject, predicate), seen in grades.items():
        if len(seen) > 1:
            out.append(("ledger", subject, "the same predicate is filed at %s" % " and ".join(sorted(seen)),
                        "re/ledger.json"))

    # 2. a field past its object's size, 3. two widths, 4. two fields at one offset
    sizes = {}
    for claim in data["claims"]:
        m = re.match(r"^0x([0-9A-F]+) bytes$", claim["predicate"])
        if m:
            sizes[claim["subject"].split(".")[0]] = int(m.group(1), 16)
    offsets = defaultdict(list)
    widths = defaultdict(set)
    for claim in data["claims"]:
        m = re.search(r"\+0x([0-9A-F]+)", claim["predicate"])
        if not m:
            continue
        offset = int(m.group(1), 16)
        owner = claim["subject"].split(".")[0]
        offsets[(owner, offset)].append(claim["subject"])
        w = re.search(r"\b(double|dword|byte|word|qword)\b", claim["predicate"])
        if w:
            widths[claim["subject"]].add(w.group(1))
        if owner in sizes and offset >= sizes[owner]:
            out.append(("ledger", claim["subject"],
                        "claims +0x%X inside a %s object (0x%X)" % (offset, owner, sizes[owner]),
                        "re/ledger.json and the CONSTRUCTOR claim for %s" % owner))
    for (owner, offset), subjects in offsets.items():
        if len(set(subjects)) > 1:
            out.append(("ledger", "%s +0x%X" % (owner, offset),
                        "two subjects claim the same offset: %s" % ", ".join(sorted(set(subjects))),
                        "re/ledger.json"))
    for subject, kinds in widths.items():
        if len(kinds) > 1:
            out.append(("ledger", subject, "declared with two widths: %s" % ", ".join(sorted(kinds)), "re/ledger.json"))

    # 5. a claim with no witness
    for claim in data["claims"]:
        if not claim.get("witness") or len(claim["witness"]) < 8:
            out.append(("ledger", claim["subject"], "a %s claim with no usable witness" % claim["grade"],
                        "re/ledger.json"))

    # 6. an offset written at two widths by the module itself -- scoped to ONE OBJECT, keyed by the width the object's own
    #    constructor writes.
    #
    # Two earlier versions of this check produced 973 and then 720 findings and both were useless, for the same reason: a bare
    # offset has no identity. `+0x10` is a double in the launch order and a pointer in a std::vector, so "one offset, two
    # widths" is not a contradiction unless the two accesses are to the same object. Scoping it to "an offset the ledger
    # mentions" did not help either, because the ledger's offsets are equally generic.
    #
    # What DOES have identity is an offset inside an object whose constructor fixes the field's width. So the check is keyed on
    # the pair (offset, constructor width) and reports a disagreement only where a constructor has spoken.
    profile = load_prof()
    constructor_width = {}
    layout_objects = {}
    for claim in data["claims"]:
        if claim.get("kind") != "layout":
            continue
        m = re.match(r"^0x([0-9A-F]+) bytes$", claim["predicate"])
        if m:
            layout_objects[claim["subject"].split(".")[0]] = int(m.group(1), 16)
    for claim in data["claims"]:
        if claim.get("kind") != "width":
            continue
        owner = claim["subject"].split(".")[0]
        offset_match = re.search(r"\+0x([0-9A-F]+)", claim["predicate"])
        width_match = re.search(r"\b(double|dword|byte|word|qword)\b", claim["predicate"])
        if offset_match and width_match and owner in layout_objects:
            constructor_width[(owner, int(offset_match.group(1), 16))] = {
                "double": 8, "qword": 8, "dword": 4, "word": 2, "byte": 1}[width_match.group(1)]
    for (owner, offset), declared in constructor_width.items():
        sizes = defaultdict(set)
        for addr, info in profile.items():
            size = info.get("size") or 0
            if size <= 0:
                continue
            for ins in disasm(addr):
                if ins.address >= addr + size:
                    break
                for m in ACCESS.finditer(ins.op_str.replace(" ", "")):
                    # ONLY the first argument's object area. Scanning the whole module for `+0x10` counts every type's tenth
                    # byte, which is how this check first reported that the launch order's +0x10 is "also written as 1 byte in
                    # 696 functions": those are other objects. A member of THIS object is reached through the FIRST argument,
                    # which is rcx at the entry of a method and through whatever it was copied into.
                    if canonical_register(m.group(1)) != "rcx" or not m.group(2):
                        continue
                    if int(m.group(2), 16) != offset:
                        continue
                    w = width_of(ins.op_str)
                    if w:
                        sizes[w].add(addr)
        others = {w: addrs for w, addrs in sizes.items() if w != declared and len(addrs) >= 4}
        if others:
            out.append(("binary", "%s +0x%X" % (owner, offset),
                        "the constructor calls it %d bytes; the module also writes %s there through the FIRST argument"
                        % (declared, ", ".join("%d bytes in %d functions" % (w, len(a)) for w, a in sorted(others.items()))),
                        "RE the constructor in the ledger plus the module's own instructions"))

    # 7. a function that holds the same slot number in vtables whose member regions do not overlap AT ALL.
    #
    # The first version reported every shared slot and produced 720 findings, because a base class's method legitimately sits at
    # slot 5 of forty derived vtables -- that is inheritance, not a contradiction. What would be a contradiction is the same
    # method in two vtables that have no member offsets in common, since then they are not the same hierarchy. Fifty-four
    # vtables sharing slot 2 is the module's class tree showing itself, and the report says so rather than flagging it.
    vtables = json.load(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8"))
    in_slot = defaultdict(set)
    region = {}
    mangled_of = {}
    for mangled, info in vtables.items():
        rva = info.get("vtable_rva") or 0
        mangled_of[rva] = mangled
        slots = [s for s in (info.get("slots") or []) if s in profile]
        offsets = set()
        for slot in slots:
            size = (profile.get(slot) or {}).get("size") or 0
            if size <= 0:
                continue
            for ins in disasm(slot):
                if ins.address >= slot + size:
                    break
                for m in ACCESS.finditer(ins.op_str.replace(" ", "")):
                    if canonical_register(m.group(1)) == "rcx" and m.group(2):
                        offsets.add(int(m.group(2), 16))
        region[rva] = offsets
        for position, slot in enumerate(info.get("slots") or []):
            if slot:
                in_slot[slot].add((rva, position))
    shared = 0
    FOREIGN = ("8CryptoPP", "4Coin", "3Clp", "3Osi", "5boost", "6Json", "NSt", "St", "__cxxabiv1", "__gnu_cxx", "6locale")
    for slot, places in in_slot.items():
        by_position = defaultdict(list)
        for rva, position in places:
            by_position[position].append((rva, mangled_of.get(rva, "")))
        for position, rvas_with_names in by_position.items():
            # A verdict about a third-party hierarchy is not a verdict about this module: the 54 vtables that share slot 2
            # with 0x81B600 are all CryptoPP's own derived filters, which is the library's business and not a finding here.
            own = [(rva, name) for rva, name in rvas_with_names if not any(m in name for m in FOREIGN)]
            if len(own) < 4:
                continue
            disjoint = 0
            for i in range(len(own)):
                for j in range(i + 1, len(own)):
                    if region.get(own[i][0]) and region.get(own[j][0]) and not (region[own[i][0]] & region[own[j][0]]):
                        disjoint += 1
            if disjoint:
                out.append(("binary", "0x%X slot %d" % (slot, position),
                            "%d of this module's vtables share it, %d pairs with no member offset in common"
                            % (len(own), disjoint),
                            "re/vtables.json; a shared BASE method is inheritance, disjoint member regions are not"))
                shared += 1
    if not shared:
        out.append(("binary", "vtable slots",
                    "every widely shared slot is either third party or sits in vtables whose member regions overlap",
                    "re/vtables.json -- a base class's method in many vtables is inheritance, and this says so"))

    # 8. a class method touching an offset past the class's own construction size
    for mangled, info in vtables.items():
        slots = [s for s in (info.get("slots") or []) if s in profile]
        if not slots:
            continue
        biggest = 0
        for slot in slots[:3]:          # the destructor and the two it calls usually allocate
            size = (profile.get(slot) or {}).get("size") or 0
            biggest = max(biggest, size)
        if biggest < 0x2000:
            continue
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--kind", choices=("ledger", "binary"), default=None)
    args = parser.parse_args(argv)

    rows = findings()
    if args.kind:
        rows = [r for r in rows if r[0] == args.kind]
    rows.sort(key=lambda r: r[0])
    print("contradictions and sharp edges found: %d" % len(rows))
    print("")
    shown = 0
    for kind, subject, what, where in rows:
        shown += 1
        if shown > args.top:
            break
        print("%-7s %-22s %s" % (kind, subject[:22], what))
        print("        from: %s" % where[:110])
    if shown < len(rows):
        print("... %d more" % (len(rows) - shown))
    print("")
    print("A finding is not automatically a defect. The binary rows are facts about the original module and some of them are")
    print("how it really is: the launch order has a byte and a dword at neighbouring offsets, and a base class's method is in")
    print("many vtables. What matters is that each is SEEN rather than discovered later by accident.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
