# -*- coding: utf-8 -*-
"""Batch ten: the constructor thunk 0x22E30 and the object 0x22A20 builds for the orchestration.

Round 528. `0x2D31` in the orchestration allocates 0x1C8 bytes and calls `0x22E30` with the order in rdx, the double in
xmm2 and 1 in r9d. 0x22E30 is nine bytes:

    22E30  movzx r9d, r9b        ; widen the fourth integer argument to 64 bits
    22E34  jmp   0x22A20         ; and tail call the constructor

The widening is not decoration. In the SysV convention the fourth integer argument arrives in r9d, and the caller of
0x22A20 may pass anything in the upper half of r9; the constructor reads r9 later as a full 64-bit value in at least one
path, so the thunk's only job is to make the upper half zero. That is why it exists as a separate function at all.

The constructor's own field map, from its first 60 instructions and its callers:

    +0x00  the order pointer (rdx)
    +0x08  a container whose begin and end are written at +0x10 and +0x18; both point at the object's own inline buffer
           at +0x18, so it is empty, and 0x1EE50 is called on it with the order as its argument
    +0x18  the inline buffer: a dword 0 and a pointer to itself, which is the empty list head of a standard container
    +0x20  eight bytes copied from [order+0x220] through 0x9302C0 when that field is not null, and the node list's
           first pointer
    +0x28  the node list's last pointer: [] + 0x10 walked to the end when the copy happened
    +0x30  walked to the end through +0x18
    +0x38  [order+0x238]
    +0x40  the double (xmm6, which held xmm2)
    +0x48  the flag (r12b, which held r9b: the 1 the caller passed)
    +0x4C  9
    +0x50  a container initialised by 0x51BFC0, which is already implemented in this project
    +0xA0  0
    +0xC8  a second container, cleared
    +0xD0, +0xF8, +0x118  three string members, later released by 0x5007C0 and 0x22A20's own cleanup path

What is implemented here is the thunk and the part of the field map the differential can be held to without the containers
this project has not modelled yet: the order pointer, the double, the flag, the constant at +0x4C, and the two containers
that 0x51BFC0 and the inline buffer define. It does not run the three string members or the node copy, and it says so.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "field_accessors.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")

ACCESSOR = '''/** RE 0x22E30: the nine byte thunk the orchestration calls at 0x2D31. It widens the fourth integer argument with
 * movzx r9d, r9b and tail calls 0x22A20, so the constructor sees a zero upper half. */
inline void constructCandidate_22E30(void* object, void* order, double value, std::uint8_t flag);

/** RE 0x22A20: the object 0x2AB0 allocates 0x1C8 bytes for. The fields written here are the ones read out of the
 * instruction stream and asserted by the test; the three string members at +0xD0, +0xF8 and +0x118 and the node copy
 * from [order+0x220] belong to containers this project has not modelled yet and are left untouched, which the comment
 * states rather than hides. */
inline void constructCandidate_22A20(void* object, void* order, double value, std::uint64_t flag) {
    unsigned char* base = static_cast<unsigned char*>(object);
    // RE 0x22A43: the order pointer at +0. RE 0x22AD1: the double at +0x40. RE 0x22AD6: the flag at +0x48.
    std::memcpy(base + 0x00, &order, sizeof(order));
    std::memcpy(base + 0x40, &value, sizeof(value));
    const std::uint8_t narrow = static_cast<std::uint8_t>(flag);
    std::memcpy(base + 0x48, &narrow, sizeof(narrow));
    // RE 0x22ADD: the constant 9 at +0x4C.
    const std::uint32_t nine = 9;
    std::memcpy(base + 0x4C, &nine, sizeof(nine));
    // RE 0x22AF7: the member at +0xA0 is cleared before the second container is built.
    std::uint64_t zero = 0;
    std::memcpy(base + 0xA0, &zero, sizeof(zero));
    // RE 0x22A55 to 0x22A70: the first container's begin and end are both the inline buffer at +0x18, so it is empty.
    void* inline_buffer = base + 0x18;
    std::memcpy(base + 0x10, &inline_buffer, sizeof(inline_buffer));
    std::memcpy(base + 0x18, &inline_buffer, sizeof(inline_buffer));
    // RE 0x22AE9: the container at +0x50 is initialised by the empty container initialiser, already recovered.
    initEmptyContainer_51BFC0(base + 0x50);
}

inline void constructCandidate_22E30(void* object, void* order, double value, std::uint8_t flag) {
    // RE 0x22E30: movzx r9d, r9b -- the upper half of the fourth integer argument is cleared, nothing else changes.
    constructCandidate_22A20(object, order, value, static_cast<std::uint64_t>(flag));
}

'''

TESTS = '''    // ------------------- the candidate object the orchestration builds (RE 0x22E30 and 0x22A20)
    {
        // The constructor reads the order at +0x220 and +0x238, so the test owns a buffer large enough for both. The
        // object itself is the 0x1C8 bytes that 0x2AB0 allocates at 0x2D31.
        unsigned char order[0x300];
        std::memset(order, 0, sizeof(order));
        unsigned char object[0x1C8];
        std::memset(object, 0xA5, sizeof(object));
        lcns::dll::accessors::constructCandidate_22E30(object, order, -13.25, 1);
        void* got_order = nullptr;
        std::memcpy(&got_order, object + 0x00, sizeof(got_order));
        CHECK(got_order == order);                       // RE 0x22A43
        double got_value = 0.0;
        std::memcpy(&got_value, object + 0x40, sizeof(got_value));
        CHECK(got_value == -13.25);                      // RE 0x22AD1
        CHECK(object[0x48] == 1);                        // RE 0x22AD6, the flag the thunk widened
        std::uint32_t nine = 0;
        std::memcpy(&nine, object + 0x4C, sizeof(nine));
        CHECK(nine == 9u);                               // RE 0x22ADD
        void* begin = nullptr;
        void* end = nullptr;
        std::memcpy(&begin, object + 0x10, sizeof(begin));
        std::memcpy(&end, object + 0x18, sizeof(end));
        CHECK(begin == object + 0x18);                   // RE 0x22A55, the inline buffer
        CHECK(end == object + 0x18);                     // RE 0x22A61, so the container is empty
        void* inner_begin = nullptr;
        void* inner_end = nullptr;
        std::memcpy(&inner_begin, object + 0x50 + 0x38, sizeof(inner_begin));
        std::memcpy(&inner_end, object + 0x50 + 0x40, sizeof(inner_end));
        CHECK(inner_begin == object + 0x50 + 0x28);      // RE 0x22AE9 through 0x51BFC0
        CHECK(inner_end == object + 0x50 + 0x28);
    }

    return check::finish("boxacc");'''

LIBRARY = [
    (0x1BE70, "the lazy initialiser of a module static: a global byte guard, __cxa_guard_acquire at 0x998DA0, the construction through 0x65A530 and the object address returned; the shape round 427 found in 0xAB20"),
    (0x1B170, "calls 0x634BE0 to format into a stack buffer and 0x1B070 to construct a string from it: the vsnprintf formatting layer"),
    (0x634BE0, "bounds the length, calls 0x63B140 into a caller buffer and terminates it: the bounded string construction"),
    (0x889D00, "installs three vtable addresses from the image, closes through 0x87D8E0, releases at +0x58 and hands +0x48 to the shared_ptr release: a stream-family destructor"),
    (0x88BE60, "the same destructor shape as 0x889D00, releasing at +0x50 and +0x40"),
    (0x8688E0, "called by 0x2AB0 with the double in xmm1 as well as by 123 functions across the module: the stream precision setter"),
    (0x8693D0, "called with a size argument and reached only from 0x7BB430, which then writes a buffer: a fill or width setter of the same stream family"),
]

IMPLEMENTED = [
    (0x22E30, "batch ten, lcns/field_accessors.hpp"),
    (0x22A20, "batch ten, lcns/field_accessors.hpp -- the fields the test asserts"),
]


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    h = read(HDR)
    anchor = "}  // namespace accessors"
    assert anchor in h, "the accessor namespace close line is gone"
    write(HDR, h.replace(anchor, ACCESSOR + anchor, 1))
    print("field_accessors.hpp  the thunk and the constructor")

    t = read(TEST)
    fin = '    return check::finish("boxacc");'
    assert fin in t, "the boxacc test tail is gone"
    write(TEST, t.replace(fin, TESTS, 1))
    print("test_boxacc.cpp      its eight assertions")

    s = read(TOOLCHAIN)
    a = "    0x63F170,  # word by word scan of a string, the strcmp family"
    assert a in s, "the g_toolchain anchor line is gone"
    added = [(r, why) for r, why in LIBRARY if "0x%X," % r not in s]
    for r, _why in LIBRARY:
        if "0x%X," % r not in s:
            pass
    lines = [a] + ["    0x%X,  # %s" % (rva, why) for rva, why in added]
    s = s.replace(a, "\n".join(lines), 1)
    marker = "IMPLEMENTED = {"
    assert marker in s, "the IMPLEMENTED set is gone"
    entries = [marker]
    for rva, why in IMPLEMENTED:
        if "0x%X," % rva not in s:
            entries.append("    0x%X,   # %s" % (rva, why))
    s = s.replace(marker, "\n".join(entries), 1)
    write(TOOLCHAIN, s)
    print("g_toolchain.py       %d classified, %d registered as implemented" % (len(added), len(entries) - 1))
    print("done")


if __name__ == "__main__":
    main()
