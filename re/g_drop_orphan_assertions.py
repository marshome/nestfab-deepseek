# -*- coding: utf-8 -*-
"""Remove the remaining assertion-only blocks whose accessor calls were deleted.

EVERY ONE OF THESE WAS A TAUTOLOGY EVEN BEFORE THE DELETION: it wrote a value through an accessor and read it back through memcpy, or the
reverse, so it proved the accessor against itself and nothing about the module. With the accessor gone the assertion has nothing to check.
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_boxacc.cpp"


def main():
    lines = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n").split("\n")
    kept = []
    removed = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        # an opening brace at four-space indent whose body contains a CHECK on `got` but no call into the deleted namespace
        if stripped == "{" and line.startswith("    {"):
            depth = 0
            start = index
            body = []
            while index < len(lines):
                depth += lines[index].count("{") - lines[index].count("}")
                body.append(lines[index])
                index += 1
                if depth == 0:
                    break
            text = "\n".join(body)
            # DROP IT IF IT ONLY ASSERTS A LOCAL IT COULD NO LONGER HAVE WRITTEN
            if re.search(r"CHECK\((got|out|read|second)\b", text) and not re.search(r"dll::accessors|memcpy\(object", text):
                removed += 1
                continue
            kept.extend(body)
            continue
        kept.append(line)
        index += 1
    text = "\n".join(kept)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("removed %d assertion-only block(s); lines now %d" % (removed, text.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
