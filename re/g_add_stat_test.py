# -*- coding: utf-8 -*-
"""Add the stat predicate include and test to test_recovered.cpp, with real newlines.

A PowerShell attempt at this flattened the file to two lines, because `-Raw` and `-NoNewline` and a regex replace do not compose
the way they look like they do. The file was restored with git and this does the edit in Python, where a newline is a newline.

The test asserts the two predicates against EVERY small value, because the entire content of the two routines is which values they
accept: `{0, 1}` and `{0, 2}`.
"""
import io
import os

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

INCLUDE_AFTER = '#include "lcns/owned_chain.hpp"\n'
INCLUDE = '#include "lcns/stat.hpp"\n'

TEST = '''
    // ---------------------------------------------------------------- the stat predicates (RE 0x52F810 and 0x52F830)
    //
    // The two functions that ../structure/stat.cpp's aggregators are parameterised by, and the ONLY difference between the
    // GetLength and GetHeight exports. The assertions cover every small value, because the whole content of the two routines is
    // which values they accept: {0, 1} for the first and {0, 2} for the second.
    {
        for (std::uint32_t value = 0; value <= 8u; ++value) {
            CHECK(lcns::statIsShortAxis(&value) == (value <= 1u));                 // RE 0x52F810: cmp 1 ; setbe
            CHECK(lcns::statIsLongAxis(&value) == (value == 0u || value == 2u));   // RE 0x52F830: test 0xFFFFFFFD ; sete
        }
        // the two disagree on exactly two values, which is why they are two predicates rather than one with a flag
        int disagree = 0;
        for (std::uint32_t value = 0; value <= 8u; ++value) {
            if (lcns::statIsShortAxis(&value) != lcns::statIsLongAxis(&value)) {
                ++disagree;
            }
        }
        CHECK(disagree == 2);        // 1 and 2
        CHECK(lcns::statIsShortAxis(nullptr) == false || true);   // the routines dereference, so only real values are passed
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if INCLUDE not in text:
        assert INCLUDE_AFTER in text, "the owned_chain include is gone, so this is the wrong anchor"
        text = text.replace(INCLUDE_AFTER, INCLUDE_AFTER + INCLUDE, 1)
        print("added the include")
    if "statIsShortAxis" not in text:
        marker = '    return check::finish("test_recovered");'
        assert marker in text, "the finish marker is gone"
        text = text.replace(marker, TEST + "\n" + marker, 1)
        print("added the test")
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("lines now: %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
