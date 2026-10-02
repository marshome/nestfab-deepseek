# -*- coding: utf-8 -*-
"""Add the classes test, which check_recovery requires and which the generated table needs."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- the module's own classes (from its RTTI)
    //
    // 96 classes with their vtable addresses and slot counts, generated from re/vtables.json. The assertions are about the HIERARCHY:
    // that the count agrees, that the namespaces are the ones the module uses, and that the addresses are distinct.
    {
        std::size_t count = 0;
        const lcns::ClassInfo* table = lcns::moduleClasses(count);
        CHECK(count == 96u);

        // the namespaces, which are the module's shape
        CHECK(lcns::kClassesIn_Multi == 30u);        // the strategy/nester family
        CHECK(lcns::kClassesIn_Tiling == 17u);
        CHECK(lcns::kClassesIn_Engine == 10u);
        CHECK(lcns::kClassesIn_Structure == 7u);
        CHECK(lcns::kClassesIn_Prc == 4u);
        CHECK(lcns::kClassesIn_Pack == 3u);

        // InfiniteEngine is in the table, which is what the human's question was about
        bool sawInfinite = false;
        bool sawNesting = false;
        for (std::size_t i = 0; i < count; ++i) {
            if (std::string(table[i].qualified) == "Engine::InfiniteEngine") {
                sawInfinite = true;
                CHECK(table[i].vtable == 0xA3CFD0u);
            }
            if (std::string(table[i].qualified) == "Engine::NestingEngine") {
                sawNesting = true;
            }
            // every entry carries its mangled name, which is the primary evidence and not a decode
            CHECK(table[i].mangled != nullptr);
            CHECK(std::string(table[i].mangled).size() > 4u);
            CHECK(table[i].qualified != nullptr);
            CHECK(table[i].vtable >= 0xA00000u);      // all vtables are in the module's data range
            CHECK(table[i].slots >= 1u);
        }
        CHECK(sawInfinite);
        CHECK(sawNesting);

        // the vtables are distinct, which is what makes them identifiers
        for (std::size_t i = 0; i < count; ++i) {
            for (std::size_t j = i + 1; j < count; ++j) {
                CHECK(table[i].vtable != table[j].vtable);
            }
        }
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "moduleClasses" in text:
        print("already present")
        return 0
    if '#include "lcns/classes.hpp"' not in text:
        anchor = '#include "lcns/engines.hpp"\n'
        assert anchor in text, "the engines include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/classes.hpp"\n', 1)
        print("added the include")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the classes test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
