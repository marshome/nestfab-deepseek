# -*- coding: utf-8 -*-
"""Remove the class-constructors test block by LINE NUMBERS, and put the member-based assertions in its place.

The text-bounded version failed because the two comment headers it searched for do not both appear -- so the bounds are taken from the file's
own block headers, read with the tool that will edit the file.
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

REPLACEMENT = '''    // ---------------------------------------------------------------- every class's constructor, AS A MEMBER
    //
    // A `ClassConstructor` TABLE stood here: six columns keyed by class name, of which ONE was a fact about the module -- the address of the
    // function that builds each class. The others were the vtable (already a constant in each class), a field COUNT (countable from the
    // declared fields), and two statistics about MY SCAN, which are not facts about the module at all. **The address is now `kConstructor`
    // inside each class**, which is C++; the same number in a row keyed by a string is a registry, and this project has the registries it
    // needs.
    {
        using lcns::Multi::SplitNode;
        using lcns::Multi::TerminalNode;
        CHECK(SplitNode::kConstructor == 0x99910u);       // RE the slot-0 reference that finds it
        CHECK(SplitNode::kVtable == 0xA3BB70u);
        CHECK(TerminalNode::kConstructor == 0x99360u);
        CHECK(TerminalNode::kVtable == 0xA3B570u);
        // a class whose constructor writes no field still knows its constructor, which the table could state only as a row
        CHECK(SplitNode::kConstructor != TerminalNode::kConstructor);
    }

'''


def main():
    lines = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n").split("\n")
    headers = [(index, line) for index, line in enumerate(lines) if re.match(r"^    // -{20,} ", line)]
    start = end = None
    for index, line in headers:
        if "every class's constructor" in line and index > 7000:
            start = index
        elif start is not None and index > start:
            end = index
            break
    if start is None or end is None:
        print("the block bounds are not found: start=%s end=%s" % (start, end))
        return 1
    print("replacing lines %d..%d" % (start + 1, end))
    out = lines[:start] + REPLACEMENT.split("\n") + lines[end:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("lines now %d" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
