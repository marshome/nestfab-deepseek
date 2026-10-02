# -*- coding: utf-8 -*-
"""Add the class-definitions test, which check_recovery requires and which the generated declarations need."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- every class the RTTI names (generated declarations)
    //
    // The systematic answer to the defect the human found: the repository named classes in prose and declared almost none. This asserts the
    // TABLE's shape and that the declarations exist as types, which is the claim a declaration makes.
    {
        std::size_t count = 0;
        const lcns::ClassFacts* facts = lcns::classFacts(count);
        CHECK(count >= 80u);

        // the namespaces the declarations cover, and how many per namespace
        CHECK(lcns::kDeclaredIn_Multi == 17u);
        CHECK(lcns::kDeclaredIn_Structure == 7u);
        CHECK(lcns::kDeclaredIn_Utils == 5u);
        CHECK(lcns::kDeclaredIn_Prc == 4u);
        CHECK(lcns::kDeclaredIn_Json == 3u);

        // the declarations ARE types: a pointer to each must compile, which is what a declaration claims
        lcns::Multi::FlipNester* flip = nullptr;
        lcns::Multi::FilterNester* filter = nullptr;
        lcns::Multi::NoFillNester* nofill = nullptr;
        lcns::Multi::TilingNester* tiling = nullptr;
        lcns::Multi::DatabaseNester* database = nullptr;
        lcns::Structure::Observer* observer = nullptr;
        lcns::Prc::BoxPriceComputer* price = nullptr;
        lcns::Tiling::BoxMultiTiler* tiler = nullptr;
        CHECK(flip == nullptr && filter == nullptr && nofill == nullptr);
        CHECK(tiling == nullptr && database == nullptr && observer == nullptr);
        CHECK(price == nullptr && tiler == nullptr);

        // a class already defined by hand is flagged, and NOT declared again -- two declarations would be a compile error
        bool sawInfinite = false;
        bool sawCompositeByHand = false;
        for (std::size_t i = 0; i < count; ++i) {
            CHECK(facts[i].vtable >= 0xA00000u);
            CHECK(facts[i].slots >= 3u);
            CHECK(facts[i].firstVirtual >= 0x1000u);
            if (std::string(facts[i].qualified) == "Engine::InfiniteEngine") {
                sawInfinite = true;
                CHECK(facts[i].definedByHand);
                CHECK(facts[i].firstVirtual == 0x759A80u);
                CHECK(facts[i].firstVirtualBytes == 80u);
            }
            if (std::string(facts[i].qualified) == "Engine::CompositeEngine") {
                sawCompositeByHand = true;
                CHECK(facts[i].definedByHand);
                CHECK(facts[i].firstVirtualBytes != 0u);
            }
        }
        CHECK(sawInfinite);
        CHECK(sawCompositeByHand);

        // and no two classes share a vtable, which is what makes the vtables identifiers
        for (std::size_t i = 0; i < count; ++i) {
            for (std::size_t j = i + 1; j < count; ++j) {
                CHECK(facts[i].vtable != facts[j].vtable);
            }
        }
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "classFacts" in text:
        print("already present")
        return 0
    if '#include "lcns/class_definitions.hpp"' not in text:
        anchor = '#include "lcns/engines_composite.hpp"\n'
        assert anchor in text, "the engines_composite include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/class_definitions.hpp"\n', 1)
        print("include added")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("class-definitions test added; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
