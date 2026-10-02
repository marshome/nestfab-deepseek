# -*- coding: utf-8 -*-
"""Have the test NAME every generated member struct, which check_recovery requires and which the generated file needs."""
import io
import re
import sys

HEADER = r"D:\Nesting\nestfab\lcns\include\lcns\named_members.hpp"
TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
MARKER = "        // THE REGION BETWEEN PLACED FIELDS IS NAMED"


def main():
    header = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    names = re.findall(r"^struct (\w+) \{", header, re.M)
    if len(names) < 6:
        print("REFUSING: only %d structs found in the generated header" % len(names))
        return 2
    print("the generated header declares %d member structs" % len(names))

    lines = ["        // EVERY GENERATED MEMBER STRUCT IS NAMED, which check_recovery requires: a declaration nothing refers to is a declaration",
             "        // nobody has checked. **Each is also INSTANTIATED**, because a struct that does not compile is not a declaration either.",
             "        {"]
    for index, name in enumerate(sorted(names)):
        lines.append("            lcns::%s instance%d{}; (void)instance%d;" % (name, index, index))
    lines.append("        }")
    block = "\n".join(lines) + "\n\n"

    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "instance0{}" in text:
        print("already present")
        return 0
    if MARKER not in text:
        print("the insertion marker is gone")
        return 1
    text = text.replace(MARKER, block + MARKER, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("named and instantiated %d structs; lines now %d" % (len(names), text.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
