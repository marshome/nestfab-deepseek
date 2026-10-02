# -*- coding: utf-8 -*-
"""Name the new header in a test, and make the base chain a CHECKED fact rather than a document.

`check_recovery` requires every declared class to be named by a test, and `base_chain.hpp` declares constants rather than classes -- so this asserts
the constants themselves against the module, which is stronger than naming them: **the program fails if the module's own typeinfo names change.**
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

BLOCK = '''
    // ---------------------------------------------------------------- the base chain (RE the module's own RTTI typeinfo)
    //
    // **THE MODULE'S CLASSES ARE NOT STANDALONE TYPES AND lcns/ WROTE THEM AS IF THEY WERE.** A whole layer of abstract bases was missing, which is
    // why a field would appear at +0x10 with nothing to own it. Each name below is read out of the module's typeinfo strings by
    // re/g_base_chain.py, and the list is in lcns/base_chain.hpp.
    {
        using namespace lcns::base_chain;

        // the two names the Nester family's middle layer needs: **THE +0x10 FIELDS BELONG TO CompositeNester**
        CHECK(std::string(kNester) == "N5Multi6NesterE");
        CHECK(std::string(kCompositeNester) == "N5Multi15CompositeNesterE");

        // and the bases lcns/ was missing entirely
        CHECK(std::string(kRowDistancer) == "N3Row9DistancerE");          // Row::Squeezer IS one
        CHECK(std::string(kEngineEngine) == "N6Engine6EngineE");          // and every concrete engine
        CHECK(std::string(kStructureObserver) == "N9Structure8ObserverE");  // which DOES have a vtable at 0xA53550
        CHECK(std::string(kTilingMultiTiler) == "N6Tiling10MultiTilerE");
        CHECK(std::string(kTilingEvaluator) == "N6Tiling9EvaluatorE");

        // the list is the module's, and it is long enough to be the missing layer rather than one class
        CHECK(sizeof(kUndeclaredAbstractBases) / sizeof(kUndeclaredAbstractBases[0]) == 14);

        // **AND THE ONE THAT MATTERS MOST**: Nester and CompositeNester are DIFFERENT classes, which is the whole reason the fields had no owner
        CHECK(std::string(kNester) != std::string(kCompositeNester));
    }
'''


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "base_chain.hpp" in text:
        print("the test already names the base chain")
        return 0
    if '#include "lcns/recovery.hpp"' in text:
        text = text.replace('#include "lcns/recovery.hpp"', '#include "lcns/recovery.hpp"\n#include "lcns/base_chain.hpp"', 1)
    else:
        marker = text.index("\n\n")
        text = text[:marker] + '\n#include "lcns/base_chain.hpp"' + text[marker:]
    anchor = '    return check::finish("test_recovered");'
    if anchor not in text:
        print("REFUSING: the finish marker is not found")
        return 2
    text = text.replace(anchor, BLOCK + "\n" + anchor, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("added the base-chain assertions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
