# -*- coding: utf-8 -*-
"""Which vtable belongs to which strategy class, from the recovered strategy list.

Usage: python g_strategy_vtables.py [--out re/CLASSES.md]

re/STRATEGY_METHODS.md already names the strategy classes and their Run bodies -- Multi::TilingNester Run at slot 5 is
0x46940, 16258 bytes, and so on for eleven of them plus the Pack family. What it does not carry is the VTABLE ADDRESS, and
re/CLASSES.md carries the addresses but not the class names, because the mangled name of a vtable is just the namespace when
the class is a template instantiation.

This joins them by slot 5: a strategy class's Run is its largest method and it sits at the same slot in every strategy, so
the vtable whose slot 5 is 0x46940 IS Multi::TilingNester. The result is a table of strategy class -> vtable address -> Run
address -> Run size, which is what makes the twelve Run bodies addressable: their classes can now be looked up in
CLASSES.md and their member regions read out of their own methods.

It also writes the mapping into re/CLASSES.md as a column, so the class table stops saying fourteen anonymous `Multi` rows.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ROOT = os.path.dirname(HERE)

# name -> the rva of its Run body, from re/STRATEGY_METHODS.md.
STRATEGIES = {
    "Multi::TilingNester": 0x46940,
    "Multi::NestingNester": 0x378E0,
    "Multi::RowNester": 0x913E0,
    "Multi::MultiTorchNester": 0x7BCC0,
    "Multi::CompactNester": 0xB13D0,
    "Multi::NoFillNester": 0x7F240,
    "Multi::RectangleNester": 0x75FB0,
    "Multi::DatabaseNester": 0x5B250,
    "Multi::FlipNester": 0x4B870,
    "Multi::FilterNester": 0xB3AE0,
    "Multi::LimitedNester": 0x4AB40,
}


def main(argv):
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    data = json.load(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8"))

    by_run = {}
    for mangled, info in data.items():
        slots = info.get("slots") or []
        if not slots:
            continue
        largest = max((s for s in slots if s), key=lambda s: 0) if False else None
        # slot 5 is where every strategy's Run sits, per re/STRATEGY_METHODS.md
        if len(slots) > 5 and slots[5] in STRATEGIES.values():
            by_run.setdefault(slots[5], []).append((info.get("vtable_rva") or 0, mangled))

    missing = [name for name, run in STRATEGIES.items() if run not in by_run]
    print("strategy Run bodies found in a vtable slot 5: %d of %d" % (len(STRATEGIES) - len(missing), len(STRATEGIES)))
    print("")
    mapping = {}
    for name, run in sorted(STRATEGIES.items(), key=lambda kv: kv[1]):
        entries = by_run.get(run)
        if entries:
            vtable, mangled = entries[0]
            mapping[vtable] = name
            print("  %-28s vtable 0x%-8X Run 0x%-8X  (%s)" % (name, vtable, run, mangled[:40]))
        else:
            print("  %-28s Run 0x%-8X  -- not found as a slot 5 in vtables.json" % (name, run))
    if missing:
        print("")
        print("missing: %s" % ", ".join(missing))

    if out:
        path = os.path.join(ROOT, out.replace("/", os.sep))
        text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        lines = text.split("\n")
        replaced = 0
        for index, line in enumerate(lines):
            m = re.match(r"\| `0x([0-9A-F]+)` \| `([A-Za-z:]+)` \|", line)
            if not m:
                continue
            vtable = int(m.group(1), 16)
            if vtable in mapping:
                lines[index] = line.replace("| `%s` |" % m.group(2), "| `%s` |" % mapping[vtable], 1)
                replaced += 1
        io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
        print("")
        print("replaced %d anonymous class names in %s with the strategy names" % (replaced, out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
