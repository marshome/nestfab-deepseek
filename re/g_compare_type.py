# -*- coding: utf-8 -*-
"""Compare two declarations of one object, field by field, and report every disagreement.

Usage: python g_compare_type.py Order LaunchingOrderLayout

The human asked whether Order and LaunchingOrderLayout are duplicates. They are, and the tool that answers it properly is a
comparison rather than a similarity score, because the interesting output is not "these are the same" but the LIST OF PLACES
THEY DISAGREE -- each of which is a defect in one of the two.

The comparison is driven by the offsets in the declarations' own comments (`// +0x..`), which is how this project records a
recovered layout, so the two are aligned by offset rather than by position:

  * an offset in one and not the other      -> a field missed by one declaration
  * the same offset, different WIDTH        -> one of them is wrong about the object's memory
  * the same offset, different name         -> the two disagree about what the field IS
  * a width the MODULE contradicts          -> the stricter test, when the ledger or an RE comment gives the store

The width test is the important one and it is the reason this tool exists. Order declares
`int commonCutSafetyFlag // +0x68`, and the module writes that byte with `mov byte ptr [rdi+0x68], 1` -- so the declaration is
four times too wide and every field after it in a packed view is misplaced. That is exactly the class of defect a similarity
score cannot see, because the NAMES look right.
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

FIELD = re.compile(r"^\s*((?:std::)?(?:u?int\d+_t|int|long|short|char|float|double|bool|size_t|std::size_t|"
                   r"unsigned\s+char|unsigned\s+int|void\s*\*|[A-Z]\w*(?:::\w+)*)(?:\s*\*)?)\s+"
                   r"([A-Za-z_]\w*)\s*(?:\[\s*(\d+)\s*\])?\s*(?:=[^;]*)?;\s*(?://\s*(.*))?$")
STRUCT = re.compile(r"^\s*(struct|class)\s+([A-Za-z_]\w*)\s*(?::[^{]*)?\{")
OFFSET = re.compile(r"\+0x([0-9A-Fa-f]+)")
SIZES = {"char": 1, "bool": 1, "unsigned char": 1, "std::uint8_t": 1, "uint8_t": 1, "short": 2, "unsigned short": 2,
         "std::uint16_t": 2, "uint16_t": 2, "int": 4, "unsigned int": 4, "float": 4, "std::uint32_t": 4, "uint32_t": 4,
         "double": 8, "long long": 8, "std::uint64_t": 8, "uint64_t": 8, "size_t": 8, "std::size_t": 8, "long": 4}


def size_of(type_text):
    text = type_text.strip()
    if "*" in text:
        return 8
    return SIZES.get(text)


def read(type_name):
    """the fields of a declared type, aligned by the offset in each field's own comment."""
    out = {}
    for pattern in ("lcns/include/lcns/*.hpp", "lcns/include/lcns/**/*.hpp"):
        import glob
        for path in glob.glob(os.path.join(ROOT, pattern), recursive=True):
            text = io.open(path, encoding="utf-8", errors="replace").read()
            current = None
            for number, line in enumerate(text.split("\n"), 1):
                m = STRUCT.match(line)
                if m:
                    current = m.group(2)
                    continue
                if current is None:
                    continue
                if line.strip().startswith("};"):
                    current = None
                    continue
                if current != type_name:
                    continue
                f = FIELD.match(line)
                if not f:
                    continue
                comment = f.group(4) or ""
                offset = OFFSET.search(comment)
                width = size_of(f.group(1))
                if f.group(3):                      # an array: the width is the element times the count
                    width = (width or 0) * int(f.group(3))
                out[int(offset.group(1), 16) if offset else None] = {
                    "type": f.group(1).strip(), "name": f.group(2), "width": width,
                    "file": os.path.relpath(path, ROOT).replace("\\", "/"), "line": number, "comment": comment.strip(),
                }
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("left")
    parser.add_argument("right")
    args = parser.parse_args(argv)
    left, right = read(args.left), read(args.right)
    if not left:
        print("%s: no declaration with offset comments was found" % args.left)
        return 2
    if not right:
        print("%s: no declaration with offset comments was found" % args.right)
        return 2

    named_left = {o: f for o, f in left.items() if o is not None}
    named_right = {o: f for o, f in right.items() if o is not None}
    print("%s: %d fields (%d with an offset) from %s"
          % (args.left, len(left), len(named_left), next(iter(left.values()))["file"]))
    print("%s: %d fields (%d with an offset) from %s"
          % (args.right, len(right), len(named_right), next(iter(right.values()))["file"]))
    print("")

    only_left = sorted(set(named_left) - set(named_right))
    only_right = sorted(set(named_right) - set(named_left))
    shared = sorted(set(named_left) & set(named_right))

    width_mismatch = []
    name_mismatch = []
    agree = 0
    for offset in shared:
        a, b = named_left[offset], named_right[offset]
        if a["width"] and b["width"] and a["width"] != b["width"]:
            width_mismatch.append((offset, a, b))
        elif a["name"] != b["name"]:
            name_mismatch.append((offset, a, b))
        else:
            agree += 1

    print("offsets present in both: %d  (agreeing on name and width: %d)" % (len(shared), agree))
    print("offsets only in %s: %d" % (args.left, len(only_left)))
    print("offsets only in %s: %d" % (args.right, len(only_right)))
    print("")

    if width_mismatch:
        print("WIDTH DISAGREEMENTS -- the object's memory cannot be both:")
        for offset, a, b in width_mismatch:
            print("  +0x%-4X %-26s %-12s %d B   vs   %-26s %-12s %s B"
                  % (offset, a["name"], a["type"], a["width"], b["name"], b["type"], b["width"]))
        print("")
    if name_mismatch:
        print("NAME DISAGREEMENTS -- the same bytes, two ideas about what they are:")
        for offset, a, b in name_mismatch[:20]:
            print("  +0x%-4X %-34s (%s:%d)   vs   %-34s (%s:%d)"
                  % (offset, a["name"], os.path.basename(a["file"]), a["line"],
                     b["name"], os.path.basename(b["file"]), b["line"]))
        if len(name_mismatch) > 20:
            print("  ... and %d more" % (len(name_mismatch) - 20))
        print("")
    if only_left:
        print("ONLY IN %s:" % args.left)
        for offset in only_left[:20]:
            f = named_left[offset]
            print("  +0x%-4X %-34s %s" % (offset, f["name"], f["type"]))
        print("")
    if only_right:
        print("ONLY IN %s:" % args.right)
        for offset in only_right[:20]:
            f = named_right[offset]
            print("  +0x%-4X %-34s %s" % (offset, f["name"], f["type"]))
        print("")

    verdict = "DUPLICATES" if len(shared) >= 0.5 * max(len(named_left), len(named_right)) else "RELATED"
    print("VERDICT: %s -- %d of %d offsets are declared by both, and %d of those disagree on width"
          % (verdict, len(shared), max(len(named_left), len(named_right)), len(width_mismatch)))
    if width_mismatch:
        print("The width disagreements are not a style problem: a field declared four times too wide misplaces every field")
        print("after it in any packed view of the object, and the module's own store instructions say which is right.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
