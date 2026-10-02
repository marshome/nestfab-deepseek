# -*- coding: utf-8 -*-
"""Replace the compiler-pointer block with names taken from the header's own doc comments.

A third attempt at parsing the namespace nesting is not worth making. **The generator writes the qualified name into the doc comment above
every declaration** -- `/** Multi::AllSheetSelector -- vtable 0xA3B840, 4 virtual slot(s). */` -- so the answer is already in the file and
reading it needs no depth tracking at all.

That is the lesson the last three attempts earned: when a structure is ambiguous to a parser, look for a place where the producer stated it
unambiguously rather than re-deriving it.
"""
import io
import os
import re

ROOT = r"D:\Nesting\nestfab"
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "class_definitions.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")

START = "        // THE DECLARATIONS ARE TYPES: one pointer per declared class, generated from the header. This is a COMPILE-TIME"
END = "        // a class already defined by hand is flagged"


def main():
    header = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    # the doc comment gives the qualified name; the declaration follows it
    qualified = re.findall(r"/\*\* ([\w:]+) -- vtable 0x[0-9A-F]+, \d+ virtual slot\(s\)\. \*/\nclass (\w+) \{", header)
    names = ["lcns::" + q for q, _short in qualified]
    # the outer namespace may already be in the comment's name
    names = [n.replace("lcns::lcns::", "lcns::") for n in names]
    if len(names) < 40:
        print("REFUSING: only %d names read from the doc comments" % len(names))
        return 2
    print("read %d qualified names from the header's own doc comments" % len(names))
    for name in names[:6]:
        print("   %s" % name)

    lines = ["        // THE DECLARATIONS ARE TYPES: one pointer per declared class, taken from the header's own doc comments, which",
             "        // state the qualified name. This is a COMPILE-TIME claim that the type exists in that namespace.",
             "        {"]
    for index, name in enumerate(sorted(names)):
        lines.append("            %s* p%d = nullptr; (void)p%d;" % (name, index, index))
    lines.append("        }")
    block = "\n".join(lines) + "\n\n"

    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find(START)
    end = text.find(END)
    if start < 0 or end < 0 or end <= start:
        print("block bounds not found: start=%d end=%d" % (start, end))
        return 1
    text = text[:start] + block + text[end:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote the block with %d names" % len(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
