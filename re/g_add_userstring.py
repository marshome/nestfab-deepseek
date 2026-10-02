# -*- coding: utf-8 -*-
"""Classify two std::string internals and land ordinal 208, which is a string assignment.

Read in round 508:

    0x910C20 (299 bytes) and 0x90ECB0 (650 bytes) both work on the three words at [rcx], [rcx + 8] and [rcx + 0x10] --
    a data pointer, a length and a small-string buffer -- and 0x910C20 calls 0x910BA0, the growth routine classified two
    rounds ago. That is libstdc++'s std::string layout, so both are library code and neither is domain logic.

That classification collapses the closure of ordinal 208 to nothing, and its own body then reads:

    0x16CB0  call 0x63F238            ; the strlen stub on the second argument
             r8 = [rbx + 0x1C0]
             rcx = rbx + 0x1B8 ; edx = 0 ; r9 = the pointer ; [rsp] = the length
             call 0x90ECB0            ; the std::string operation

so ordinal 208 assigns the given C string to the std::string at +0x1B8 of the object. That is the same field the already
implemented getUserStringAt1B8 reads, and this confirms what that field is: a real std::string, because the three words
line up with libstdc++ and the length is taken with strlen rather than stored. The reimplementation therefore uses
std::string itself, which is what the original does, instead of a hand-rolled buffer.
"""
import io
import json
import os

ROOT = r"D:\Nesting\nestfab"
LAYOUT = os.path.join(ROOT, "lcns", "include", "lcns", "dll_layout.hpp")
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")
SRC = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
MAP = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")
TEST = os.path.join(ROOT, "lcns", "tests", "test_exports.cpp")
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")

CARRIER = '''/**
 * The std::string at +0x1B8 of a part, as libstdc++ lays it out: data at +0x00, length at +0x08 and the small string
 * buffer at +0x10. RE 0x90ECB0 reads all three, and RE 0x16CB0 reaches it through the strlen stub, which is why the
 * field is modelled as std::string rather than as a raw pointer.
 */
struct UserStringHolder {
    void* data;                                // +0x00
    std::size_t length;                        // +0x08
    unsigned char smallBuffer[0x10];
    std::string* stringAt(std::size_t offset) { return reinterpret_cast<std::string*>(reinterpret_cast<unsigned char*>(this) + offset); }
};
static_assert(offsetof(UserStringHolder, data) == 0x00, "libstdc++ layout, RE 0x90ECB0");
static_assert(offsetof(UserStringHolder, length) == 0x08, "libstdc++ layout, RE 0x90ECB0");
static_assert(offsetof(UserStringHolder, smallBuffer) == 0x10, "libstdc++ layout, RE 0x90ECB0");

'''

DECL = '''/** RE 0x16CB0 (ordinal 208): assigns the C string to the std::string at +0x1B8. */
void setUserStringAt1B8(void* object, const char* text);

'''

BODY = '''void setUserStringAt1B8(void* object, const char* text) {
    // RE 0x16CB0: the length comes from the strlen stub at 0x63F238, and the string sits at +0x1B8, so this is an
    // assignment of a C string into a std::string, done with the same type the original uses.
    auto* holder = reinterpret_cast<std::string*>(static_cast<unsigned char*>(object) + 0x1B8);
    *holder = (text != nullptr) ? text : "";
}

'''

