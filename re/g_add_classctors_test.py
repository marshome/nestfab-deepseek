# -*- coding: utf-8 -*-
"""Add the class-constructors test, which check_recovery requires and which the generated table needs."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
ANCHOR = '    return check::finish("test_recovered");'

BLOCK = '''
    // ---------------------------------------------------------------- every class's constructor (generated)
    //
    // A constructor is found by the vtable slot-0 ADDRESS it installs, and a field by a store through a register shown to hold the object.
    // The count is of DISTINCT OFFSETS, so Multi::NestingNester's two writes at 0x30 make one position.
    {
        std::size_t count = 0;
        const lcns::ClassConstructor* ctors = lcns::classConstructors(count);
        CHECK(count == lcns::kClassesWithConstructor);
        CHECK(count >= 90u);
        CHECK(lcns::kClassesWritingFields >= 80u);
        CHECK(lcns::kClassesWritingFields <= count);

        // every row has a vtable in the data range, and a constructor either in the code range or absent
        std::size_t withCtor = 0;
        std::size_t writing = 0;
        for (std::size_t i = 0; i < count; ++i) {
            CHECK(ctors[i].qualified != nullptr);
            CHECK(ctors[i].vtable >= 0xA00000u);
            CHECK(ctors[i].candidates >= 1u);
            CHECK(ctors[i].functionsWriting <= ctors[i].candidates);
            if (ctors[i].constructor != 0u) {
                ++withCtor;
                CHECK(ctors[i].constructor >= 0x1000u);
                CHECK(ctors[i].constructor < 0x9C0000u);
            }
            if (ctors[i].fields > 0u) {
                ++writing;
            }
        }
        CHECK(writing == lcns::kClassesWritingFields);
        CHECK(withCtor >= 90u);

        // THE TWO CLASSES THE COVERAGE CHECK FOUND NAMED AND UNDECLARED now have constructors, which is what this round was for
        bool sawSplit = false, sawTerminal = false;
        for (std::size_t i = 0; i < count; ++i) {
            if (std::string(ctors[i].qualified) == "Multi::SplitNode") {
                sawSplit = true;
                CHECK(ctors[i].constructor == 0x99910u);
                CHECK(ctors[i].fields == 11u);
            }
            if (std::string(ctors[i].qualified) == "Multi::TerminalNode") {
                sawTerminal = true;
                CHECK(ctors[i].constructor == 0x99360u);
                CHECK(ctors[i].fields == 10u);
            }
        }
        CHECK(sawSplit);
        CHECK(sawTerminal);

        // the class a previous round measured by hand, whose two writes at 0x30 make one position
        bool sawNesting = false;
        for (std::size_t i = 0; i < count; ++i) {
            if (std::string(ctors[i].qualified) == "Multi::NestingNester") {
                sawNesting = true;
                CHECK(ctors[i].constructor == 0x342E0u);
                CHECK(ctors[i].fields == 7u);      // seven positions from eight stores
            }
        }
        CHECK(sawNesting);

        // and the class with the most, which is the richest layout the scan found
        const lcns::ClassConstructor* richest = &ctors[0];
        for (std::size_t i = 1; i < count; ++i) {
            if (ctors[i].fields > richest->fields) {
                richest = &ctors[i];
            }
        }
        CHECK(richest->fields >= 30u);
        CHECK(std::string(richest->qualified) == "Tiling::SqueezeMultiTiler");
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    changed = False
    if "classConstructors" not in text:
        text = text.replace(ANCHOR, BLOCK + "\n" + ANCHOR, 1)
        changed = True
        print("added the class-constructors test")
    include = '#include "lcns/class_constructors.hpp"\n'
    if include not in text:
        anchor = '#include "lcns/nesting_nester_fields.hpp"\n'
        assert anchor in text, "the nesting_nester_fields include is gone"
        text = text.replace(anchor, anchor + include, 1)
        changed = True
        print("added the include")
    if changed:
        io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
