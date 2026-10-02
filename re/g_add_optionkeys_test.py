# -*- coding: utf-8 -*-
"""Add the option-keys test, which check_recovery requires for a newly declared name."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- the option keys (RE 0x82A3E0's call sites)
    //
    // The names the engine looks up and whose results reach a field. The assertions are about the TABLE: the count, the names known by
    // hand, and the invariant that a name is looked up at least as often as it is stored.
    {
        std::size_t count = 0;
        const lcns::OptionKey* table = lcns::optionKeys(count);
        CHECK(count == lcns::kOptionKeyCount);
        CHECK(count == 108u);
        CHECK(lcns::kOptionKeysConfirmedTwice == 54u);
        CHECK(lcns::kOptionKeysConfirmedTwice < lcns::kOptionKeyCount);

        // the two names verified by hand: one from the store test and one from the archive's rodata table
        bool sawPowBoost = false;
        bool sawBeamWidth = false;
        for (std::size_t i = 0; i < count; ++i) {
            CHECK(table[i].stores > 0);            // every entry is here BECAUSE a store confirmed it
            CHECK(table[i].lookups >= table[i].stores);
            if (std::string(table[i].name) == "nesting_pow_boost") {
                CHECK(table[i].stores >= 1u);
                sawPowBoost = true;
            }
            if (std::string(table[i].name) == "beam_width") {
                sawBeamWidth = true;
            }
        }
        CHECK(sawPowBoost);
        CHECK(sawBeamWidth);

        // and the data-looking strings are NOT in the table, which is the whole point of the store test
        for (std::size_t i = 0; i < count; ++i) {
            CHECK(std::string(table[i].name) != "air03");
            CHECK(std::string(table[i].name) != "bell3a");
            CHECK(std::string(table[i].name) != "egout");
        }
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "optionKeys" in text:
        print("already present")
        return 0
    if '#include "lcns/option_keys.hpp"' not in text:
        anchor = '#include "lcns/engine_defaults.hpp"\n'
        assert anchor in text, "the engine_defaults include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/option_keys.hpp"\n', 1)
        print("added the include")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the option-keys test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
