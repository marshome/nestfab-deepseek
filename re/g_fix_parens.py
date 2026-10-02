# -*- coding: utf-8 -*-
"""Fix the parentheses the field-name rewrite left unbalanced.

The rewrite turned `dword(0x8C)` into `dword(offsetof(LaunchingOrderLayout, commonCutCuttingPreference)`, and the closing
`))` lost one paren on the way. This closes them again, and it is written as a script rather than a one-liner because the
count of parens is exactly the thing a shell quoting layer gets wrong.
"""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_exports.cpp"


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = text.split("\n")
    fixed = 0
    for index, line in enumerate(lines):
        if "offsetof(lcns::dll::LaunchingOrderLayout," not in line:
            continue
        # balance the parentheses on this line
        depth = 0
        out = []
        for char in line:
            if char == "(":
                depth += 1
            out.append(char)
        # the statement must end with ';' and the depth must return to zero
        head = "".join(out)
        if depth > 0:
            # insert the missing closers before the trailing ';'
            semi = head.rfind(";")
            if semi < 0:
                continue
            head = head[:semi] + (")" * depth) + head[semi:]
            fixed += 1
        lines[index] = head
    io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("closed %d unbalanced lines" % fixed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
