# -*- coding: utf-8 -*-
"""Implement the two pair-copy accessors and hold them to the original.

Round 484 read both whole, nineteen bytes each:

    5203D0  r9 = [rdx + 0x38] ; r10 = [rdx + 0x40] ; [rcx] = r9 ; [rcx + 8] = r10 ; ret
    5203F0  r9 = [rdx + 0x28] ; r10 = [rdx + 0x30] ; [rcx] = r9 ; [rcx + 8] = r10 ; ret

Note the argument order: rdx is the element and rcx the destination, so the second argument is the source. 0x524EE0 calls
them one after the other, which is how an element contributes two pairs of coordinates to the box arithmetic.

Both were classified callable when embedded in round 485, so unlike the export entries -- which begin by handing a
rip-relative label to the logger and therefore cannot run from another image -- these can be compared against the original
bit for bit. That is what the test below does, with values chosen to be awkward: negative zero, a denormal, and a pair of
distinct bit patterns, so a mistake in which offset is read cannot pass.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "boxmerge.hpp")
SRC = os.path.join(ROOT, "lcns", "src", "boxmerge.cpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")

DECL = """void copyPair38(void* destination, const void* element);   // RE 0x5203D0 -- first argument is the destination, per RCX/RDX: the pair at +0x38 and +0x40
void copyPair28(void* destination, const void* element);   // RE 0x5203F0 -- first argument is the destination, per RCX/RDX: the pair at +0x28 and +0x30
"""

BODY = """void copyPair38(void* destination, const void* element) {
    const unsigned char* src = static_cast<const unsigned char*>(element);
    unsigned char* dst = static_cast<unsigned char*>(destination);
    double first = 0.0;    // RE 0x5203D0: r9 = [rdx + 0x38]
    double second = 0.0;   // RE 0x5203D4: r10 = [rdx + 0x40]
    std::memcpy(&first, src + 0x38, sizeof(first));
    std::memcpy(&second, src + 0x40, sizeof(second));
    std::memcpy(dst, &first, sizeof(first));        // RE 0x5203DB: [rcx] = r9
    std::memcpy(dst + 8, &second, sizeof(second));  // RE 0x5203DE: [rcx + 8] = r10
}

void copyPair28(void* destination, const void* element) {
    const unsigned char* src = static_cast<const unsigned char*>(element);
    unsigned char* dst = static_cast<unsigned char*>(destination);
    double first = 0.0;    // RE 0x5203F0: r9 = [rdx + 0x28]
    double second = 0.0;   // RE 0x5203F4: r10 = [rdx + 0x30]
    std::memcpy(&first, src + 0x28, sizeof(first));
    std::memcpy(&second, src + 0x30, sizeof(second));
    std::memcpy(dst, &first, sizeof(first));        // RE 0x5203FB: [rcx] = r9
    std::memcpy(dst + 8, &second, sizeof(second));  // RE 0x5203FE: [rcx + 8] = r10
}
"""

TESTS = '''    // ---------------- 0x5203D0 and 0x5203F0 against the original, which is callable for both
#if defined(LCNS_HAS_EMBEDDED_ASM)
    {
        auto orig38 = reinterpret_cast<void (*)(void*, const void*)>(emb::originalOf(0x5203D0u));
        auto orig28 = reinterpret_cast<void (*)(void*, const void*)>(emb::originalOf(0x5203F0u));
        CHECK(orig38 != nullptr);
        CHECK(orig28 != nullptr);
        if (orig38 != nullptr && orig28 != nullptr) {
            // Awkward bit patterns, and the two pairs deliberately swapped in value, so reading the wrong offset fails.
            const std::uint64_t bits28[4] = {0x8000000000000000ull, 0x0000000000000001ull,
                                             0x3FF0000000000000ull, 0xBFF8000000000000ull};
            const std::uint64_t bits38[4] = {0x7FEFFFFFFFFFFFFFull, 0x0000000000000000ull,
                                             0x400921FB54442D18ull, 0xC01921FB54442D18ull};
            unsigned char element[0x60];
            std::memset(element, 0x5A, sizeof(element));   // fills everything else with noise
            std::memcpy(element + 0x28, bits28, sizeof(bits28));
            std::memcpy(element + 0x38, bits38, sizeof(bits38));
            unsigned char mine[16];
            unsigned char theirs[16];
            for (int which = 0; which < 2; ++which) {
                std::memset(mine, 0, sizeof(mine));
                std::memset(theirs, 0, sizeof(theirs));
                if (which == 0) {
                    lcns::dll::exports::impl::copyPair38(mine, element);
                    orig38(theirs, element);
                } else {
                    lcns::dll::exports::impl::copyPair28(mine, element);
                    orig28(theirs, element);
                }
                CHECK(std::memcmp(mine, theirs, sizeof(mine)) == 0);   // bit for bit, not approximately
            }
        }
    }
#endif

    return check::finish("boxacc");'''


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    hdr = read(HDR)
    anchor = "double windowSpanHeight(const lcns::dll::WindowSlots& window, const void* boxBase, bool hasGeometry);"
    assert anchor in hdr, "the span declaration block was not found in boxmerge.hpp"
    write(HDR, hdr.replace(anchor, anchor + "\n" + DECL, 1))
    print("boxmerge.hpp   the two accessor declarations")

    src = read(SRC)
    close = "}  // namespace impl"
    assert close in src, "the impl namespace close was not found in boxmerge.cpp"
    assert "#include <cstring>" in src, "cstring is expected to be included already"
    write(SRC, src.replace(close, BODY + "\n" + close, 1))
    print("boxmerge.cpp   the two accessor bodies, each line citing its instruction")

    test = read(TEST)
    finish = '    return check::finish("boxacc");'
    assert finish in test, "the boxacc finish anchor was missing"
    write(TEST, test.replace(finish, TESTS, 1))
    print("test_boxacc.cpp differential comparison against the embedded originals")

    print("")
    print("done: two more routines held to the original, and this time by running it")


if __name__ == "__main__":
    main()
