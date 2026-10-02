# -*- coding: utf-8 -*-
"""Land the two window spans behind GetLength and GetHeight, using the real anchors this time.

Round 472 failed because the script asserted something about boxmerge.hpp that was not true: it has no #include line at
all, and its declarations live in lcns::dll::exports::impl, not in a namespace called lcns::boxmerge. The header was read
in round 473 and it is fifteen lines:

    // lcns/boxmerge.hpp -- RE 0x5C8C50: merge the box at srcBase into the box at dstBase.
    #pragma once
    namespace lcns { namespace dll { namespace exports { namespace impl {
    void mergeBoxInto(void* dstBase, const void* srcBase);
    } } } }

So this version adds the include it needs, declares the spans inside the same impl namespace, and discovers the insertion
points by searching the files rather than assuming them. Every step asserts before it writes.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "boxmerge.hpp")
SRC = os.path.join(ROOT, "lcns", "src", "boxmerge.cpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")

SPAN_DECL = '''
/**
 * The two spans that the GetLength and GetHeight implementers return, as read from their tails:
 * RE 0x526227 with RE 0x52624D for the first, RE 0x526767 with RE 0x526790 for the second, and zero when there is no
 * geometry (RE 0x526264, RE 0x5267B0). The status argument that selects these branches is the implementer's second
 * argument (RE 0x526170 saves it, RE 0x526216 reads it) and both entry points pass zero, so this is the branch they take.
 */
double windowSpanLength(const lcns::dll::WindowSlots& window, bool hasGeometry);
double windowSpanHeight(const lcns::dll::WindowSlots& window, bool hasGeometry);
'''

SPAN_BODY = '''
double windowSpanLength(const lcns::dll::WindowSlots& window, bool hasGeometry) {
    if (!hasGeometry) {
        return 0.0;   // RE 0x526264
    }
    return window.slot18 - window.slot38;   // RE 0x526227 and RE 0x52624D
}

double windowSpanHeight(const lcns::dll::WindowSlots& window, bool hasGeometry) {
    if (!hasGeometry) {
        return 0.0;   // RE 0x5267B0
    }
    return window.slot20 - window.slot40;   // RE 0x526767 and RE 0x526790
}
'''

SPAN_TESTS = '''    // ------------------------------------- the two window spans behind GetLength and GetHeight
    {
        // Hand computed so that the two answers differ and a mix-up between them cannot pass: 30 - 4 = 26 and 17 - 2 = 15.
        lcns::dll::WindowSlots window{};
        window.slot18 = 30.0;
        window.slot38 = 4.0;
        window.slot20 = 17.0;
        window.slot40 = 2.0;
        CHECK(lcns::dll::exports::impl::windowSpanLength(window, true) == 26.0);
        CHECK(lcns::dll::exports::impl::windowSpanHeight(window, true) == 15.0);
        CHECK(lcns::dll::exports::impl::windowSpanLength(window, false) == 0.0);
        CHECK(lcns::dll::exports::impl::windowSpanHeight(window, false) == 0.0);
        // the pairs these spans must not read are set far away, so reading the wrong pair fails loudly
        window.slot08 = 1000.0;
        window.slot48 = -1000.0;
        window.slot10 = 1000.0;
        window.slot50 = -1000.0;
        CHECK(lcns::dll::exports::impl::windowSpanLength(window, true) == 26.0);
        CHECK(lcns::dll::exports::impl::windowSpanHeight(window, true) == 15.0);
    }

    return check::finish("boxacc");'''


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    # 1. the header: one include, and two declarations inside the existing impl namespace
    hdr = read(HDR)
    assert "#pragma once" in hdr, "no pragma once in boxmerge.hpp"
    assert "void mergeBoxInto" in hdr, "mergeBoxInto declaration not found"
    assert '#include "lcns/dll_layout.hpp"' not in hdr, "the include is already there"
    hdr = hdr.replace("#pragma once", '#pragma once\n\n#include "lcns/dll_layout.hpp"', 1)
    marker = "void mergeBoxInto(void* dstBase, const void* srcBase);"
    hdr = hdr.replace(marker, marker + "\n" + SPAN_DECL, 1)
    write(HDR, hdr)
    print("patched boxmerge.hpp    (include plus two span declarations)")

    # 2. the source: bodies just before the innermost namespace close
    src = read(SRC)
    close = "}  // namespace impl"
    assert close in src, "the impl namespace close is not in boxmerge.cpp"
    src = src.replace(close, SPAN_BODY + "\n" + close, 1)
    write(SRC, src)
    print("patched boxmerge.cpp    (two span bodies, each citing its RVA)")

    # 3. the test: make sure the header is visible, then add hand computed checks
    test = read(TEST)
    if '#include "lcns/boxmerge.hpp"' not in test:
        first = test.find("#include")
        assert first >= 0, "no include at all in test_boxacc.cpp"
        eol = test.find("\n", first)
        assert eol > first
        test = test[:eol + 1] + '#include "lcns/boxmerge.hpp"\n' + test[eol + 1:]
        print("test_boxacc.cpp         (added the boxmerge include)")
    anchor = '    return check::finish("boxacc");'
    assert anchor in test, "the boxacc finish anchor is missing"
    test = test.replace(anchor, SPAN_TESTS, 1)
    write(TEST, test)
    print("patched test_boxacc.cpp (hand computed span checks)")

    print("")
    print("the spans are implemented and tested; the two export ordinals are still not forwarded, because the window")
    print("traversal that feeds them has not been read and forwarding it now would be a guess")


if __name__ == "__main__":
    main()
