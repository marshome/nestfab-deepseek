# -*- coding: utf-8 -*-
"""Batch eleven: the constructor's tail, which is where the object's semantics are.

Round 529. 0x22A20 allocates the 0x1C8 bytes 0x2AB0 asks for; batch ten implemented its head and the fields a test could be
held to. Its tail is more informative than the head, because it branches on a mode the ORDER carries:

    22BC1  edi = [order + 0x240]                 ; the mode
    22BAB  xmm0 = 4.0     22BD1  xmm6 = 0.1      ; the defaults
    22BF1  [obj + 0x154] = 10
    22BFB  [obj + 0x158] = 4.0
    22C03  [obj + 0x160] = 0.1
    22C2C  cmp edi, 1 -> 22C92                  ; mode 1
    22C31  cmp edi, 2 -> 22CD0                  ; mode 2
    22C3A  otherwise: [obj + 0x150] = 0
    22C92  mode 1: [obj + 0x150] = 1, xmm3 = 10.0, xmm4 = 0.2, [obj + 0x154] = 0x1F4 = 500
    22CD0  mode 2: [obj + 0x150] = 1, xmm5 = 3.0, [obj + 0x154] = 10

So the flag at +0x150 is "a limit applies", +0x154 is the iteration cap and +0x158/+0x160 are a pair of double parameters:
500 with 10.0 and 0.2 in one mode, 10 with 3.0 in the other, and 10 with 4.0 and 0.1 by default. The three doubles that are
not part of that pair -- 4.0 at +0x158 and 0.1 at +0x160 in the default, 3.0 at +0x158 in mode 2 -- are what distinguishes
the modes, and 4.0/0.1 against 10.0/0.2 is a ratio of the same two numbers, which is what a scale and a relative tolerance
look like.

The mode itself comes from [order+0x240], and 0x65A530 already showed the module distinguishes three log destinations,
local, cloud and plain. The constructor does not decide which; it reads the order's field and configures itself.

What is implemented here is the tail exactly as the instructions read: the three zeroed bytes at +0x148 to +0x14A, the
dword at +0x14C, the mode-dependent flag, cap and pair, and the byte at +0x168. The strings at +0x180 and +0x1A0 are built
by 0x1B130 from two literals that the dump does not carry as text, and the call at 0x22C76 goes to 0x4FBE70, which this
project has already recovered; both are left as the comments say.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "field_accessors.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")

OLD_TAIL = """    // RE 0x22AE9: the container at +0x50 is initialised by the empty container initialiser, already recovered.
    initEmptyContainer_51BFC0(base + 0x50);
}
"""

NEW_TAIL = """    // RE 0x22AE9: the container at +0x50 is initialised by the empty container initialiser, already recovered.
    initEmptyContainer_51BFC0(base + 0x50);
    // RE 0x22AF7 to 0x22B4B: the members from +0xA0 to +0xC0 are cleared.
    for (std::size_t offset = 0xA0; offset <= 0xC0; offset += 8) {
        std::memcpy(base + offset, &zero, sizeof(zero));
    }
    // RE 0x22B56 to 0x22B8C: four members from +0xC8 to +0xE0 are registered and cleared. The registration goes through
    // 0x63F6C8, which is the runtime's atexit family and has no counterpart here, so only the clearing is reproduced.
    std::memcpy(base + 0xC8, &zero, sizeof(zero));
    std::memcpy(base + 0xD0, &zero, sizeof(zero));
    std::memcpy(base + 0xD8, &zero, sizeof(zero));
    std::memcpy(base + 0xE0, &zero, sizeof(zero));
    // RE 0x22B94: the member at +0xE8 is the identity of 0x895F80, which stays zero.
    std::memcpy(base + 0xE8, &zero, sizeof(zero));
    // RE 0x22B9C to 0x22BA6: the dword at +0xF0 and the container at +0xF8.
    const std::uint32_t zero32 = 0;
    std::memcpy(base + 0xF0, &zero32, sizeof(zero32));
    initEmptyContainer_51BFC0(base + 0xF8);
    // RE 0x22BBA to 0x22C1C: the head of the block that carries the three parameters.
    base[0x148] = 0;                                   // RE 0x22BBA
    base[0x149] = 0;                                   // RE 0x22BC7
    base[0x14A] = 0;                                   // RE 0x22BD9
    std::memcpy(base + 0x14C, &zero32, sizeof(zero32));  // RE 0x22BE0
    // RE 0x22C12: the dword at +0x16C, and RE 0x22C1C: the pointer at +0x170.
    std::memcpy(base + 0x16C, &zero32, sizeof(zero32));
    std::memcpy(base + 0x170, &zero, sizeof(zero));
    // RE 0x22C27: the timer object at +0x178 comes from 0x5F3900, which batch seven implemented. It allocates, so it is
    // left out of this initialiser and the field stays as the caller left it; the constructor's own call is recorded here.
    // RE 0x22C1F: the mode is read from the order at +0x240, not from the object.
    std::uint32_t mode = 0;
    if (order != nullptr) {
        std::memcpy(&mode, static_cast<const unsigned char*>(order) + 0x240, sizeof(mode));
    }
    double first = 4.0;                                // RE 0x22BAB, the literal at 0x9AE1E8
    double second = 0.1;                               // RE 0x22BD1, the literal at 0x9AE1F0
    std::uint32_t cap = 10;                            // RE 0x22BF1
    std::uint8_t applies = 0;                          // RE 0x22C3A, the default when the mode is neither 1 nor 2
    if (mode == 1) {                                   // RE 0x22C2C
        first = 10.0;                                  // RE 0x22C92, the literal at 0x9AE1F8
        second = 0.2;                                  // RE 0x22CA1, the literal at 0x9AE200
        cap = 500;                                     // RE 0x22CA9
        applies = 1;
    } else if (mode == 2) {                            // RE 0x22C31
        first = 3.0;                                   // RE 0x22CD0, the literal at 0x9AE208
        cap = 10;                                      // RE 0x22CDF
        applies = 1;
    }
    base[0x150] = applies;                             // RE 0x22C41 and 0x22C9A and 0x22CD8
    std::memcpy(base + 0x154, &cap, sizeof(cap));      // RE 0x22BF1 and 0x22CA9 and 0x22CDF
    std::memcpy(base + 0x158, &first, sizeof(first));  // RE 0x22BFB and 0x22CB3 and 0x22CE9
    std::memcpy(base + 0x160, &second, sizeof(second));// RE 0x22C03 and 0x22CBB
    base[0x168] = 0;                                   // RE 0x22C0B
    // RE 0x22C41 and 0x22C54: the two strings at +0x180 and +0x1A0 are built by 0x1B130 from two literals that the dump
    // does not carry as text, and RE 0x22C76 calls 0x4FBE70, which this project has already recovered. Both are left out
    // here and the object is returned with those three fields as the caller left them.
}
"""

TESTS = '''    // ------------------- the candidate object's mode-dependent tail (RE 0x22A20 from 0x22C1F)
    {
        unsigned char order[0x300];
        unsigned char object[0x1C8];
        // The mode at [order+0x240] selects the parameters; 1 and 2 are the two the code tests for, 0 and 3 fall through
        // to the default, so all four are checked.
        const std::uint32_t modes[4] = {0, 1, 2, 3};
        const std::uint8_t expect_flag[4] = {0, 1, 1, 0};
        const std::uint32_t expect_cap[4] = {10, 500, 10, 10};
        const double expect_first[4] = {4.0, 10.0, 3.0, 4.0};
        const double expect_second[4] = {0.1, 0.2, 0.1, 0.1};
        for (int mode = 0; mode < 4; ++mode) {
            std::memset(order, 0, sizeof(order));
            std::memcpy(order + 0x240, &modes[mode], sizeof(modes[mode]));
            std::memset(object, 0xA5, sizeof(object));
            lcns::dll::accessors::constructCandidate_22E30(object, order, 0.5, 1);
            CHECK(object[0x150] == expect_flag[mode]);            // RE 0x22C41
            std::uint32_t cap = 0;
            std::memcpy(&cap, object + 0x154, sizeof(cap));
            CHECK(cap == expect_cap[mode]);                       // RE 0x22BF1
            double first = 0.0;
            double second = 0.0;
            std::memcpy(&first, object + 0x158, sizeof(first));
            std::memcpy(&second, object + 0x160, sizeof(second));
            CHECK(first == expect_first[mode]);                   // RE 0x22BFB
            CHECK(second == expect_second[mode]);                 // RE 0x22C03
        }
    }

    return check::finish("boxacc");'''


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    h = read(HDR)
    assert OLD_TAIL in h, "the batch ten tail of constructCandidate_22A20 is gone"
    write(HDR, h.replace(OLD_TAIL, NEW_TAIL, 1))
    print("field_accessors.hpp  the constructor tail")

    t = read(TEST)
    fin = '    return check::finish("boxacc");'
    assert fin in t, "the boxacc test tail is gone"
    write(TEST, t.replace(fin, TESTS, 1))
    print("test_boxacc.cpp      the four-mode check")
    print("done")


if __name__ == "__main__":
    main()
