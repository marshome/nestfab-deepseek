# -*- coding: utf-8 -*-
"""Update the exports test: 45 to 47, and ordinals 200 and 202 in the predicate."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_exports.cpp"

OLD_COUNT = "        CHECK(ex::forwardedCount() == 45u);"
NEW_COUNT = "        CHECK(ex::forwardedCount() == 47u);"

OLD_TAIL = "                                  e->ordinal0 == 196 || e->ordinal0 == 198;"
NEW_TAIL = ("                                  e->ordinal0 == 196 || e->ordinal0 == 198 ||\n"
            "                                  // round 598: two more of the variant family, whose targets 0x14A60 and 0xC1A0 are read.\n"
            "                                  // Ordinal 204 is deliberately NOT here: its target 0x10CE0 has only its head read, and a\n"
            "                                  // forwarding entry claims agreement with the assembly.\n"
            "                                  e->ordinal0 == 200 || e->ordinal0 == 202;")


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
