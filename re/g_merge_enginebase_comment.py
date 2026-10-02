# -*- coding: utf-8 -*-
"""Merge the two comments on EngineBase into one, with the byte counts MEASURED.

**TWO COMMENTS ABOUT ONE CLASS IS THE DUPLICATION THIS PROJECT CHECKS FOR**, and I created the second one by inserting a note above a class that
already had a doc comment. And the note's ranges were wrong: it said "70 to 137 bytes" for slot 0, which is right, and gave no range for slot 1 while
calling the slot-1 addresses a byte range. The measured values are

    Engine           slot 0   slot 1   slot 2
    CloudEngine         70       71    15430
    MultiEngine         90      100     2329
    DelayedEngine       71       76      750
    NestingEngine       98       94     1975
    InfiniteEngine      71       76       80
    CompositeEngine    137      129     8230
    EquivalentEngine   126      123     3569

so the ranges are 70..137, 71..129 and 80..15430.
"""
import io
import sys

ENGINES = r"D:\Nesting\nestfab\lcns\include\lcns\engines.hpp"

OLD_TAIL = """ * The result is returned as a POINTER rather than by value because the caller passes a buffer and the slot hands it back -- and because
 * the recovered `Run`s end with `mov rax, rbx` where rbx is that buffer.
 */
/** **RE the seven tables below: ONE VIRTUAL, AND IT IS `run`.** Every concrete engine has exactly three slots --
 *
 *      0x755000..0x75CB40   the deleting destructor, 70 to 137 bytes
 *      0x754FB0..0x75CAC0   the destructor
 *      slot 2, DIFFERENT IN ALL SEVEN   `run`, 80 bytes for `InfiniteEngine` and 15430 for `CloudEngine`
 *
 *  -- so **the base's surface is that one method**, and the class is abstract because every derived class implements it. There is no vtable for
 *  `Engine::Engine` ITSELF in re/vtables.json because an abstract base has no instantiated table, which is the same reason the whole base layer was
 *  missing from this tree. **`Engine::InfiniteEngine`'s own constructor is NOT in the profile either** -- the three functions that install its
 *  vtable pointer are its two destructors and another class's constructor, recorded in the ledger. */
"""

NEW_TAIL = """ * The result is returned as a POINTER rather than by value because the caller passes a buffer and the slot hands it back -- and because
 * the recovered `Run`s end with `mov rax, rbx` where rbx is that buffer.
 *
 * **AND THE SEVEN TABLES MEASURE THE BASE'S SURFACE: ONE VIRTUAL, AND IT IS `run`.** Every concrete engine has exactly three slots --
 *
 *      slot 0   70 to 137 bytes     the deleting destructor
 *      slot 1   71 to 129 bytes     the destructor
 *      slot 2   80 to 15430 bytes   `run`, and its ADDRESS DIFFERS IN ALL SEVEN
 *
 * -- and those counts are MEASURED rather than estimated: `CloudEngine` is 70, 71 and 15430, `InfiniteEngine` is 71, 76 and 80, and
 * `CompositeEngine` is 137, 129 and 8230. **So the base's whole surface is that one method**, and it is abstract because every derived class
 * implements it. There is no vtable for `Engine::Engine` ITSELF in re/vtables.json because an abstract base has no instantiated table, which is the
 * same reason the whole base layer was missing from this tree.
 */"""

# the version g_annotate_engines.py actually wrote, in case the ranges differ by whitespace
import re

pattern = re.compile(
    r" \* The result is returned as a POINTER rather than by value because the caller passes a buffer and the slot hands it back -- and because\n"
    r" \* the recovered `Run`s end with `mov rax, rbx` where rbx is that buffer\.\n"
    r" \*/\n"
    r"/\*\* \*\*RE the seven tables below.*?\*/\n", re.S)


def main():
    text = io.open(ENGINES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD_TAIL in text:
        text = text.replace(OLD_TAIL, NEW_TAIL, 1)
        print("merged the two comments using the exact text")
    else:
        match = pattern.search(text)
        if not match:
            print("REFUSING: neither form of the double comment is present")
            return 2
        text = text[:match.start()] + NEW_TAIL + "\n" + text[match.end():]
        print("merged the two comments by pattern")
    io.open(ENGINES, "w", encoding="utf-8", newline="\n").write(text)
    # and count the comments left on EngineBase, so the merge is verified rather than assumed
    index = text.find("class EngineBase")
    comments = text.count("/**", max(0, index - 3000), index)
    print("EngineBase now has %d doc comment(s) above it" % comments)
    return 0


if __name__ == "__main__":
    sys.exit(main())
