# -*- coding: utf-8 -*-
"""Add the config-parameters test, which check_recovery requires for a newly declared name."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- the engine's config parameters (RE 0x4EC00)
    //
    // RE 0x4EC00 fills an object in rsi by asking 0x82A3E0 for a parameter BY NAME and storing the value when the lookup succeeds, so
    // each entry is a name from the module's own strings beside the instruction that writes it. The assertions below are about the
    // TABLE: that the count agrees with the generated constant, and that the named offsets are the ones the generator recorded.
    {
        std::size_t count = 0;
        const lcns::ConfigParameter* table = lcns::configParameters(count);
        CHECK(count == lcns::config::kConfigParameterCount);
        CHECK(count == 59u);

        // the one site verified by hand: nesting_pow_boost at +0x100
        CHECK(lcns::config::knesting_pow_boost == 0x100);
        CHECK(lcns::config::knesting_max_context_size == 0x108);
        // and a few from the same run, chosen because their names state their role
        CHECK(lcns::config::knb_strips_first == 0x44);
        CHECK(lcns::config::knb_max_threads == 0x344);
        CHECK(lcns::config::kseed == 0x33C);
        CHECK(lcns::config::kcombined_price_frequency == 0x210);
        CHECK(lcns::config::kbeam_width == 0x150);

        // the table and the constants must agree, which is the check that the generated header is self-consistent
        bool found = false;
        for (std::size_t i = 0; i < count; ++i) {
            if (std::string(table[i].name) == "nesting_pow_boost") {
                CHECK(table[i].offset == lcns::config::knesting_pow_boost);
                found = true;
            }
        }
        CHECK(found);

        // the offsets are ascending, which is what a sorted generator produces and what a reader relies on
        for (std::size_t i = 1; i < count; ++i) {
            CHECK(table[i].offset > table[i - 1].offset);
        }
        // and they all fall inside the largest offset the parser writes
        CHECK(table[count - 1].offset == 0x344);
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "configParameters" in text:
        print("already present")
        return 0
    if '#include "lcns/config_parameters.hpp"' not in text:
        anchor = '#include "lcns/module_switch.hpp"\n'
        assert anchor in text, "the module_switch include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/config_parameters.hpp"\n', 1)
        print("added the include")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the config test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
