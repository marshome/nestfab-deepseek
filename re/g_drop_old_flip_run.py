# -*- coding: utf-8 -*-
"""Remove the OLD FlipNester::run from nester.cpp, now that flip_nester.cpp carries the class's own implementation.

Two definitions of one method is a link error, and the old one was written from a guess: it took a `double ratio_` and called NestingNester,
neither of which the module's FlipNester does.
"""
import io
import re
import sys

SRC = r"D:\Nesting\nestfab\lcns\src\nester.cpp"


def main():
    text = io.open(SRC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find("Solution FlipNester::run(SolveContext& ctx) {")
    if start < 0:
        print("no FlipNester::run found; nothing to remove")
        return 0
    # the brace block that follows
    index = text.find("{", start)
    depth = 0
    while index < len(text):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                break
        index += 1
    end = index + 1
    while end < len(text) and text[end] in "\r\n":
        end += 1
    removed = text[start:end]
    text = text[:start] + ("// FlipNester::run now lives in lcns/src/flip_nester.cpp, next to the constructor's instructions. The version that\n"
                           "// stood here took a `double ratio_` and delegated to NestingNester, neither of which the module's FlipNester does.\n\n") + text[end:]
    io.open(SRC, "w", encoding="utf-8", newline="\n").write(text)
    print("removed %d characters of the old FlipNester::run" % len(removed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
