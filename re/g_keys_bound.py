# -*- coding: utf-8 -*-
"""Pair a serialiser key to an offset, inside the key's own comparison-bounded body, and name the object.

Usage:
    python g_keys_bound.py                       -> every serialiser, its keys, and the offsets its bodies touch
    python g_keys_bound.py --serialiser 0x5070E0
    python g_keys_bound.py --match               -> which declared struct each serialiser's offsets fit

re/g_json_fields.py pairs 16 offsets and is not good enough, and this round established why rather than assuming it. Its rule
takes the FIRST single-offset accessor within a window after a key, so a key whose own body contains no accessor steals the next
key's -- the report had four different keys on `+0x10`. And its thirteen serialisers act on DIFFERENT objects, so an offset
gathered across all of them is a set of coincidences.

That is the same lesson the contradiction finder and the duplicate declaration both reached: **an offset has no identity without
its object**. So this tool supplies both things that were missing:

  BOUNDARY   a key's body runs from the key's own comparison to the NEXT key's comparison, because a serialiser must compare
             the incoming name to decide which branch to take. Inside that span the offsets touched are that key's, and no
             window or heuristic is involved.
  IDENTITY   the offsets a serialiser touches are its object's signature. A serialiser that reads +0x50 as a double and +0x44
             as a byte is writing the object whose declaration has those offsets, so the object is identified by the SHAPE of
             the accesses rather than by assuming which object each file argues about.

The identity step is what `--match` reports: for every serialiser, the declared struct whose offset set contains the most of the
serialiser's offsets, with the count and the misses. A serialiser that matches the launch order to within a couple of offsets is
serialising the launch order, and that is the pairing the 70 unnamed offsets need.
"""
import argparse
import glob
import io
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

# The serialisers, from re/g_json_fields.py's SERIALISERS list plus the two the string sweep attributed keys to.
SERIALISERS = (0x50DB70, 0x50EE50, 0x5091B0, 0x509A40, 0x50A550, 0x50B1D0, 0x505280, 0x5052C0, 0x506B30, 0x506D80,
               0x506E90, 0x506130, 0x506350, 0x5070E0, 0x506C10)
ALIAS = {}
for _full, _names in {"rax": ("eax", "ax", "al"), "rbx": ("ebx", "bx", "bl"), "rcx": ("ecx", "cx", "cl"),
                      "rdx": ("edx", "dx", "dl"), "rsi": ("esi", "si", "sil"), "rdi": ("edi", "di", "dil")}.items():
    ALIAS[_full] = _full
    for _n in _names:
        ALIAS[_n] = _full


def canonical(reg):
    return ALIAS.get(reg, reg)


def width_of(text):
    for name, width in WIDTHS:
        if name in text:
            return width
    return 0


def image():
    return LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data


def string_table(blob):
    out = {}
    for match in PRINTABLE.finditer(blob):
        out[match.start()] = match.group(0).decode("ascii", "replace")
    return out


def keys_of(serialiser, profile, texts, span=None):
    """(instruction index, address, key text) for every key-like string the function loads, in order."""
    size = (profile.get(serialiser) or {}).get("size") or 0
    if size <= 0:
        return [], []
    body = [i for i in disasm(serialiser) if i.address < serialiser + size]
    out = []
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
            out.append((index, ins.address, text))
    return body, out


def body_offsets(segment):
    """offset -> (width, address) for the object areas this span touches."""
    out = {}
    for ins in segment:
        operand = ins.op_str.replace(" ", "")
        for m in ACCESS.finditer(operand):
            if not m.group(2):
                continue
            offset = int(m.group(2), 16)
            width = width_of(ins.op_str)
            if width and (offset not in out or 0 < width < out[offset][0]):
                out[offset] = (width, ins.address)
    return out


