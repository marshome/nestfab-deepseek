# -*- coding: utf-8 -*-
"""Remove the block that tested moduleSwitch_1BF00 and engineFetch_1BF40 through deleted accessors.

The block drove four reads and writes of a module-static buffer through `moduleSwitch_1BF00` and `engineFetch_1BF40`, which were accessors.
**Those two are worth keeping as WORK** -- they are named and their addresses are in re/pending_operations.md -- but the block cannot stand
without the functions, and leaving orphaned variables produces the warnings the gate refuses.
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_boxacc.cpp"
START_MARK = "module_static"


def main():
    lines = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n").split("\n")
    # find the enclosing block: walk back to the `{` line that opens it, forward to the matching `}`
    target = next(index for index, line in enumerate(lines) if START_MARK in line)
    start = target
    while start > 0 and lines[start].count("{") - lines[start].count("}") == 0:
        start -= 1
        if lines[start].strip() == "{":
            break
    # the block's header comment, two lines up if there is one
    while start > 0 and lines[start - 1].strip().startswith("//"):
        start -= 1
    depth = 0
    end = start
    while end < len(lines):
        depth += lines[end].count("{") - lines[end].count("}")
        end += 1
        if depth == 0 and "{" in "\n".join(lines[start:end]):
            break
    print("removing lines %d..%d" % (start + 1, end))
    replacement = [
        "    // ------------------------------------------------------------------ moduleSwitch and engineFetch, DELETED",
        "    //",
        "    // A block stood here driving the module-static buffer through `moduleSwitch_1BF00` and `engineFetch_1BF40`. **Both are worth",
        "    // keeping as WORK** -- their names say what they do and their addresses are recorded in re/pending_operations.md -- but they were",
        "    // memcpy accessors built on 96 more of the same, and the file is deleted. **The right form is each of them placed in the class",
        "    // whose object it acts on**, which is the work this block records rather than performs.",
        "",
    ]
    out = lines[:start] + replacement + lines[end:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("lines now %d" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
