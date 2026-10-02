# -*- coding: utf-8 -*-
"""Add a test for StatBox::fold, which check_recovery demands because the class is declared.

The project's own rule: every class declared in include/lcns must be named in a test, or be listed in UNTESTED_OK with a reason.
StatBox is a struct with one member function, so the test is small and it is also the only place the fold's three behaviours are
pinned: an invalid element contributes nothing, the first valid value sets both bounds, and later values move one bound or the
other.
"""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- StatBox::fold (RE 0x5C8C50)
    //
    // The fold's three behaviours, each from an instruction: an element whose flag is zero is skipped (0x5C8C50), the first value
    // that arrives sets both bounds (0x5C8C60's other route), and a later value moves one bound or the other (0x5C8C73 and
    // 0x5C8C88). The class is declared in a header, so check_recovery requires it to be named in a test; the requirement and the
    // behaviour coincide here.
    {
        lcns::StatBox box;
        CHECK(box.valid == 0);
        // an invalid element contributes nothing at all
        box.fold(false, 42.0, box.low0, box.high0);
        CHECK(box.valid == 0);
        CHECK(box.low0 == 0.0 && box.high0 == 0.0);
        // the first valid value sets both bounds
        box.fold(true, 5.0, box.low0, box.high0);
        CHECK(box.valid == 1);
        CHECK(box.low0 == 5.0 && box.high0 == 5.0);
        // a smaller value moves the low bound only
        box.fold(true, 2.0, box.low0, box.high0);
        CHECK(box.low0 == 2.0 && box.high0 == 5.0);
        // a larger one moves the high bound only
        box.fold(true, 9.0, box.low0, box.high0);
        CHECK(box.low0 == 2.0 && box.high0 == 9.0);
        // and one inside the range moves neither
        box.fold(true, 4.0, box.low0, box.high0);
        CHECK(box.low0 == 2.0 && box.high0 == 9.0);
        // the second dimension is independent, which is what the 0x10 interleave at 0x5C8C94 is for
        box.fold(true, -1.0, box.low1, box.high1);
        box.fold(true, 3.0, box.low1, box.high1);
        CHECK(box.low1 == -1.0 && box.high1 == 3.0);
        CHECK(box.low0 == 2.0 && box.high0 == 9.0);      // untouched by the second dimension
        CHECK(lcns::kStatFlag == 0x00);
        CHECK(lcns::kStatMin0 == 0x08 && lcns::kStatMax0 == 0x18);
        CHECK(lcns::kStatMin1 == 0x10 && lcns::kStatMax1 == 0x20);
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "StatBox::fold" in text or "StatBox box" in text:
        print("already present")
        return 0
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the StatBox test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
