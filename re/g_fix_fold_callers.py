# -*- coding: utf-8 -*-
"""Point the two callers of the old fold at foldSingle, which is the one-axis convenience.

RE 0x5C8C50 folds FOUR doubles; the accumulator at 0x526160 folds one measurement per element. The first version of StatBox tried to
serve both with one method and got the four-double routine wrong, so they are now separate names and the callers must say which they mean.
"""
import io
import re

STAT = r"D:\Nesting\nestfab\lcns\include\lcns\stat.hpp"
TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"


def fix_stat():
    text = io.open(STAT, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    old = """    StatBox box;
    for (const Element* element = begin; element != end; ++element) {          // RE 0x5261D4 and 0x5261EE
        if (!accept(element)) {                                                // RE 0x52621E, the predicate on the element
            continue;
        }
        const double value = measure(element);                                 // RE 0x5261DE and 0x5261E9
        box.fold(true, value, box.low0, box.high0);                            // RE 0x5C8C50
    }"""
    new = """    StatBox box;
    bool seen = false;
    for (const Element* element = begin; element != end; ++element) {          // RE 0x5261D4 and 0x5261EE
        if (!accept(element)) {                                                // RE 0x52621E, the predicate on the element
            continue;
        }
        const double value = measure(element);                                 // RE 0x5261DE and 0x5261E9
        box.foldSingle(true, value, seen, box.low0, box.high0);                // one axis, not RE 0x5C8C50's four
    }"""
    if old not in text:
        print("stat.hpp: the statExtent body is not as expected")
        return 1
    text = text.replace(old, new, 1)
    io.open(STAT, "w", encoding="utf-8", newline="\n").write(text)
    print("stat.hpp: statExtent now calls foldSingle")
    return 0


def fix_test():
    lines = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n").split("\n")
    # the fold test block: from the StatBox comment to the variant comment
    start = next(i for i, l in enumerate(lines) if "StatBox::fold (RE 0x5C8C50)" in l)
    end = next(i for i, l in enumerate(lines) if "the variant scale rule (RE 0x132E0)" in l)
    block = '''    // ---------------------------------------------------------------- StatBox::fold (RE 0x5C8C50)
    //
    // READ FROM THE WHOLE 255 BYTE BODY. The element is FOUR doubles and the box's flag means BUILD ME rather than I am valid:
    //
    //     element flag zero  -> return untouched           (0x5C8C50)
    //     box flag NONZERO   -> install a and b into all four slots, clear the flag, then compare c and d  (0x5C8D10)
    //     box flag ZERO      -> compare a, b, c and d      (0x5C8C69)
    //
    // Three earlier attempts read a fragment and got the polarity and the arity wrong; they are recorded in re/blockers.json.
    {
        // the build path: a and b set both ends of both axes, the flag clears, and c and d are then compared
        lcns::StatBox fresh;
        fresh.valid = 1;                                   // BUILD ME
        fresh.low0 = 100.0; fresh.high0 = 200.0;
        fresh.low1 = 300.0; fresh.high1 = 400.0;
        fresh.fold(true, 11.0, 22.0, 5.0, 40.0);
        CHECK(fresh.valid == 0);                           // RE 0x5C8D14
        CHECK(fresh.low0 == 5.0);                          // a=11 set it, then c=5 lowered it
        CHECK(fresh.high0 == 11.0);                        // and a is still the high, because c did not exceed it
        CHECK(fresh.low1 == 22.0);                         // b=22 set it, then d=40 raised the high instead
        CHECK(fresh.high1 == 40.0);

        // the compare path: all four values meet the box
        lcns::StatBox box;
        box.fold(true, 5.0, 7.0, 9.0, 4.0);
        CHECK(box.valid == 0);                             // untouched: the compare path never sets it
        CHECK(box.low0 == 5.0 && box.high0 == 9.0);        // a=5 lowered nothing, c=9 raised the high
        CHECK(box.low1 == 4.0 && box.high1 == 7.0);        // b=7 set the high, d=4 lowered the low

        // an element with a zero flag contributes nothing at all, which is the routine's first three instructions
        lcns::StatBox untouched;
        untouched.fold(false, 42.0, 42.0, 42.0, 42.0);
        CHECK(untouched.low0 == 0.0 && untouched.high0 == 0.0);
        CHECK(untouched.low1 == 0.0 && untouched.high1 == 0.0);
        CHECK(untouched.valid == 0);

        // and a build followed by a compare: the second call takes the compare path because the flag was cleared
        lcns::StatBox built;
        built.valid = 1;
        built.fold(true, 1.0, 2.0, 1.0, 2.0);
        CHECK(built.low0 == 1.0 && built.high0 == 1.0);
        CHECK(built.low1 == 2.0 && built.high1 == 2.0);
        built.fold(true, 0.0, 0.0, 3.0, 3.0);
        CHECK(built.low0 == 0.0 && built.high0 == 3.0);
        CHECK(built.low1 == 0.0 && built.high1 == 3.0);

        CHECK(lcns::kStatFlag == 0x00);
        CHECK(lcns::kStatMin0 == 0x08 && lcns::kStatMax0 == 0x18);
        CHECK(lcns::kStatMin1 == 0x10 && lcns::kStatMax1 == 0x20);
    }

'''
    out = lines[:start] + block.split("\n") + lines[end:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("test_recovered.cpp: the fold test rewritten for four doubles and the build path")
    return 0


if __name__ == "__main__":
    raise SystemExit(max(fix_stat(), fix_test()))
