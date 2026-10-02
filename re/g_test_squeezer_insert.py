# -*- coding: utf-8 -*-
"""Test Squeezer::insert against the two keys RE 0x13A360 walks with, and the update-in-place its walk implies.

`insert` had a declaration and no definition, so it was dead. **A METHOD WITH NO TEST IS A METHOD WHOSE BEHAVIOUR NOTHING STATES**, and the reason
to test it here is specific: 0x13A360 walks a tree comparing the LOWER key at 0x13A394 before the UPPER key at 0x13A399, and it updates the node it
found rather than adding a second -- so the observable behaviour is that two inserts with the same pair leave ONE entry.
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_row.cpp"

BLOCK = '''
    // --- Squeezer::insert, RE 0x13A360 ---
    //
    // The routine walks the lookup tree at impl + 0x250 and inserts into the one at impl + 0x240, comparing the LOWER key first
    // (0x13A394) and the upper one second (0x13A399). So the pair (lo, hi) IS the identity of an entry, and a second insert with the same pair
    // updates rather than adds -- which is what the walk's found-branch does.
    {
        Squeezer sq;
        CHECK(sq.size() == 0);

        sq.insert(0x2000, 0x2100, 5.0);          // RE 0x13A3EB: the insert into the tree at +0x240
        CHECK(sq.size() == 1);

        // the same pair again: the module found the node and updates it, so the count stays at one
        sq.insert(0x2000, 0x2100, 7.0);
        CHECK(sq.size() == 1);

        // A DIFFERENT LOWER KEY IS A DIFFERENT NODE, because 0x13A394 compares it FIRST
        sq.insert(0x2001, 0x2100, 9.0);
        CHECK(sq.size() == 2);

        // and a different upper key with the same lower one also has to be a different node, because 0x13A399 compares the second too. **IF
        // ONLY THE LOWER KEY WERE THE IDENTITY, THIS WOULD UPDATE THE FIRST ENTRY INSTEAD OF ADDING**, so the count is what distinguishes the
        // two readings of the walk.
        sq.insert(0x2000, 0x2101, 11.0);
        CHECK(sq.size() == 3);

        sq.clear();
        CHECK(sq.size() == 0);
        CHECK(sq.hits() == 0);
        CHECK(sq.misses() == 0);
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "Squeezer::insert, RE 0x13A360" in text:
        print("the insert test is already present")
        return 0
    # insert before the file's final closing brace of main
    marker = '    return check::finish("test_row");'
    if marker not in text:
        print("REFUSING: the finish marker is not found")
        return 2
    text = text.replace(marker, BLOCK + "\n" + marker, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("added the insert test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
