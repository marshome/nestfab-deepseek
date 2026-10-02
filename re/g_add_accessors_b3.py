# -*- coding: utf-8 -*-
"""Accessor batch three: nine more accessors, five more identity helpers.

Read in round 514 from the LaunchLocalComputation closure, all four bytes each:

    0x54D100  movzx eax, [rcx]       ; byte getter at +0x00
    0x5C4CD0  movzx eax, [rcx]       ; byte getter at +0x00, another object
    0x4F7050  mov eax, [rcx+0x24]    ; dword getter
    0x4FC1D0  mov rax, [rcx]         ; pointer getter at +0x00
    0x5FC7E0  mov rax, [rcx]         ; pointer getter at +0x00
    0x4FC200  mov rax, [rcx]         ; pointer getter at +0x00
    0x4F8C70  mov [rcx+0x60], edx    ; dword setter
    0x4F76B0  mov [rcx+0x20], edx    ; dword setter
    0x548390  mov eax, [rcx+0x20]    ; dword getter

and five more `mov rax, rcx ; ret`: 0x5C61D0, 0x5C5260, 0x548630, 0x5C61E0, 0x548380.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "field_accessors.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")
TOOLCHAIN = os.path.join(ROOT, "re", "g_toolchain.py")

NEW = [
    ("getByte00_54D100", 0x54D100, "get", 0x00, 1),
    ("getByte00_5C4CD0", 0x5C4CD0, "get", 0x00, 1),
    ("getDword24_4F7050", 0x4F7050, "get", 0x24, 4),
    ("getPtr00_4FC1D0", 0x4FC1D0, "get", 0x00, 8),
    ("getPtr00_5FC7E0", 0x5FC7E0, "get", 0x00, 8),
    ("getPtr00_4FC200", 0x4FC200, "get", 0x00, 8),
    ("setDword60_4F8C70", 0x4F8C70, "set", 0x60, 4),
    ("setDword20_4F76B0", 0x4F76B0, "set", 0x20, 4),
    ("getDword20_548390", 0x548390, "get", 0x20, 4),
]

IDENTITY = [0x5C61D0, 0x5C5260, 0x548630, 0x5C61E0, 0x548380]


def accessor_lines():
    out = []
    for name, rva, access, offset, width in NEW:
        bits = width * 8
        if access == "get":
            out.append("/** RE 0x%X: reads the %d-bit value at +0x%02X. */" % (rva, bits, offset))
            out.append("inline std::uint%d_t %s(const void* object) {" % (bits, name))
            out.append("    std::uint%d_t value = 0;" % bits)
            out.append("    std::memcpy(&value, static_cast<const unsigned char*>(object) + 0x%02X, sizeof(value));" % offset)
            out.append("    return value;")
        else:
            out.append("/** RE 0x%X: writes the %d-bit value at +0x%02X and nothing else. */" % (rva, bits, offset))
            out.append("inline void %s(void* object, std::uint%d_t value) {" % (name, bits))
            out.append("    std::memcpy(static_cast<unsigned char*>(object) + 0x%02X, &value, sizeof(value));" % offset)
        out.append("}")
        out.append("")
    return out


def test_lines():
    out = ["    // ------------------- field accessors, third batch"]
    out.append("    {")
    out.append("        unsigned char object[0x80];")
    out.append("        std::memset(object, 0xA5, sizeof(object));")
    for name, rva, access, offset, width in NEW:
        bits = width * 8
        probe = {1: 0x5A, 4: 0x12345678, 8: 0x1122334455667788}[width]
        if access == "set":
            out.append("        lcns::dll::accessors::%s(object, 0x%Xull);   // RE 0x%X" % (name, probe, rva))
            out.append("        {")
            out.append("            std::uint%d_t got = 0;" % bits)
            out.append("            std::memcpy(&got, object + 0x%02X, sizeof(got));" % offset)
            out.append("            CHECK(got == 0x%Xull);" % probe)
            out.append("        }")
        else:
            out.append("        {")
            out.append("            const std::uint%d_t put = 0x%Xull;" % (bits, probe))
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
    io.open(HDR, "w", encoding="utf-8", newline="\n").write(h.replace(anchor, "\n".join(accessor_lines()) + anchor, 1))
    print("field_accessors.hpp  %d more accessors" % len(NEW))

    t = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    a = '    return check::finish("boxacc");'
    assert a in t, "the boxacc finish anchor was missing"
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(t.replace(a, "\n".join(test_lines()), 1))
    print("test_boxacc.cpp      third batch of checks")

    s = io.open(TOOLCHAIN, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    anchor2 = "    0x4F7030,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment"
    assert anchor2 in s, "the identity anchor was not found"
    lines = [anchor2] + ["    0x%X,  # mov rax, rcx ; ret -- returns its own argument, a pointer adjustment" % r for r in IDENTITY]
    s = s.replace(anchor2, "\n".join(lines), 1)
    marker = "IMPLEMENTED = {"
    entry = "    " + ", ".join("0x%X" % n[1] for n in NEW) + ",   # batch three, lcns/field_accessors.hpp"
    s = s.replace(marker, marker + "\n" + entry, 1)
    io.open(TOOLCHAIN, "w", encoding="utf-8", newline="\n").write(s)
    print("g_toolchain.py       %d identity helpers classified, %d accessors registered" % (len(IDENTITY), len(NEW)))
    print("")
    print("done")


if __name__ == "__main__":
    main()
