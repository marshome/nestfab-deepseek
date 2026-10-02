# -*- coding: utf-8 -*-
"""Correct the BestObserver size assertion: the class has a VTABLE as well as the pointer.

**THE OLD ASSERTION WAS `sizeof(BestObserver) == sizeof(void*)` AND IT WAS A STATEMENT ABOUT THE OLD MODEL.** That model had `BestObserver` as a
class with one member and no base, inferred from the three forwarders reading `[rcx + 0x10]`.

**THE MODULE'S TYPEINFO SAYS OTHERWISE**: `N6Engine12BestObserverE -> N9Structure8ObserverE`, so it has a base, so it has its own vtable pointer at
+0, and `sink_` at +0x10 -- **which is exactly why the forwarders read +0x10 and not +8**: the first eight bytes are the base's vptr.

**SO THE ASSERTION BECOMES THE ONE THAT ACTUALLY DISCRIMINATES**: sixteen, not eight. A class with a base and one member is two words, and if the
declaration ever lost its base the test would fail rather than pass quietly.
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD = """        static_assert(std::is_abstract<lcns::Structure_Observer>::value, "a pure interface");
        CHECK(sizeof(lcns::BestObserver) == sizeof(void*));      // RE 0x755A40: the class holds ONE pointer, at +0x10"""

NEW = """        static_assert(std::is_abstract<lcns::Structure_Observer>::value, "a pure interface");

        // **SIXTEEN, NOT EIGHT.** The class has a BASE -- `N6Engine12BestObserverE -> N9Structure8ObserverE` -- so it carries its own vtable pointer
        // at +0 and `sink_` at +0x10. **THAT IS WHY THE FORWARDERS READ +0x10 AND NOT +8**: the first eight bytes are the base's vptr, and an
        // earlier assertion of `sizeof(void*)` was a statement about a model that had no base at all.
        CHECK(sizeof(lcns::BestObserver) == 2 * sizeof(void*));
        static_assert(std::is_base_of<lcns::Structure_Observer, lcns::BestObserver>::value,
                      "the module's typeinfo chain says so");"""


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD not in text:
        print("REFUSING: the assertion is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("the size assertion now requires TWO words and names the base")
    return 0


if __name__ == "__main__":
    sys.exit(main())