def declared_structs():
    """struct name -> {offset: (field name, width)} for the offsets the declarations comment."""
    sizes = {"char": 1, "bool": 1, "unsigned char": 1, "std::uint8_t": 1, "uint8_t": 1, "short": 2,
             "unsigned short": 2, "std::uint16_t": 2, "uint16_t": 2, "int": 4, "unsigned int": 4, "float": 4,
             "std::uint32_t": 4, "uint32_t": 4, "double": 8, "long long": 8, "std::uint64_t": 8, "uint64_t": 8,
             "size_t": 8, "std::size_t": 8, "long": 4}
    out = {}
    pattern = re.compile(r"^\s*((?:std::)?(?:u?int\d+_t|int|long|short|char|float|double|bool|size_t|std::size_t|"
                         r"unsigned\s+char|unsigned\s+int|void\s*\*|[A-Z]\w*(?:::\w+)*)(?:\s*\*)?)\s+"
                         r"([A-Za-z_]\w*)\s*(?:\[\s*(\d+)\s*\])?\s*(?:=[^;]*)?;\s*(?://\s*(.*))?$")
    for path in glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "**", "*.hpp"), recursive=True):
        text = io.open(path, encoding="utf-8", errors="replace").read()
        current = None
        for line in text.split("\n"):
            m = re.match(r"\s*(?:struct|class)\s+(\w+)", line)
            if m:
                current = m.group(1)
                out.setdefault(current, {})
                continue
            if current is None or line.strip().startswith("};"):
                if line.strip().startswith("};"):
                    current = None
                continue
            f = pattern.match(line)
            if not f:
                continue
            o = re.search(r"\+0x([0-9A-Fa-f]+)", f.group(4) or "")
            if not o:
                continue
            width = 8 if "*" in f.group(1) else sizes.get(f.group(1).strip())
            if f.group(3) and width:
                width *= int(f.group(3))
            out[current][int(o.group(1), 16)] = (f.group(2), width)
    return {k: v for k, v in out.items() if len(v) >= 4}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--serialiser", type=lambda v: int(v, 0), default=None)
    parser.add_argument("--match", action="store_true")
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args(argv)

    blob = image()
    texts = string_table(blob)
    profile = load_prof()
    structs = declared_structs()

    targets = [args.serialiser] if args.serialiser else list(SERIALISERS)
    summary = []
    for serialiser in targets:
        body, keys = keys_of(serialiser, profile, texts)
        if not keys:
            print("0x%-8X no key-like strings" % serialiser)
            continue
        pairs = []
        touched = {}
        for position, (index, address, text) in enumerate(keys):
            end = keys[position + 1][0] if position + 1 < len(keys) else len(body)
            segment = body[index:end]
            offsets = body_offsets(segment)
            for offset, (width, at) in offsets.items():
                touched[offset] = min(width, touched.get(offset, 99))
            pairs.append((text, offsets, len(segment)))
        print("=== 0x%-8X %6d bytes  %2d keys" % (serialiser, (profile.get(serialiser) or {}).get("size") or 0,
                                                  len(keys)))
        for text, offsets, span in pairs[:args.limit]:
            shown = ", ".join("+0x%X:%s" % (o, offsets[o][0]) for o in sorted(offsets))
            mark = "PAIRED" if len(offsets) == 1 else ("%d offsets" % len(offsets) if offsets else "none")
            print("    %-36s %-44s %s" % (text[:36], shown[:44], mark))
        print("")

        if args.match and touched:
            best = []
            for name, fields in structs.items():
                hit = [o for o in touched if o in fields]
                agree = [o for o in hit if fields[o][1] and fields[o][1] == touched[o]]
                best.append((len(agree), len(hit), name, len(fields)))
            best.sort(reverse=True)
            summary.append((serialiser, len(touched), best[:3]))

    if args.match:
        print("which declared object each serialiser's accesses fit (offsets agreeing in width):")
        print("")
        for serialiser, count, best in summary:
            print("0x%-8X %2d offsets touched" % (serialiser, count))
            for agree, hit, name, total in best:
                print("      %-28s %2d/%2d agreeing, %2d in the declaration (%d fields)"
                      % (name, agree, count, hit, total))
            print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
