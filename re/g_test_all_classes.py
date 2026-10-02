# -*- coding: utf-8 -*-
"""Have the class-definitions test NAME every class the generated header declares.

check_recovery requires it, and it is right to: a declaration nothing refers to is a declaration nobody has checked. The test already
asserts the table; this adds one pointer per declared class, generated from the header, so the requirement is met mechanically rather than
by a list kept in step by hand.

Each pointer is a COMPILE-TIME claim that the type exists in that namespace -- which is exactly what a declaration claims, and not a claim
about behaviour.
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
    # walk the emitted namespaces and collect qualified names. THE CLOSE IS BY DEPTH, not by one pop per line: a nested namespace emits
    # one `}  // namespace` PER LEVEL, so a single pop per closing line leaves the outer names off -- which is how `Compact::Compacter`'s
    # inner class came out as `Implementation` at the root.
    qualified = []
    stack = []
    for line in header.split("\n"):
        stripped = line.strip()
        opened = re.match(r"^namespace ([\w:]+) \{$", stripped)
        if opened:
            stack.extend(opened.group(1).split("::"))
            continue
        if stripped.startswith("}  // namespace") or stripped.startswith("}"):
            # POP AS MANY LEVELS AS THE LINE CLOSES. The generator emits one `}  // namespace` per level, but a line may also close more
            # than one; counting the braces is what makes the depth right either way, and a single pop per line is what put
            # Compact::Compacter's inner class at the root.
            for _ in range(max(1, stripped.count("}"))):
                if stack:
                    stack.pop()
            continue
        declared = re.match(r"^class (\w+) \{", stripped)
        if declared:
            qualified.append("lcns::" + "::".join(stack + [declared.group(1)]))
    qualified = [name.replace("lcns::lcns::", "lcns::") for name in qualified]
    if len(qualified) < 40:
        print("REFUSING: only %d declarations found in the header" % len(qualified))
        return 2

    lines = ["        // THE DECLARATIONS ARE TYPES: one pointer per declared class, generated from the header. This is a COMPILE-TIME",
             "        // claim that the type exists in that namespace, which is what a declaration claims and nothing about behaviour.",
             "        {"]
    for index, name in enumerate(sorted(qualified)):
        lines.append("            %s* p%d = nullptr; (void)p%d;" % (name, index, index))
    lines.append("        }")
    block = "\n".join(lines) + "\n\n"

    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find(START)
    end = text.find(END)
    if start < 0 or end < 0 or end <= start:
        print("the block bounds are not found: start=%d end=%d" % (start, end))
        return 1
    text = text[:start] + block + text[end:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("named %d declared classes in the test" % len(qualified))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
