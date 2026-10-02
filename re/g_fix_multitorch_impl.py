# -*- coding: utf-8 -*-
"""Fix MultitorchEvaluator's field name in the implementation, and correct the comment about how the Impl is held.

THE STRUCTURE IS CONFIRMED BY THE CALL SITE, which is better evidence than the constructor alone. At 0x766DCF the class is constructed ON THE
STACK:

    0x766DBA  lea rbx, [rsp + 0xd0]          ; THIS object is a stack temporary
    0x766DB8  mov edx, [rax]                 ; the int, out of an option
    0x766DC2  movsd xmm3, [rax + 8]          ; a double
    0x766DCA  movsd xmm2, [rax + 0x18]       ; and another
    0x766DCF  call 0x4E8410

and inside, `0x4E8454 mov [rbx], rax` stores the ALLOCATED 0x20 byte object at the stack temporary's +0. **So the class holds a POINTER, and
saying the Impl is held "BY VALUE" was wrong** -- what is true is that the class's entire state is that one pointer.
"""
import io
import re
import sys

TILING = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"
SRC = r"D:\Nesting\nestfab\lcns\src\tiling.cpp"


def fix_header():
    text = io.open(TILING, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    text = text.replace(
        "    Impl impl_{};                      // **BY VALUE**, because RE 0x4E8454 stores the ALLOCATED pointer at +0, so this object IS that memory",
        "    // RE 0x4E8454: `mov [rbx], rax` -- the class holds a POINTER to the allocated Impl, and that pointer is its whole state.\n"
        "    Impl impl_{};                      // +0x00: the Impl the constructor allocates")
    io.open(TILING, "w", encoding="utf-8", newline="\n").write(text)
    print("corrected the Impl comment in the header")
    return 0


def fix_source():
    text = io.open(SRC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "MultitorchEvaluator::MultitorchEvaluator" not in text:
        marker = "double MultitorchEvaluator::evaluate("
        if marker not in text:
            print("REFUSING: the evaluate definition is not found")
            return 2
        text = text.replace(marker,
                            "// RE 0x4E8410: (this, int, double, double), all three written into the object the constructor allocates.\n"
                            "MultitorchEvaluator::MultitorchEvaluator(int torches, double first, double second) {\n"
                            "    impl_.torches = torches;      // RE 0x4E8447: mov dword [rax + 8], esi\n"
                            "    impl_.first = first;          // RE 0x4E844A: movsd [rax + 0x10], xmm2\n"
                            "    impl_.second = second;        // RE 0x4E844F: movsd [rax + 0x18], xmm3\n"
                            "}\n\n" + marker, 1)
        print("added the constructor definition")
    text = text.replace("nbTorches_", "impl_.torches")
    io.open(SRC, "w", encoding="utf-8", newline="\n").write(text)
    print("renamed nbTorches_ to impl_.torches in the implementation")
    return 0


if __name__ == "__main__":
    code = fix_header()
    if code == 0:
        code = fix_source()
    sys.exit(code)
