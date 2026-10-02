# -*- coding: utf-8 -*-
"""Batch six: one container initialiser implemented, seven functions classified from their bodies.

Read in rounds 523 and 524 out of the LaunchLocalComputation closure.

    0x51BFC0  lea rax,[rcx+0x28] ; clears +0x00 .. +0x48 ; then +0x38 = +0x40 = rax
              an empty container whose two pointers aim at the inline buffer at +0x28, which is testable

    0x921970, 0x921B40, 0x944690, 0x944860   four functions of the same shape:
              xor eax,eax ; setne al ; mov [rcx+8], eax ; lea rax,[rip+..] ; mov [rcx], rax
              they install a vtable taken from the image and store whether the second argument was null. The vtable's
              address belongs to the original image and cannot be reproduced, and the class is not modelled, so these are
              ABI rather than domain code.

    0x9A0700  takes a global, calls an import stub, allocates eight bytes, stores a vtable, throws
    0x62FF40  special cases -1, builds six bytes on the stack and calls a library routine
    0x8771C0  tests the first member and a flag then clears: a release or reset path
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "field_accessors.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")

ACCESSOR = '''/** RE 0x51BFC0: clears a container and points its begin and end at the inline buffer at +0x28. */
inline void initEmptyContainer_51BFC0(void* object) {
    unsigned char* base = static_cast<unsigned char*>(object);
    for (std::size_t offset = 0x00; offset <= 0x48; offset += 8) {
        std::uint64_t zero = 0;
        std::memcpy(base + offset, &zero, sizeof(zero));
    }
    void* buffer = base + 0x28;
    std::memcpy(base + 0x38, &buffer, sizeof(buffer));
    std::memcpy(base + 0x40, &buffer, sizeof(buffer));
}

'''

TESTS = '''    // ------------------- the empty container initialiser
    {
        unsigned char container[0x60];
        std::memset(container, 0xA5, sizeof(container));
        lcns::dll::accessors::initEmptyContainer_51BFC0(container);
        std::uint64_t zero = 1;
        std::memcpy(&zero, container + 0x00, sizeof(zero));
        CHECK(zero == 0u);
        std::memcpy(&zero, container + 0x20, sizeof(zero));
        CHECK(zero == 0u);
        std::memcpy(&zero, container + 0x48, sizeof(zero));
        CHECK(zero == 0u);
        void* begin = nullptr;
        void* end = nullptr;
        std::memcpy(&begin, container + 0x38, sizeof(begin));
        std::memcpy(&end, container + 0x40, sizeof(end));
        CHECK(begin == container + 0x28);              // RE 0x51BFFA
        CHECK(end == container + 0x28);                // RE 0x51BFFE, empty
    }

    return check::finish("boxacc");'''

LIBRARY = [
    (0x921970, "installs a vtable from the image and stores whether the argument was null: ABI, and the vtable address cannot be reproduced"),
    (0x921B40, "the same constructor shape as 0x921970"),
    (0x944690, "the same constructor shape as 0x921970"),
    (0x944860, "the same constructor shape as 0x921970"),
    (0x9A0700, "takes a global, calls an import stub, allocates eight bytes, stores a vtable and throws"),
    (0x62FF40, "special cases minus one and builds six bytes on the stack for a library routine"),
    (0x8771C0, "tests the first member and a flag then clears: a release or reset path"),
]


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    h = read(HDR)
    anchor = "}  // namespace accessors"
    assert anchor in h
    write(HDR, h.replace(anchor, ACCESSOR + anchor, 1))
    print("field_accessors.hpp  the container initialiser")

    t = read(TEST)
    fin = '    return check::finish("boxacc");'
    assert fin in t
    write(TEST, t.replace(fin, TESTS, 1))
    print("test_boxacc.cpp      its checks")

    s = read(TOOLCHAIN)
    a = "    0x63F170,  # word by word scan of a string, the strcmp family"
    assert a in s
    lines = [a] + ["    0x%X,  # %s" % (rva, reason) for rva, reason in LIBRARY]
    s = s.replace(a, "\n".join(lines), 1)
    marker = "IMPLEMENTED = {"
    entry = "    0x51BFC0,   # batch six, lcns/field_accessors.hpp"
    s = s.replace(marker, marker + "\n" + entry, 1)
    write(TOOLCHAIN, s)
    print("g_toolchain.py       %d classified as library, one registered as implemented" % len(LIBRARY))
    print("done")


if __name__ == "__main__":
    main()
