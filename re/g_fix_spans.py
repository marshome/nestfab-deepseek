# -*- coding: utf-8 -*-
"""Correct the two window spans after round 474 found the real stack base.

Round 473 read rsi as rsp+0x70 and produced window[+0x18] - window[+0x38] and window[+0x20] - window[+0x40]. Round 474 read
the opening of 0x526160:

    526177  call 0x51D0C0                 ; the container view, not 0x51C020 as earlier notes said
    526189  lea rsi, [rsp + 0xA0]         ; so rsi is rsp+0xA0, and the merged box lives at rsp+0x70, before it
    526199  lea rbp, [rsp + 0x70]         ; the box, whose +0x08, +0x10, +0x18, +0x20 are cleared and then merged into

With that base, the four return forms read:

    0x526244 + 0x52624D   box[+0x18] - window[+0x08]      GetLength, status true   <- the entries pass zero
    0x526227 + 0x526230   window[+0x18] - box[+0x08]      GetLength, status false
    0x526790 + 0x5267A2   box[+0x20] - window[+0x10]      GetHeight, status true   <- the entries pass zero
    0x526767 + 0x526770   window[+0x20] - box[+0x10]      GetHeight, status false

0x526264 and 0x5267B0 return zero without geometry. Box +0x18 and +0x20 are maxX and maxY in this project's own box model
(boxacc.hpp), so the meaning is the span of the merged bounding box.

Round 475 tried to land this from two one line commands and only the second one applied, leaving the test calling three
argument functions that did not exist; the build failed and the edit was reverted. It is a file this time.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "boxmerge.hpp")
SRC = os.path.join(ROOT, "lcns", "src", "boxmerge.cpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")

OLD_DECL = """double windowSpanLength(const lcns::dll::WindowSlots& window, bool hasGeometry);
double windowSpanHeight(const lcns::dll::WindowSlots& window, bool hasGeometry);"""

NEW_DECL = """double windowSpanLength(const lcns::dll::WindowSlots& window, const void* boxBase, bool hasGeometry);
double windowSpanHeight(const lcns::dll::WindowSlots& window, const void* boxBase, bool hasGeometry);"""

NEW_BODIES = """double windowSpanLength(const lcns::dll::WindowSlots& window, const void* boxBase, bool hasGeometry) {
    if (!hasGeometry) {
        return 0.0;   // RE 0x526264
    }
    // RE 0x526244 with RE 0x52624D: the merged box maxX minus the window low value.
    double maxX = 0.0;
    std::memcpy(&maxX, static_cast<const unsigned char*>(boxBase) + 0x18, sizeof(maxX));
    return maxX - window.slot08;
}

double windowSpanHeight(const lcns::dll::WindowSlots& window, const void* boxBase, bool hasGeometry) {
    if (!hasGeometry) {
        return 0.0;   // RE 0x5267B0
    }
    // RE 0x526790 with RE 0x5267A2: the merged box maxY minus the window low value.
    double maxY = 0.0;
    std::memcpy(&maxY, static_cast<const unsigned char*>(boxBase) + 0x20, sizeof(maxY));
    return maxY - window.slot10;
}
"""

NEW_TESTS = '''    // ------------------------- the two window spans behind GetLength and GetHeight, box max minus window low
    {
        // Hand computed so that a mix-up cannot pass: 30 - 4 = 26 for the length and 17 - 2 = 15 for the height.
        unsigned char box[0x28];
        std::memset(box, 0, sizeof(box));
        double maxX = 30.0;
        double maxY = 17.0;
        std::memcpy(box + 0x18, &maxX, sizeof(maxX));
        std::memcpy(box + 0x20, &maxY, sizeof(maxY));
        lcns::dll::WindowSlots window{};
        window.slot08 = 4.0;
        window.slot10 = 2.0;
        CHECK(lcns::dll::exports::impl::windowSpanLength(window, box, true) == 26.0);
        CHECK(lcns::dll::exports::impl::windowSpanHeight(window, box, true) == 15.0);
        CHECK(lcns::dll::exports::impl::windowSpanLength(window, box, false) == 0.0);   // no geometry returns zero
        CHECK(lcns::dll::exports::impl::windowSpanHeight(window, box, false) == 0.0);
        // the slots these spans must not read are moved far away, so reading the wrong pair fails loudly
        window.slot18 = 1000.0;
        window.slot20 = -1000.0;
        CHECK(lcns::dll::exports::impl::windowSpanLength(window, box, true) == 26.0);
        CHECK(lcns::dll::exports::impl::windowSpanHeight(window, box, true) == 15.0);
    }

    return check::finish("boxacc");'''


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    # 1. the declarations
    hdr = read(HDR)
    assert OLD_DECL in hdr, "the two argument span declarations are not in boxmerge.hpp"
    write(HDR, hdr.replace(OLD_DECL, NEW_DECL, 1))
    print("boxmerge.hpp    declarations now take the box base")

    # 2. the bodies: replace everything from the first span body up to the namespace close
    src = read(SRC)
    start = src.find("double windowSpanLength(const lcns::dll::WindowSlots& window, bool hasGeometry) {")
    assert start > 0, "the old length body was not found"
    close = src.find("}  // namespace impl", start)
    assert close > start, "the impl namespace close was not found after the bodies"
    src = src[:start] + NEW_BODIES + "\n" + src[close:]
    if "#include <cstring>" not in src:
        anchor = '#include "lcns/boxmerge.hpp"'
        assert anchor in src, "boxmerge.cpp does not include its own header"
        src = src.replace(anchor, anchor + "\n#include <cstring>", 1)
        print("boxmerge.cpp    added cstring")
    write(SRC, src)
    print("boxmerge.cpp    bodies now read the box max minus the window low value")

    # 3. the tests
    test = read(TEST)
    begin = test.find("    // ------------------------------------- the two window spans behind GetLength and GetHeight")
    assert begin > 0, "the span test block start was not found"
    end = test.find('    return check::finish("boxacc");', begin)
    assert end > begin, "the boxacc finish anchor was not found after the span block"
    write(TEST, test[:begin] + NEW_TESTS + test[end + len('    return check::finish("boxacc");'):])
    print("test_boxacc.cpp rewritten with the corrected provenance and the same hand computed 26 and 15")

    print("")
    print("corrected. The two export ordinals are still not forwarded: the window fields at +0x08 and +0x10 that these")
    print("spans subtract have not yet been traced to whatever fills them")


if __name__ == "__main__":
    main()
