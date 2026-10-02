# -*- coding: utf-8 -*-
"""Add the MIPLIB names test, which check_recovery requires for a newly declared name."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

TEST = '''
    // ---------------------------------------------------------------- the benchmark names (RE 0x2A3520)
    //
    // 49 MIPLIB instance names that one function loads, found by following the option lookup's call sites and keeping the strings that
    // are NOT stored into a field. The findings archive reached the same function by reading rodata and declined to name it, which this
    // test respects: it asserts the EVIDENCE and the one conclusion the evidence supports.
    {
        std::size_t count = 0;
        const char* const* names = lcns::benchmarkInstanceNames(count);
        CHECK(count == 49u);

        // the seven the archive and the extraction both found
        const char* shared[7] = {"exmip1", "p0033", "flugpl", "enigma", "mod011", "probing", "mas76"};
        for (const char* wanted : shared) {
            bool found = false;
            for (std::size_t i = 0; i < count; ++i) {
                if (std::string(names[i]) == wanted) {
                    found = true;
                }
            }
            CHECK(found);
        }

        // the loader, and that the control strings are not in the list
        CHECK(lcns::kBenchmarkLoader == 0x2A3520);
        for (std::size_t i = 0; i < count; ++i) {
            CHECK(std::string(names[i]) != lcns::kBenchmarkFalse);
            CHECK(std::string(names[i]) != lcns::kBenchmarkPlain);
            CHECK(std::string(names[i]).size() >= 4u);
        }

        // and none of them is an option key, which is the distinction the split made
        std::size_t options = 0;
        const lcns::OptionKey* keys = lcns::optionKeys(options);
        for (std::size_t i = 0; i < count; ++i) {
            for (std::size_t k = 0; k < options; ++k) {
                CHECK(std::string(names[i]) != keys[k].name);
            }
        }
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "benchmarkInstanceNames" in text:
        print("already present")
        return 0
    if '#include "lcns/miplib_names.hpp"' not in text:
        anchor = '#include "lcns/option_keys.hpp"\n'
        assert anchor in text, "the option_keys include is gone"
        text = text.replace(anchor, anchor + '#include "lcns/miplib_names.hpp"\n', 1)
        print("added the include")
    marker = '    return check::finish("test_recovered");'
    assert marker in text, "the finish marker is gone"
    text = text.replace(marker, TEST + "\n" + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("added the benchmark test; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
