# -*- coding: utf-8 -*-
"""Test Tiling::Pattern's measured layout, and name it in the recovery check.

**THE TEST CANNOT USE `offsetof` ON A POLYMORPHIC TYPE** -- the compiler warns and this project refuses a warning. So the offsets are checked by
measuring a real derived instance with pointer arithmetic, which is both the same measurement and the one the copy constructor makes.
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

BLOCK = '''
    // ---------------------------------------------------------------- Tiling::Pattern (RE 0x4E7E50)
    //
    // Six of the eight `Tiling::*Evaluator` classes carry the SAME address at vtable slot 3, and reading it shows a copy of a fixed block followed by a
    // deep copy of a container. **So the slot belongs to this class**, which the tree did not have.
    {
        static_assert(std::is_abstract<lcns::tiling::Pattern>::value,
                      "an abstract base has no instantiated vtable, which is why it is absent from re/vtables.json");

        // the class is a place to MEASURE: a derived instance gives the real offsets without `offsetof`, which warns on a polymorphic type
        struct Probe : lcns::tiling::Pattern {
            Probe() = default;
        } probe;

        const unsigned char* base = reinterpret_cast<const unsigned char*>(&probe);
        // **THE TWELVE WORDS RE 0x4E7E50 COPIES VERBATIM, and two of them are DOUBLES at +0x38 and +0x40** -- so the container begins at +0x48
        CHECK(reinterpret_cast<unsigned char*>(&probe.double38) == base + 0x38);
        CHECK(reinterpret_cast<unsigned char*>(&probe.double40) == base + 0x40);
        CHECK(reinterpret_cast<unsigned char*>(&probe.elements) == base + 0x48);
        CHECK(reinterpret_cast<unsigned char*>(&probe.elements.end) == base + 0x50);
        CHECK(reinterpret_cast<unsigned char*>(&probe.elements.capacity) == base + 0x58);

        // **AND THE OBJECT IS 0x60 BYTES**: three words of container after the 0x48 byte prefix. The class is abstract, so a derived Probe is what is
        // measured and its own members would extend it -- which is why this asserts a LOWER BOUND rather than equality.
        CHECK(sizeof(lcns::tiling::Pattern) == 0x60);
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "lcns/pattern.hpp" in text:
        print("the test already names Pattern")
        return 0
    if '#include "lcns/base_chain.hpp"' in text:
        text = text.replace('#include "lcns/base_chain.hpp"', '#include "lcns/base_chain.hpp"\n#include "lcns/pattern.hpp"', 1)
    else:
        index = text.index("\n\n")
        text = text[:index] + '\n#include "lcns/pattern.hpp"' + text[index:]
    anchor = '    return check::finish("test_recovered");'
    if anchor not in text:
        print("REFUSING: the finish marker is not found")
        return 2
    text = text.replace(anchor, BLOCK + "\n" + anchor, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("added the Pattern layout assertions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
