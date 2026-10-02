# -*- coding: utf-8 -*-
"""Accessor batch four, with two new shapes: address-of and a one dword copy.

Read in round 516 from the LaunchLocalComputation closure:

    value getters
    0x52F930  movzx eax, [rcx+0x20]     0x52F940  movzx eax, [rcx+0x21]
    0x4F7350  movzx eax, [rcx+0x68]     0x4F7360  movzx eax, [rcx+0x69]
    0x4F73A0  movzx eax, [rcx+0x6A]     0x5FBC70  movzx eax, [rcx+8]
    0x5C4CE0  mov rax, [rcx+8]

    address of a member, which returns a pointer rather than a value
    0x4F73C0  lea rax, [rcx+0x70]       0x5C5F40  lea rax, [rcx+0x18]
    0x54D120  lea rax, [rcx+8]          0x5C5F60  lea rax, [rcx+0x18]
    0x5483B0  lea rax, [rcx+0x38]       0x5483A0  lea rax, [rcx+0x28]

    one dword copied from the second argument to the first
    0x54CE60  mov eax, [rdx] ; mov [rcx], eax
    0x52F8A0  mov eax, [rdx] ; mov [rcx], eax

and one more identity: 0x5C5270 `mov rax, rcx ; ret`.

The address-of shape matters: it is how the original hands a member to another function by pointer, so the
reimplementation has to return the same address rather than a copy. The copy shape takes the destination first, as the
ABI does, and the test checks both directions so a swapped pair cannot pass.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "field_accessors.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")

GETTERS = [
    ("getByte20_52F930", 0x52F930, 0x20, 1),
    ("getByte21_52F940", 0x52F940, 0x21, 1),
    ("getByte68_4F7350", 0x4F7350, 0x68, 1),
    ("getByte69_4F7360", 0x4F7360, 0x69, 1),
    ("getByte6A_4F73A0", 0x4F73A0, 0x6A, 1),
    ("getByte08_5FBC70", 0x5FBC70, 0x08, 1),
    ("getPtr08_5C4CE0", 0x5C4CE0, 0x08, 8),
]

ADDRESSES = [
    ("addr70_4F73C0", 0x4F73C0, 0x70),
    ("addr18_5C5F40", 0x5C5F40, 0x18),
    ("addr08_54D120", 0x54D120, 0x08),
    ("addr18_5C5F60", 0x5C5F60, 0x18),
    ("addr38_5483B0", 0x5483B0, 0x38),
    ("addr28_5483A0", 0x5483A0, 0x28),
]

COPIES = [
    ("copyDword_54CE60", 0x54CE60),
    ("copyDword_52F8A0", 0x52F8A0),
]

IDENTITY = [0x5C5270]


def lines_for_header():
    out = []
    for name, rva, offset, width in GETTERS:
        bits = width * 8
        out.append("/** RE 0x%X: reads the %d-bit value at +0x%02X. */" % (rva, bits, offset))
        out.append("inline std::uint%d_t %s(const void* object) {" % (bits, name))
        out.append("    std::uint%d_t value = 0;" % bits)
        out.append("    std::memcpy(&value, static_cast<const unsigned char*>(object) + 0x%02X, sizeof(value));" % offset)
        out.append("    return value;")
        out.append("}")
        out.append("")
    for name, rva, offset in ADDRESSES:
        out.append("/** RE 0x%X: returns the address of the member at +0x%02X, not its value. */" % (rva, offset))
        out.append("inline void* %s(void* object) {" % name)
        out.append("    return static_cast<unsigned char*>(object) + 0x%02X;" % offset)
        out.append("}")
        out.append("")
    for name, rva in COPIES:
        out.append("/** RE 0x%X: copies one dword from the second argument to the first. */" % rva)
        out.append("inline void %s(void* destination, const void* source) {" % name)
        out.append("    std::uint32_t value = 0;")
        out.append("    std::memcpy(&value, source, sizeof(value));")
        out.append("    std::memcpy(destination, &value, sizeof(value));")
        out.append("}")
        out.append("")
    return out


def lines_for_test():
    out = ["    // ------------------- field accessors, fourth batch: values, addresses and a copy"]
    out.append("    {")
    out.append("        unsigned char object[0x80];")
    out.append("        std::memset(object, 0xA5, sizeof(object));")
    for name, rva, offset, width in GETTERS:
        bits = width * 8
        probe = 0x5A if width == 1 else 0x1122334455667788
        out.append("        {")
        out.append("            const std::uint%d_t put = 0x%Xull;" % (bits, probe))
        out.append("            std::memcpy(object + 0x%02X, &put, sizeof(put));" % offset)
        out.append("            CHECK(lcns::dll::accessors::%s(object) == put);   // RE 0x%X" % (name, rva))
        out.append("        }")
    for name, rva, offset in ADDRESSES:
        out.append("        CHECK(lcns::dll::accessors::%s(object) == object + 0x%02X);   // RE 0x%X, an address not a value"
                   % (name, offset, rva))
    for name, rva in COPIES:
        out.append("        {")
        out.append("            unsigned char source[8];")
        out.append("            unsigned char destination[8];")
        out.append("            const std::uint32_t put = 0x0BADF00Du;")
        out.append("            std::memcpy(source, &put, sizeof(put));")
        out.append("            std::memset(destination, 0, sizeof(destination));")
        out.append("            lcns::dll::accessors::%s(destination, source);   // RE 0x%X" % (name, rva))
        out.append("            std::uint32_t got = 0;")
        out.append("            std::memcpy(&got, destination, sizeof(got));")
        out.append("            CHECK(got == put);")
        out.append("            std::uint32_t untouched = 0;")
        out.append("            std::memcpy(&untouched, destination + 4, sizeof(untouched));")
        out.append("            CHECK(untouched == 0u);   // exactly one dword is copied, not two")
        out.append("        }")
    out.append("    }")
    out.append("")
    out.append('    return check::finish("boxacc");')
    return out


def main():
    h = io.open(HDR, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    anchor = "}  // namespace accessors"
    assert anchor in h, "the accessors namespace close was not found"
    io.open(HDR, "w", encoding="utf-8", newline="\n").write(h.replace(anchor, "\n".join(lines_for_header()) + anchor, 1))
    print("field_accessors.hpp  %d getters, %d addresses, %d copies"
          % (len(GETTERS), len(ADDRESSES), len(COPIES)))

    t = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    a = '    return check::finish("boxacc");'
    assert a in t, "the boxacc finish anchor was missing"
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(t.replace(a, "\n".join(lines_for_test()), 1))
    print("test_boxacc.cpp      fourth batch of checks")

    s = io.open(TOOLCHAIN, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    anchor2 = "    0x5C5F50,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment"
    assert anchor2 in s, "the identity anchor was not found"
    s = s.replace(anchor2, anchor2 + "\n" + "    0x%X,  # mov rax, rcx ; ret -- returns its own argument" % IDENTITY[0], 1)
    marker = "IMPLEMENTED = {"
    all_rvas = [g[1] for g in GETTERS] + [a2[1] for a2 in ADDRESSES] + [c[1] for c in COPIES]
    entry = "    " + ", ".join("0x%X" % r for r in all_rvas) + ",   # batch four, lcns/field_accessors.hpp"
    s = s.replace(marker, marker + "\n" + entry, 1)
    io.open(TOOLCHAIN, "w", encoding="utf-8", newline="\n").write(s)
    print("g_toolchain.py       %d functions registered as implemented" % len(all_rvas))
    print("")
    print("done")


if __name__ == "__main__":
    main()
