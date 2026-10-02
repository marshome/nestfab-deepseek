# -*- coding: utf-8 -*-
"""Second batch of accessors, plus the identity helpers classified as library.

Read in round 513 from the LaunchLocalComputation closure:

    0x4F7380  mov [rcx+0x6A], dl     ; byte setter
    0x4F8360  mov eax, [rcx+0x20]    ; dword getter
    0x4F8CD0  mov eax, [rcx+0x64]    ; dword getter
    0x4F7060  mov eax, [rcx+0x24]    ; dword getter
    0x4F76D0  mov eax, [rcx+0x6C]    ; dword getter
    0x52F8D0  mov [rcx+0x20], dl     ; byte setter
    0x52F8E0  mov [rcx+0x21], dl     ; byte setter

and five that are `mov rax, rcx ; ret`, which return their own argument:

    0x4F7030, 0x4F8350, 0x547610, 0x5C5F30, 0x5C5F50

The five touch nothing and compute nothing, so they are pointer adjustments rather than domain logic and join the library
set. The seven accessors join the header and the registry of implemented functions.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "field_accessors.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")

NEW = [
    ("setByte6A_4F7380", 0x4F7380, "set", 0x6A, 1),
    ("getDword20_4F8360", 0x4F8360, "get", 0x20, 4),
    ("getDword64_4F8CD0", 0x4F8CD0, "get", 0x64, 4),
    ("getDword24_4F7060", 0x4F7060, "get", 0x24, 4),
    ("getDword6C_4F76D0", 0x4F76D0, "get", 0x6C, 4),
    ("setByte20_52F8D0", 0x52F8D0, "set", 0x20, 1),
    ("setByte21_52F8E0", 0x52F8E0, "set", 0x21, 1),
]

IDENTITY = [0x4F7030, 0x4F8350, 0x547610, 0x5C5F30, 0x5C5F50]


def accessor_lines():
    out = []
    for name, rva, access, offset, width in NEW:
        if access == "get":
            out.append("/** RE 0x%X: reads the %d-bit field at +0x%02X. */" % (rva, width * 8, offset))
            out.append("inline std::uint%d_t %s(const void* object) {" % (width * 8, name))
            out.append("    std::uint%d_t value = 0;" % (width * 8))
            out.append("    std::memcpy(&value, static_cast<const unsigned char*>(object) + 0x%02X, sizeof(value));" % offset)
            out.append("    return value;")
        else:
            out.append("/** RE 0x%X: writes the %d-bit field at +0x%02X and nothing else. */" % (rva, width * 8, offset))
            out.append("inline void %s(void* object, std::uint%d_t value) {" % (name, width * 8))
            out.append("    std::memcpy(static_cast<unsigned char*>(object) + 0x%02X, &value, sizeof(value));" % offset)
        out.append("}")
        out.append("")
    return out


def test_lines():
    out = ["    // ------------------- field accessors, second batch"]
    out.append("    {")
    out.append("        unsigned char object[0x80];")
    out.append("        std::memset(object, 0xA5, sizeof(object));")
    for name, rva, access, offset, width in NEW:
        if access == "set":
            out.append("        lcns::dll::accessors::%s(object, 0x%02X);   // RE 0x%X" % (name, 0x5A if width == 1 else 0x12345678, rva))
            out.append("        {")
            out.append("            std::uint%d_t got = 0;" % (width * 8))
            out.append("            std::memcpy(&got, object + 0x%02X, sizeof(got));" % offset)
            out.append("            CHECK(got == 0x%02X);" % (0x5A if width == 1 else 0x12345678))
            out.append("        }")
        else:
            out.append("        {")
            out.append("            const std::uint%d_t put = 0x%02X;" % (width * 8, 0x5A if width == 1 else 0x12345678))
            out.append("            std::memcpy(object + 0x%02X, &put, sizeof(put));" % offset)
            out.append("            CHECK(lcns::dll::accessors::%s(object) == put);   // RE 0x%X" % (name, rva))
            out.append("        }")
    out.append("    }")
    out.append("")
    out.append('    return check::finish("boxacc");')
    return out


def main():
    h = io.open(HDR, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    anchor = "}  // namespace accessors"
    assert anchor in h, "the accessors namespace close was not found"
    h = h.replace(anchor, "\n".join(accessor_lines()) + anchor, 1)
    io.open(HDR, "w", encoding="utf-8", newline="\n").write(h)
    print("field_accessors.hpp  %d more accessors" % len(NEW))

    t = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    a = '    return check::finish("boxacc");'
    assert a in t, "the boxacc finish anchor was missing"
    t = t.replace(a, "\n".join(test_lines()), 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(t)
    print("test_boxacc.cpp      second batch of checks")

    s = io.open(TOOLCHAIN, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    anchor2 = "    0xD59A0,  # xor eax, eax ; ret -- a default override returning zero"
    assert anchor2 in s, "the boilerplate anchor was not found"
    lines = [anchor2] + ["    0x%X,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment" % r for r in IDENTITY]
    s = s.replace(anchor2, "\n".join(lines), 1)
    marker = "IMPLEMENTED = {"
    assert marker in s, "the implemented registry was not found"
    entry = "    " + ", ".join("0x%X" % n[1] for n in NEW) + ",   # batch two, lcns/field_accessors.hpp"
    s = s.replace(marker, marker + "\n" + entry, 1)
    io.open(TOOLCHAIN, "w", encoding="utf-8", newline="\n").write(s)
    print("g_toolchain.py       %d identity helpers classified, %d accessors registered" % (len(IDENTITY), len(NEW)))
    print("")
    print("done")


if __name__ == "__main__":
    main()
