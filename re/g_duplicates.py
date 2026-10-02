# -*- coding: utf-8 -*-
"""Duplicate structures: declared types that describe the same thing, found by their shape.

Usage:
    python g_duplicates.py                 -> every suspicious pair, strongest first
    python g_duplicates.py --all           -> also the pairs with a weak signal
    python g_duplicates.py --type NAME     -> everything that looks like NAME

The human asked whether Order and LaunchingOrderLayout are duplicates. They are: two independent declarations of the launch
order, in nester.hpp and launching_order.hpp, and nothing in the project compared them. The question is worth generalising,
because a duplicate declaration is the failure mode this repository is most exposed to -- a recovered layout written once for
the implementation and once for the tests, or twice under different names in different rounds, drifts silently and the two
copies stop agreeing.

The signal is SHAPE, not name:

  * the same field NAMES in the same order -- the strongest, since a recovered layout's names are its evidence;
  * the same SIZES at the same offsets with different names -- a second declaration of one object;
  * the same field count and comparable size with overlapping names -- worth a look.

Fields are read from the declarations themselves, with an optional `// +0x..` comment giving the offset and an optional
`// RE 0x..` giving the evidence, because that is how this project writes a recovered layout.

This is a report, not a refactor: two structures that describe one object is sometimes right (a public view and a private
layout), and the tool prints the evidence for a reader to decide. What it refuses to do is stay quiet.
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

# A field line: a type, a name, and optionally the offset and the evidence in the comment.
FIELD = re.compile(r"^\s*((?:std::)?(?:u?int\d+_t|int|long|short|char|float|double|bool|size_t|std::size_t|"
                   r"unsigned\s+char|unsigned\s+int|void\s*\*|[A-Z]\w*(?:::\w+)*)(?:\s*\*)?)\s+"
                   r"([A-Za-z_]\w*)\s*(?:\[\s*\d+\s*\])?\s*;\s*(?://\s*(.*))?$")
STRUCT = re.compile(r"^\s*(struct|class)\s+([A-Za-z_]\w*)\s*(?::[^{]*)?\{")
OFFSET_IN_COMMENT = re.compile(r"\+0x([0-9A-Fa-f]+)")
RE_IN_COMMENT = re.compile(r"RE\s*(0x[0-9A-Fa-f]+)")
BITFIELD = re.compile(r"^\s*A\(([A-Za-z_]\w*)\)\s*$")


def type_size(type_text):
    """The size of a field's type where it is a scalar this project uses, else None."""
    text = type_text.strip()
    if "*" in text:
        return 8
    table = {"char": 1, "bool": 1, "unsigned char": 1, "std::uint8_t": 1, "uint8_t": 1,
             "short": 2, "unsigned short": 2, "std::uint16_t": 2, "uint16_t": 2,
             "int": 4, "unsigned int": 4, "long": 4, "float": 4,
             "std::uint32_t": 4, "uint32_t": 4, "int32_t": 4,
             "double": 8, "long long": 8, "std::uint64_t": 8, "uint64_t": 8, "size_t": 8, "std::size_t": 8,
             "std::int64_t": 8, "int64_t": 8}
    return table.get(text)


def declared_types():
    """name -> {fields, size from the static_assert, file, line, list of (name, offset, type, evidence)}."""
    out = {}
    patterns = ["lcns/include/lcns/*.hpp", "lcns/include/lcns/**/*.hpp", "lcns/src/*.cpp", "lcns/tests/*.cpp"]
    for pattern in patterns:
        for path in glob.glob(os.path.join(ROOT, pattern), recursive=True):
            text = io.open(path, encoding="utf-8", errors="replace").read()
            lines = text.split("\n")
            current = None
            for number, line in enumerate(lines, 1):
                m = STRUCT.match(line)
                if m:
                    current = m.group(2)
                    if current not in out:
                        out[current] = {"fields": [], "assembled": [], "size": None,
                                        "file": os.path.relpath(path, ROOT).replace("\\", "/"), "line": number}
                    continue
                if current is None:
                    continue
                if line.strip() == "};":
                    current = None
                    continue
                entry = out[current]
                b = BITFIELD.match(line)
                if b:
                    entry["assembled"].append(b.group(1))
                    continue
                f = FIELD.match(line)
                if f:
                    comment = f.group(3) or ""
                    offset = OFFSET_IN_COMMENT.search(comment)
                    evidence = RE_IN_COMMENT.search(comment)
                    entry["fields"].append({
                        "type": f.group(1).strip(),
                        "name": f.group(2),
                        "offset": int(offset.group(1), 16) if offset else None,
                        "size": type_size(f.group(1)),
                        "evidence": evidence.group(1) if evidence else None,
                    })
            # a size assertion anywhere in the same file mentioning the type
            for match in re.finditer(r"static_assert\s*\(\s*sizeof\(\s*(\w+)\s*\)\s*==\s*(0x[0-9A-Fa-f]+)", text):
                if match.group(1) in out:
                    out[match.group(1)]["size"] = int(match.group(2), 16)
    # expand the A(...) bit fields: their declaration string gives the packed layout
    for path in glob.glob(os.path.join(ROOT, "lcns/include/lcns/**/*.hpp"), recursive=True):
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in re.finditer(r"#define\s+A\(([A-Za-z_]\w*)\)\s*(.*)", text):
            macro = match.group(1)
            body = match.group(2)
            out.setdefault("__macros__", {"fields": [], "assembled": [], "size": None, "file": "", "line": 0})
            out["__macros__"].setdefault("macros", {})[macro] = body
    return out


