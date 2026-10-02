# -*- coding: utf-8 -*-
"""Batch five, by hand: two domain accessors the pattern matcher missed, and ten library functions.

The two the matcher missed, read in round 521:

    0x4FBE70  mov rax, [rcx] ; movsd [rax+0x98], xmm1      ; a double written through the first member
    0x822590  cmp qword [rcx], 0 ; setne al                ; is the first member non null

and the ten that are library, each for a reason visible in its own body:

    0xB81F0   mov eax, 0x64 ; ret                          ; a default override returning the constant 100
    0x877120  loads a member and calls the runtime stub 0x63F4B8
    0x63F140  a bounded byte scan, which is strlen's shape
    0x7C4AB0  allocates eight bytes, stores a vtable, calls the throw entry
    0x998920  the same shape as 0x7C4AB0
    0x889010  stores a vtable then copies a shared_ptr member
    0x1B130   builds a string from a pointer and a length, taking the length through the strlen stub
    0x63DEB0  walks a word array counting non zero entries: a bitset or vector internal
    0x63EA30  compares two word arrays element by element: the same family
    0x63F170  a word by word string scan
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "field_accessors.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")

ACCESSOR = '''/** RE 0x4FBE70: writes the double at +0x98 of the object the first member points at. */
inline void isetDouble98_4FBE70(void* object, double value) {
    unsigned char* inner = nullptr;
    std::memcpy(&inner, object, sizeof(inner));
    std::memcpy(inner + 0x98, &value, sizeof(value));
}

/** RE 0x822590: true when the first member is not null, the setne on a compare against zero. */
inline bool notNullMember_822590(const void* object) {
    const void* member = nullptr;
    std::memcpy(&member, object, sizeof(member));
    return member != nullptr;
}

'''

TESTS = '''    // ------------------- two accessors the pattern matcher missed, written by hand
    {
        unsigned char innerObject[0x400];
        std::memset(innerObject, 0, sizeof(innerObject));
        unsigned char outer[8];
        unsigned char* p = innerObject;
        std::memcpy(outer, &p, sizeof(p));
        lcns::dll::accessors::isetDouble98_4FBE70(outer, 12.5);
        double got = 0.0;
        std::memcpy(&got, innerObject + 0x98, sizeof(got));
        CHECK(got == 12.5);                                  // RE 0x4FBE70
        CHECK(lcns::dll::accessors::notNullMember_822590(outer));   // RE 0x822590, the member is set
        const void* nothing = nullptr;
        std::memcpy(outer, &nothing, sizeof(nothing));
        CHECK(!lcns::dll::accessors::notNullMember_822590(outer));  // and now it is not
    }

    return check::finish("boxacc");'''

LIBRARY = [
    (0xB81F0, "returns the constant 100: a default override, not a computation"),
    (0x877120, "loads a member and calls the runtime stub 0x63F4B8"),
    (0x63F140, "a bounded byte scan, the strlen shape"),
    (0x7C4AB0, "allocates eight bytes, stores a vtable, calls the throw entry"),
    (0x998920, "the same exception object shape as 0x7C4AB0"),
    (0x889010, "stores a vtable then copies a shared_ptr member"),
    (0x1B130, "builds a string from a pointer and a length through the strlen stub"),
    (0x63DEB0, "walks a word array counting non zero entries: a bitset or vector internal"),
    (0x63EA30, "compares two word arrays element by element: the same family"),
    (0x63F170, "a word by word string scan"),
]


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    h = read(HDR)
    anchor = "}  // namespace accessors"
    assert anchor in h, "the accessors namespace close was not found"
    write(HDR, h.replace(anchor, ACCESSOR + anchor, 1))
    print("field_accessors.hpp  two hand written accessors")

    t = read(TEST)
    fin = '    return check::finish("boxacc");'
    assert fin in t, "the boxacc finish anchor was missing"
    write(TEST, t.replace(fin, TESTS, 1))
    print("test_boxacc.cpp      their checks")

    s = read(TOOLCHAIN)
    a = "    0x63F170,  # word by word scan of a string, the strcmp family"
    assert a in s, "the boilerplate anchor was not found"
    lines = [a] + ["    0x%X,  # %s" % (rva, reason) for rva, reason in LIBRARY if rva != 0x63F170]
    write(TOOLCHAIN, s.replace(a, "\n".join(lines), 1))
    print("g_toolchain.py       %d library functions classified" % (len(LIBRARY) - 1))

    marker = "IMPLEMENTED = {"
    assert marker in s, "the implemented registry was not found"
    s2 = read(TOOLCHAIN)
    entry = "    0x4FBE70, 0x822590,   # batch five, lcns/field_accessors.hpp"
    write(TOOLCHAIN, s2.replace(marker, marker + "\n" + entry, 1))
    print("g_toolchain.py       two accessors registered as implemented")
    print("")
    print("done")


if __name__ == "__main__":
    main()