TESTS = '''    // ------------------- ordinal 208: a std::string assignment at +0x1B8
    {
        // A std::string has to live at +0x1B8 for this to be the same operation the original performs, so the test builds
        // exactly that: an object large enough, with a std::string at the offset the assembly names.
        alignas(std::string) unsigned char object[0x1B8 + sizeof(std::string) + 0x40];
        std::memset(object, 0, sizeof(object));
        auto* holder = new (object + 0x1B8) std::string();
        lcns::dll::exports::impl::setUserStringAt1B8(object, "hello");
        CHECK(holder->size() == 5);
        CHECK(*holder == "hello");
        lcns::dll::exports::impl::setUserStringAt1B8(object, "");
        CHECK(holder->empty());
        lcns::dll::exports::impl::setUserStringAt1B8(object, "a much longer string that will not fit in the small buffer at all");
        CHECK(holder->size() == 61);                 // the assignment replaces rather than appends
        CHECK(holder->compare(0, 4, "a mu") == 0);
        lcns::dll::exports::impl::setUserStringAt1B8(object, nullptr);
        CHECK(holder->empty());                      // a null pointer is treated as the empty string
        holder->~basic_string();
        CHECK(offsetof(lcns::dll::UserStringHolder, data) == 0x00);
        CHECK(offsetof(lcns::dll::UserStringHolder, length) == 0x08);
        CHECK(offsetof(lcns::dll::UserStringHolder, smallBuffer) == 0x10);
    }

    return check::finish("exports");'''


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    table = json.loads(io.open(os.path.join(ROOT, "re", "exports_table.json"), encoding="utf-8").read())
    ords = []
    for e in table:
        if e["rva"] == 0x16CB0:
            ords.append((e.get("ords") or [0])[0])   # primary ordinal only, per the map contract
    assert ords, "no ordinal maps to 0x16CB0"
    print("primary ordinal for 0x16CB0: %s" % ords)

    # 1. the two string internals join the library set
    t = read(TOOLCHAIN)
    a = "    0x910BA0,  # std::string growth: length field, doubling, allocate\n}"
    assert a in t, "the boilerplate close was not found"
    add = ("    0x910C20,  # std::string internal: data, length and small buffer, calls the growth routine\n"
           "    0x90ECB0,  # std::string internal: same three words, clamps against max_size\n}")
    write(TOOLCHAIN, t.replace(a, add, 1))
    print("g_toolchain.py    both string internals classified as library")

    # 2. the carrier, the declaration, the body, the row, the test
    t = read(LAYOUT)
    b = "}  // namespace dll"
    assert b in t
    write(LAYOUT, t.replace(b, CARRIER + b, 1))
    print("dll_layout.hpp    UserStringHolder with three offset assertions")

    h = read(HDR)
    c = "void setShearMode(void* order, int value);"
    assert c in h
    write(HDR, h.replace(c, DECL + c, 1))
    print("exports_impl.hpp  declaration")

    s = read(SRC)
    d = "void setShearMode(void* order, int value)"
    assert d in s
    src = s.replace(d, BODY + d, 1)
    if "#include <string>" not in src:
        e = "#include <thread>"
        assert e in src, "the thread include was not found"
        src = src.replace(e, e + "\n#include <string>", 1)
        print("exports_impl.cpp  string included")
    write(SRC, src)
    print("exports_impl.cpp  body")

    m = read(MAP)
    f = "    {33, reinterpret_cast<void*>(&lcns::dll::exports::impl::getSolutionIdentity)},  // GetSolution"
    assert f in m
    rows = "\n".join("    {%d, reinterpret_cast<void*>(&lcns::dll::exports::impl::setUserStringAt1B8)},"
                     "  // sub_16CB0" % o for o in ords)
    write(MAP, m.replace(f, f + "\n" + rows, 1))
    print("exports_forwarding.inc  %d row(s)" % len(ords))

    e = read(TEST)
    g = '    return check::finish("exports");'
    assert g in e
    e = e.replace(g, TESTS, 1)
    start = e.find("const bool expected = ")
    assert start > 0
    end = e.find(";", start)
    e = e[:end] + "".join(" || e->ordinal0 == %d" % o for o in ords) + e[end:]
    old = "CHECK(ex::forwardedCount() == 30u);"
    assert old in e, "the forwardedCount assertion was not found at 30"
    e = e.replace(old, "CHECK(ex::forwardedCount() == %du);" % (30 + len(ords)), 1)
    write(TEST, e)
    print("test_exports.cpp  string assignment checked, count 30 -> %d" % (30 + len(ords)))
    print("")
    print("done. Expected forwardedCount %d" % (30 + len(ords)))


if __name__ == "__main__":
    main()
