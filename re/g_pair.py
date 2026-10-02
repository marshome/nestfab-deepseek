# -*- coding: utf-8 -*-
"""Pair a key to the offset its own comparison-bounded body touches, with the snake_case name it shares.

Usage:
    python g_pair.py [--serialiser 0x5070E0] [--key shear_gap] [--top 30]

Everything this needs was gathered over several rounds and never used together:

  * the keys are snake_case -- `shear_gap`, `defect_gap`, `used_surface_min_offcut_dimension` -- and re/g_strings_all.py
    found the whole vocabulary in the image;
  * the module's OWN field names are the same snake_case, which is why the earlier pairing failed while it compared keys
    against camelCase C++ declarations;
  * a loader must COMPARE the incoming key to decide a branch, and re/g_keys_bound.py showed that the body between one key's
    comparison and the next key's is the key's own body -- a boundary that the first version of the pairing lacked, which is why
    it gave four different keys to `+0x10`.

So the pairing is: find the key's comparison, take the span to the next key's comparison, and take the offsets that span touches.
Then the NAME comes from the key and the OFFSET comes from the instructions, which is the division the human's refinement implies
-- an assertion or a key may name a field, and only an instruction may place it.

A key whose span touches exactly one offset is PAIRED. A key whose span touches several is reported with all of them and is not
paired, because a guess here is the failure this project keeps recording.
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
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import lib as LIB  # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

LEA = re.compile(r"^([a-z0-9]+), \[rip \+ 0x([0-9a-f]+)\]$")
ACCESS = re.compile(r"\[([a-z0-9]+)(?:\+(0x[0-9a-f]+))?\]")
KEY = re.compile(r"^[a-z][a-z0-9_]{3,40}$")
WIDTHS = (("xmmword", 16), ("oword", 16), ("qword", 8), ("dword", 4), ("word", 2), ("byte", 1))
PRINTABLE = re.compile(rb"[\x20-\x7e]{4,}")

SERIALISERS = (0x50DB70, 0x50EE50, 0x5091B0, 0x509A40, 0x50A550, 0x50B1D0, 0x505280, 0x5052C0, 0x506B30, 0x506D80,
               0x506E90, 0x506130, 0x506350, 0x5070E0, 0x506C10)
# the launch order's own fields, so a paired offset can be compared with the layout the project already declares
LAYOUT = os.path.join(ROOT, "lcns", "include", "lcns", "launching_order.hpp")


def width_of(text):
    for name, width in WIDTHS:
        if name in text:
            return width
    return 0


def image():
    return LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data


def strings(blob):
    out = {}
    for match in PRINTABLE.finditer(blob):
        out[match.start()] = match.group(0).decode("ascii", "replace")
    return out


def layout_names():
    """offset -> field name, from the recovered layout."""
    out = {}
    text = io.open(LAYOUT, encoding="utf-8", errors="replace").read()
    for line in text.split("\n"):
        m = re.match(r"\s*(?:std::uint\d+_t|double|unsigned char)\s+(\w+);\s*//\s*\+0x([0-9A-Fa-f]+)", line)
        if m:
            out[int(m.group(2), 16)] = m.group(1)
    return out


def main(argv):
    only_serialiser = None
    only_key = None
    if "--serialiser" in argv:
        only_serialiser = int(argv[argv.index("--serialiser") + 1], 0)
    if "--key" in argv:
        only_key = argv[argv.index("--key") + 1]
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 30
    blob = image()
    texts = strings(blob)
    profile = load_prof()
    known = layout_names()

    targets = [only_serialiser] if only_serialiser else list(SERIALISERS)
    pairs = []
    for serialiser in targets:
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
            if only_key and only_key not in text:
                continue
            end = keys[position + 1][0] if position + 1 < len(keys) else len(body)
            span = body[index:end]
            offsets = {}
            for ins in span:
                for m in ACCESS.finditer(ins.op_str.replace(" ", "")):
                    if not m.group(2):
                        continue
                    offset = int(m.group(2), 16)
                    width = width_of(ins.op_str)
                    if width and (offset not in offsets or width < offsets[offset][0]):
                        offsets[offset] = (width, ins.address)
            pairs.append((serialiser, text, offsets, len(span)))

    paired = [p for p in pairs if len(p[2]) == 1]
    print("key spans examined: %d;  with exactly one offset (PAIRED): %d" % (len(pairs), len(paired)))
    print("")
    print("%-34s %-9s %-6s %-10s %s" % ("key", "offset", "width", "layout name", "serialiser"))
    shown = 0
    for serialiser, text, offsets, span in sorted(paired, key=lambda p: p[1]):
        offset = next(iter(offsets))
        name = known.get(offset, "(unnamed)")
        agree = "SAME NAME" if name == text else ""
        print("%-34s +0x%-6X %-6d %-10s 0x%X %s" % (text[:34], offset, offsets[offset][0], name[:10], serialiser, agree))
        shown += 1
        if shown >= top:
            break
    print("")
    same = [p for p in paired if known.get(next(iter(p[2]))) == p[1]]
    print("of the paired keys, %d already match the layout field name at that offset exactly, which is the snake_case agreement" % len(same))
    for serialiser, text, offsets, _span in same:
        print("    %-34s +0x%X" % (text, next(iter(offsets))))
    print("")
    print("The NAME comes from the key and the POSITION from the instructions, which is the division the human's refinement")
    print("implies. A key whose span touches several offsets is not paired and is not printed as a pair.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
