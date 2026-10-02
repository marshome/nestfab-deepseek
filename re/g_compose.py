# -*- coding: utf-8 -*-
"""Find every structure embedded in another, by looking for a CONSTANT offset difference.

Usage:
    python g_compose.py                      -> every embedding found, with its evidence
    python g_compose.py --host LaunchingOrderLayout
    python g_compose.py --prove 0x50         -> the arithmetic for one base

Round 550 proved that CommonCutProperties is embedded at +0x50 of the launch order, and the proof was an arithmetic difference
rather than a shape:

    CommonCutProperties.noHoles       +0x34   ->   Order.commonCutNoHoles       +0x84    difference 0x50
    CommonCutProperties.onlyBiModules +0x35   ->   Order.commonCutOnlyBiModules +0x85    difference 0x50

Two independent differences agreeing is what makes it a proof, and the method generalises into something a program can run: for
every pair of declared structures, compute the difference for every matching pair of offsets, and report the ones where a SINGLE
difference explains several matches.

That is what this does, and the strength is in the count rather than in the story:

    2 agreeing differences   a coincidence is still possible
    3 or more                the inner structure is embedded at that base, and the count is the evidence

A match requires the offset to line up AND the widths to agree, because a host with a byte where the inner declares a double is
not the same object. `--prove` prints the arithmetic for one base so a reader can check it instead of trusting the count.

Why this beats the shape method that came first: round 539 found a candidate at parent +0x40 because 15 functions derived its
address with `lea`, which is suggestive and unprovable, and that claim is still at SHAPE. Two subtractions that agree cannot be
explained away by a shared idiom.
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

SIZES = {"char": 1, "bool": 1, "unsigned char": 1, "std::uint8_t": 1, "uint8_t": 1, "short": 2, "unsigned short": 2,
         "std::uint16_t": 2, "uint16_t": 2, "int": 4, "unsigned int": 4, "float": 4, "std::uint32_t": 4, "uint32_t": 4,
         "double": 8, "long long": 8, "std::uint64_t": 8, "uint64_t": 8, "size_t": 8, "std::size_t": 8, "long": 4}
FIELD = re.compile(r"^\s*((?:std::)?(?:u?int\d+_t|int|long|short|char|float|double|bool|size_t|std::size_t|"
                   r"unsigned\s+char|unsigned\s+int|void\s*\*|[A-Z]\w*(?:::\w+)*)(?:\s*\*)?)\s+"
                   r"([A-Za-z_]\w*)\s*(?:\[\s*(\d+)\s*\])?\s*(?:=[^;]*)?;\s*(?://\s*(.*))?$")


def width_of(type_text, count=None):
    text = type_text.strip()
    width = 8 if "*" in text else SIZES.get(text)
    if count and width:
        width *= int(count)
    return width


def declarations():
    """struct name -> {offset: (field, width, file, line)}, for every struct whose offsets are commented."""
    out = {}
    for path in glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "**", "*.hpp"), recursive=True):
        text = io.open(path, encoding="utf-8", errors="replace").read()
        current = None
        for number, line in enumerate(text.split("\n"), 1):
            m = re.match(r"\s*(?:struct|class)\s+(\w+)", line)
            if m:
                current = m.group(1)
                out.setdefault(current, {})
                continue
            if current is None:
                continue
            if line.strip().startswith("};"):
                current = None
                continue
            f = FIELD.match(line)
            if not f:
                continue
            o = re.search(r"\+0x([0-9A-Fa-f]+)", f.group(4) or "")
            if not o:
                continue
            out[current][int(o.group(1), 16)] = (f.group(2), width_of(f.group(1), f.group(3)),
                                                 os.path.relpath(path, ROOT).replace("\\", "/"), number)
    return {k: v for k, v in out.items() if len(v) >= 2}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=None)
    parser.add_argument("--prove", type=lambda v: int(v, 0), default=None)
    parser.add_argument("--min", type=int, default=2, help="how many agreeing differences make an embedding")
    parser.add_argument("--fraction", type=float, default=0.6,
                        help="how much of the inner structure the differences must explain")
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args(argv)

    structs = declarations()
    names = sorted(structs)
    print("declared structures with commented offsets: %d" % len(names))
    print("")

    found = []
    for outer in names:
        if args.host and outer != args.host:
            continue
        outer_fields = structs[outer]
        for inner in names:
            if inner == outer:
                continue
            inner_fields = structs[inner]
            by_difference = defaultdict(list)
            for i_offset, (i_name, i_width, _if, _il) in inner_fields.items():
                for o_offset, (o_name, o_width, _of, _ol) in outer_fields.items():
                    if o_offset <= i_offset:
                        continue
                    if i_width and o_width and i_width != o_width:
                        continue
                    by_difference[o_offset - i_offset].append((i_offset, i_name, o_offset, o_name, i_width))
            for base, matches in by_difference.items():
                # A difference that explains ONE field is a coincidence, so a floor of two is the start. But a floor alone is
                # not enough, and the first run of this tool proved it: with only the floor it reported 793 embeddings out of 26
                # structures, because a two or three field struct can align by accident. Two further conditions do the real
                # work, and both come from what an embedding MEANS:
                #
                #   COVERAGE    the differences must explain a large share of the inner structure. An embedding is the whole
                #               object present in the host, not a couple of fields that happen to line up.
                #   CONTAINMENT every OTHER field of the inner structure must land inside a field of the host at the same
                #               base, even where the widths differ -- because if the inner object really is there, its layout
                #               occupies those bytes and cannot fall into a gap.
                if len(matches) < args.min:
                    continue
                if len(matches) < args.fraction * len(inner_fields):
                    continue
                explained = {m[0] for m in matches}
                contradicted = 0
                for i_offset, (_n, _w, _f, _l) in inner_fields.items():
                    if i_offset in explained:
                        continue
                    if (i_offset + base) not in outer_fields:
                        contradicted += 1
                if contradicted:
                    continue
                found.append((len(matches), outer, inner, base, matches))

    found.sort(key=lambda f: -f[0])
    print("embeddings found (one difference explaining several fields, with containment): %d" % len(found))
    print("")
    for count, outer, inner, base, matches in found[:args.top]:
        print("=== %s contains %s at +0x%X   (%d agreeing fields)" % (outer, inner, base, count))
        for i_offset, i_name, o_offset, o_name, i_width in sorted(matches)[:6]:
            print("      %-28s +0x%-5X = %-28s +0x%-5X  %s B"
                  % (i_name, i_offset, o_name, o_offset, i_width if i_width else "?"))
        print("")

    if args.prove is not None:
        print("the arithmetic for base +0x%X, which is the evidence:" % args.prove)
        any_shown = False
        for count, outer, inner, base, matches in found:
            if base != args.prove:
                continue
            any_shown = True
            print("  %s at +0x%X of %s, by %d independent differences:" % (inner, base, outer, count))
            for i_offset, i_name, o_offset, o_name, _iw in sorted(matches):
                print("      %s +0x%X -> %s +0x%X    0x%X - 0x%X = 0x%X"
                      % (inner, i_offset, outer, o_offset, o_offset, i_offset, o_offset - i_offset))
        if not any_shown:
            print("  nothing found at that base")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