def similarity(a, b):
    """(score, why) for two declarations, from their shapes."""
    fa, fb = a["fields"], b["fields"]
    if not fa or not fb:
        return 0.0, ""
    names_a = [f["name"] for f in fa]
    names_b = [f["name"] for f in fb]
    shared_names = [n for n in names_a if n in names_b]
    score = 0.0
    why = []
    if names_a == names_b:
        score = 1.0
        why.append("identical field names in the same order (%d fields)" % len(names_a))
    elif shared_names:
        overlap = len(shared_names) / float(max(len(names_a), len(names_b)))
        score = 0.4 + 0.4 * overlap
        why.append("%d of %d field names shared" % (len(shared_names), max(len(names_a), len(names_b))))
    offsets_a = {f["offset"]: f for f in fa if f["offset"] is not None}
    offsets_b = {f["offset"]: f for f in fb if f["offset"] is not None}
    if offsets_a and offsets_b:
        same_offsets = set(offsets_a) & set(offsets_b)
        if same_offsets:
            agreeing = [o for o in same_offsets
                        if offsets_a[o]["size"] and offsets_a[o]["size"] == offsets_b[o]["size"]]
            if len(same_offsets) >= 4:
                score = max(score, 0.5 + 0.4 * (len(same_offsets) / float(max(len(offsets_a), len(offsets_b)))))
                why.append("%d offsets in common, %d with the same width" % (len(same_offsets), len(agreeing)))
    if a.get("size") and a.get("size") == b.get("size"):
        score = min(1.0, score + 0.2)
        why.append("both assert sizeof == 0x%X" % a["size"])
    if a.get("assembled") and a["assembled"] == b.get("assembled"):
        score = max(score, 0.9)
        why.append("the same %d assembled field names" % len(a["assembled"]))
    return score, "; ".join(why)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--type", default=None)
    parser.add_argument("--threshold", type=float, default=0.4)
    args = parser.parse_args(argv)

    types = {name: value for name, value in declared_types().items() if name != "__macros__"}
    print("declared types with fields: %d" % len(types))
    with_fields = {n: v for n, v in types.items() if len(v["fields"]) >= 3}
    print("of those, with 3 or more fields: %d" % len(with_fields))
    print("")

    pairs = []
    names = sorted(with_fields)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = with_fields[names[i]], with_fields[names[j]]
            score, why = similarity(a, b)
            if score >= (0.0 if args.all else args.threshold):
                pairs.append((score, names[i], names[j], why, a, b))
    pairs.sort(key=lambda p: -p[0])

    by_name = defaultdict(list)
    for score, left, right, why, a, b in pairs:
        by_name[left].append((score, right, why))
        by_name[right].append((score, left, why))

    if args.type:
        related = sorted(by_name.get(args.type, []), reverse=True)
        if not related:
            print("%s has no similar declaration" % args.type)
            return 0
        entry = with_fields.get(args.type) or types.get(args.type)
        print("%s: %d fields, declared at %s:%d%s"
              % (args.type, len(entry["fields"]), entry["file"], entry["line"],
                 (", sizeof 0x%X" % entry["size"]) if entry.get("size") else ""))
        for index, field in enumerate(entry["fields"]):
            print("    %-22s %-28s %s" % (field["type"], field["name"],
                                          ("+0x%X" % field["offset"]) if field["offset"] is not None else ""))
        print("")
        for score, other, why in related:
            print("    %.2f  %s -- %s" % (score, other, why))
        return 0

    print("suspicious pairs, strongest first (score, the two types, and the evidence):")
    print("")
    for score, left, right, why, a, b in pairs[:30]:
        print("%.2f  %-28s %-28s %s" % (score, left, right, why))
        print("      %s:%d  versus  %s:%d" % (a["file"], a["line"], b["file"], b["line"]))
    print("")
    strong = [p for p in pairs if p[0] >= 0.8]
    print("%d pairs at 0.8 or above -- those are duplicates by field names or assembled names" % len(strong))
    print("%d pairs above the %.2f threshold in total" % (len(pairs), args.threshold))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
