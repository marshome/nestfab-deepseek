# -*- coding: utf-8 -*-
"""Update the exports test for the two variant ordinals: 43 to 45, and the predicate extended.

The test is the project's own guard: it asserts the exact count and that forwards() agrees with the table for every entry, so
adding two entries fails until the test says so. That is the behaviour wanted, and this is the edit.
"""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_exports.cpp"

OLD_COUNT = "        CHECK(ex::forwardedCount() == 43u);"
NEW_COUNT = "        CHECK(ex::forwardedCount() == 45u);"

OLD_TAIL = "                                  e->ordinal0 == 88 || e->ordinal0 == 90 || e->ordinal0 == 92;"
NEW_TAIL = ("                                  e->ordinal0 == 88 || e->ordinal0 == 90 || e->ordinal0 == 92 ||\n"
            "                                  // round 593: the two variant wrappers, which share the tail target 0x132E0 and\n"
            "                                  // whose every callee on the path is now read\n"
            "                                  e->ordinal0 == 196 || e->ordinal0 == 198;")


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    changed = 0
    if OLD_COUNT in text:
        text = text.replace(OLD_COUNT, NEW_COUNT, 1)
        changed += 1
    if OLD_TAIL in text:
        text = text.replace(OLD_TAIL, NEW_TAIL, 1)
        changed += 1
    if changed:
        io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("updated %d site(s)" % changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
