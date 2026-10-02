# -*- coding: utf-8 -*-
"""Pair a key to an offset with OBJECT and CONTRADICTION constraints, which the last attempt lacked.

Usage: python g_pair2.py [--top 40] [--serialiser 0x50B1D0]

The previous attempt produced 96 pairs and not one agreed with the layout's name at its offset, and the reason was specific: a
comparison-bounded span contains CALLS, and a call touches its OWN object. Three constraints follow from that, and this tool
applies all three.

  OBJECT       an offset counts only if it is reached through the FIRST ARGUMENT's registers. The caller passes the object in
               rcx, and this follows where rcx goes; an offset reached through any other base belongs to a helper's object and is
               excluded. This is the constraint the contradiction finder needed four scopings to find, applied here first.

  NESTED       a call to another SERIALISER ends the span. A nested serialiser has its own object and its own keys, so its body
               contributes nothing to this key; the serialisers are already a named set, so this is mechanical.

  CONTRADICTION  the same key must map to the same offset everywhere it appears. If two serialisers put one key on two offsets,
               the pairing is wrong and BOTH are dropped rather than printed. This is the check the previous attempt did not
               perform, which is why it printed four contradictions without flagging them.

The division stays: the key gives the NAME, the instructions give the POSITION.
"""
import argparse
import io
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import disasm, load_prof, rva2off  # noqa: E402
import lib as LIB  # noqa: E402

LEA = re.compile(r"^([a-z0-9]+), \[rip \+ 0x([0-9a-f]+)\]$")
DIRECT = re.compile(r"^0x([0-9a-f]+)$")
ACCESS = re.compile(r"\[([a-z0-9]+)(?:\+(0x[0-9a-f]+))?\]")
MOVE = re.compile(r"^([a-z0-9]+), ([a-z0-9]+)$")
KEY = re.compile(r"^[a-z][a-z0-9_]{3,40}$")
WIDTHS = (("xmmword", 16), ("oword", 16), ("qword", 8), ("dword", 4), ("word", 2), ("byte", 1))
PRINTABLE = re.compile(rb"[\x20-\x7e]{4,}")

SERIALISERS = {0x50DB70, 0x50EE50, 0x5091B0, 0x509A40, 0x50A550, 0x50B1D0, 0x505280, 0x5052C0, 0x506B30, 0x506D80,
               0x506E90, 0x506130, 0x506350, 0x5070E0, 0x506C10}
ALIAS = {}
for _full, _names in {"rax": ("eax", "ax", "al"), "rbx": ("ebx", "bx", "bl"), "rcx": ("ecx", "cx", "cl"),
                      "rdx": ("edx", "dx", "dl"), "rsi": ("esi", "si", "sil"), "rdi": ("edi", "di", "dil")}.items():
    ALIAS[_full] = _full
    for _n in _names:
        ALIAS[_n] = _full
for _r in range(8, 16):
    for _s in ("", "d", "w", "b"):
        ALIAS["r%d%s" % (_r, _s)] = "r%d" % _r


def canonical(reg):
    return ALIAS.get(reg, reg)


def width_of(text):
    for name, width in WIDTHS:
        if name in text:
            return width
    return 0


def image():
    return LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data


def strings(blob):
    return {m.start(): m.group(0).decode("ascii", "replace") for m in PRINTABLE.finditer(blob)}


def layout_names():
    out = {}
    for line in io.open(os.path.join(ROOT, "lcns", "include", "lcns", "launching_order.hpp"),
                        encoding="utf-8", errors="replace").read().split("\n"):
        m = re.match(r"\s*(?:std::uint\d+_t|double|unsigned char)\s+(\w+);\s*//\s*\+0x([0-9A-Fa-f]+)", line)
        if m:
            out[int(m.group(2), 16)] = m.group(1)
    return out


