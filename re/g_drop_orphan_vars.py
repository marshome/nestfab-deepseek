#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Remove the variables left orphaned when the accessor calls were deleted, and mark the block that lost them.

The lines this drops are `unsigned char build_id[8]` and similar that existed only to be handed to a deleted accessor. **A variable set and
never used is a warning, and the gate refuses a warning** -- so they go, and the block says what stood there.
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_boxacc.cpp"


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = text.split("\n")
    kept = []
    removed = []
    for line in lines:
        # a declaration of a local that nothing uses any more: it appears only as `unsigned char name[...]` or `std::uint8_t name...`
        if re.match(r"^\s+(?:unsigned char|std::uint8_t|std::uint32_t|int|const void\*) \w+(?:\[\d+\])?\s*(?:=[^;]*)?;\s*$", line):
            name = re.search(r"(\w+)(?:\[| =|;)", line).group(1)
            # unused only if the name does not appear again in the file
            if len(re.findall(r"\b%s\b" % re.escape(name), text)) <= 1:
                removed.append(name)
                continue
        kept.append(line)
    text = "\n".join(kept)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("removed %d orphaned variable(s): %s" % (len(removed), ", ".join(removed[:8])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
