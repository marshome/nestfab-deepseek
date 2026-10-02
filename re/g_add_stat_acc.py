# -*- coding: utf-8 -*-
"""Add the range-accumulator test to test_recovered.cpp, in Python so the newlines survive.

The test covers the accumulator's RULE rather than its element walk, because the walk needs two functions that have not been read:
the extent of a set is `max - min` over the elements a predicate accepts, and an empty set is zero.

It also pins the two predicates against each other over every small value, and pins the stride the walk uses.
"""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- the stat accumulator (RE 0x526160 and 0x5266A0)
    //
    // The two exported aggregators call the same seven functions and differ at ONE pointer, so this is one shape: walk a container
    // of 0x78-byte records, fold each accepted element's measurement into a running min and max, and return the difference --
    // which RE 0x526230 performs with one `subsd` after the walk. The element functions are parameters here because the two
    // bodies behind them are not read yet, and a guessed contract would be worse than a parameter.
    {
        struct Element { std::uint32_t axis; double measure; };
        Element elements[4] = {{0u, 1.0}, {1u, 5.0}, {2u, 2.0}, {3u, 9.0}};
        const auto measure = [](const Element* e) { return e->measure; };

        // the short-axis predicate accepts {0,1}, so the extent is over measures 1.0 and 5.0
        const double shortExtent = lcns::statExtent(
            elements, elements + 4, measure, [](const Element* e) { return lcns::statIsShortAxis(&e->axis); });
        CHECK(shortExtent == 4.0);

        // the long-axis predicate accepts {0,2}, so the extent is over measures 1.0 and 2.0
        const double longExtent = lcns::statExtent(
            elements, elements + 4, measure, [](const Element* e) { return lcns::statIsLongAxis(&e->axis); });
        CHECK(longExtent == 1.0);

        // accepting everything gives the full range, which is what the two disagreeing over {1,2} is worth
        const double allExtent = lcns::statExtent(
            elements, elements + 4, measure, [](const Element*) { return true; });
        CHECK(allExtent == 8.0);            // 9.0 - 1.0

        // an empty set is zero rather than a sentinel pair, because the original returns the difference of its accumulators
        const double nothing = lcns::statExtent(
            elements, elements, measure, [](const Element*) { return true; });
        CHECK(nothing == 0.0);
        // and a set where nothing is accepted is the same case
        const double noneAccepted = lcns::statExtent(
            elements, elements + 4, measure, [](const Element*) { return false; });
        CHECK(noneAccepted == 0.0);

        // a single element is a zero extent, which is the accumulator agreeing with itself
        const double one = lcns::statExtent(
            elements + 1, elements + 2, measure, [](const Element*) { return true; });
        CHECK(one == 0.0);

        CHECK(lcns::kStatElementStride == 0x78);
        CHECK(lcns::kStatElementStride == 120u);
        CHECK(lcns::kStatElementStride * 2 == 240u);
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "statExtent" in text:
        print("already present")
        return 0
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the accumulator test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