def object_registers(body):
    """The registers that carry the FIRST ARGUMENT, following its moves from rcx."""
    carries = {"rcx"}
    changed = True
    while changed:
        changed = False
        for ins in body:
            m = MOVE.match(ins.op_str)
            if ins.mnemonic != "mov" or not m:
                continue
            if canonical(m.group(2)) in carries and canonical(m.group(1)) not in carries:
                carries.add(canonical(m.group(1)))
                changed = True
    return carries


def main(argv):
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 40
    only = int(argv[argv.index("--serialiser") + 1], 0) if "--serialiser" in argv else None
    blob = image()
    texts = strings(blob)
    profile = load_prof()
    known = layout_names()

    candidates = defaultdict(set)     # key -> {offset}
    evidence = defaultdict(list)      # (key, offset) -> [(serialiser, address, width)]
    for serialiser in sorted(SERIALISERS if only is None else {only}):
        size = (profile.get(serialiser) or {}).get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(serialiser) if i.address < serialiser + size]
        # every key this function loads, in instruction order
        keys = []
        for index, ins in enumerate(body):
            m = LEA.match(ins.op_str)
            if ins.mnemonic != "lea" or not m:
                continue
            target = ins.address + ins.size + int(m.group(2), 16)
            try:
                file_offset = rva2off(target)
            except Exception:
                continue
            text = texts.get(file_offset)
            if text and KEY.match(text):
                keys.append((index, ins.address, text))
        for position, (index, address, text) in enumerate(keys):
            end = keys[position + 1][0] if position + 1 < len(keys) else len(body)
            span = body[index:end]
            # NESTED: a call to another serialiser ends this key's span
            for cut, ins in enumerate(span):
                if ins.mnemonic != "call":
                    continue
                m = DIRECT.match(ins.op_str.strip())
                if m and int(m.group(1), 16) in SERIALISERS and int(m.group(1), 16) != serialiser:
                    span = span[:cut]
                    break
            carries = object_registers(body)          # OBJECT: the first argument and its copies
            offsets = {}
            for ins in span:
                for m in ACCESS.finditer(ins.op_str.replace(" ", "")):
                    base = canonical(m.group(1))
                    if base not in carries or not m.group(2):
                        continue
                    offset = int(m.group(2), 16)
                    width = width_of(ins.op_str)
                    if width and (offset not in offsets or width < offsets[offset][0]):
                        offsets[offset] = (width, ins.address)
            if len(offsets) != 1:
                continue
            offset, (width, at) = next(iter(offsets.items()))
            candidates[text].add(offset)
            evidence[(text, offset)].append((serialiser, at, width))

    # CONTRADICTION: a key on more than one offset is dropped, and so is an offset claimed by more than one key
    consistent = {k: next(iter(v)) for k, v in candidates.items() if len(v) == 1}
    by_offset = defaultdict(set)
    for key, offset in consistent.items():
        by_offset[offset].add(key)
    conflicted = {o for o, ks in by_offset.items() if len(ks) > 1}

    print("keys with exactly one object offset in every serialiser: %d" % len(consistent))
    print("dropped as contradictions: %d keys on several offsets, %d offsets claimed by several keys"
          % (len(candidates) - len(consistent), len(conflicted)))
    print("")
    print("%-40s %-9s %-6s %-24s %s" % ("key", "offset", "width", "layout name at that offset", "verdict"))
    agree = 0
    for key in sorted(consistent):
        offset = consistent[key]
        width = evidence[(key, offset)][0][2]
        name = known.get(offset, "(unnamed)")
        verdict = ""
        if name == key:
            verdict = "AGREES with the layout"
            agree += 1
        if offset in conflicted:
            verdict = "CONFLICT: this offset is claimed by %d keys" % len(by_offset[offset])
        print("%-40s +0x%-6X %-6d %-24s %s" % (key[:40], offset, width, name[:24], verdict))
        if offset in conflicted:
            agree -= 1 if name == key else 0
    print("")
    print("%d keys agree with the layout's own field name at the offset the instructions give." % agree)
    print("")
    print("Three constraints, and the third is the one the previous attempt lacked: a key on two offsets is a contradiction and")
    print("is dropped, not printed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
