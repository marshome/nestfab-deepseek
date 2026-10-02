# -*- coding: utf-8 -*-
"""Add the engine-defaults test, which check_recovery requires for a newly declared name."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- the engine defaults (RE 0x4E5B0)
    //
    // The initialiser of the object 0x4EC00 then fills by name. Every value is the immediate of its instruction or the double its movsd
    // loads, so the assertions below are about the TABLE and its sites rather than about a reconstructed struct.
    {
        std::size_t count = 0;
        const lcns::EngineDefault* table = lcns::engineDefaults(count);
        CHECK(count == 17u);

        // the five doubles, each with the site that loads it
        CHECK(lcns::kDefaultSmallRatio == 0.0001);
        CHECK(lcns::kDefaultTinyRatio == 0.001);
        CHECK(lcns::kDefaultTenthRatio == 0.1);
        CHECK(lcns::kDefaultHundredthRatio == 0.01);
        CHECK(lcns::kDefaultHalfRatio == 0.5);

        // and the two dwords worth naming: 30 and the 15 at +0x350
        bool sawThirty = false;
        bool sawFifteen = false;
        bool sawFlag = false;
        for (std::size_t i = 0; i < count; ++i) {
            if (table[i].offset == 0x24 && table[i].kind == lcns::EngineDefault::Kind::Dword) {
                CHECK(table[i].value == 30.0);
                CHECK(table[i].site == 0x4E629);
                sawThirty = true;
            }
            if (table[i].offset == 0x350) {
                CHECK(table[i].value == 15.0);
                CHECK(table[i].site == 0x4E5F4);
                sawFifteen = true;
            }
            if (table[i].offset == 0x00) {
                CHECK(table[i].value == 1.0);
                CHECK(table[i].kind == lcns::EngineDefault::Kind::Byte);
                sawFlag = true;
            }
        }
        CHECK(sawThirty);
        CHECK(sawFifteen);
        CHECK(sawFlag);

        // the offsets ascend, which is what a sorted table gives a reader
        for (std::size_t i = 1; i < count; ++i) {
            CHECK(table[i].offset > table[i - 1].offset);
        }
        // and every site is inside the initialiser
        for (std::size_t i = 0; i < count; ++i) {
            CHECK(table[i].site >= 0x4E5B0u);
            CHECK(table[i].site < 0x4E5B0u + 1574u);
        }
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "engineDefaults" in text:
        print("already present")
        return 0
    if '#include "lcns/engine_defaults.hpp"' not in text:
        anchor = '#include "lcns/parameter_report.hpp"\n'
        assert anchor in text, "the parameter_report include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/engine_defaults.hpp"\n', 1)
        print("added the include")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the engine-defaults test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
