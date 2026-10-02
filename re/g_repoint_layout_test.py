# -*- coding: utf-8 -*-
"""Repoint the class test at NestingNesterLayout, which states the module's offsets without a base class shifting them."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

PAIRS = [
    ("using lcns::Multi::NestingNester;", "using lcns::Multi::NestingNesterLayout;"),
    ("NestingNester nester{};", "NestingNesterLayout nester{};"),
    ("NestingNester seeded{};", "NestingNesterLayout seeded{};"),
    ("offsetof(NestingNester,", "offsetof(NestingNesterLayout,"),
    ("lcns::Multi::NestingNester* nesterPtr", "lcns::Multi::NestingNesterLayout* nesterPtr"),
    ("const lcns::Multi::NestingNester", "const lcns::Multi::NestingNesterLayout"),
]


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    for old, new in PAIRS:
        if old in text:
            text = text.replace(old, new)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("repointed to NestingNesterLayout; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
