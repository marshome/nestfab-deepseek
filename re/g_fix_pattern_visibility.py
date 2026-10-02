# -*- coding: utf-8 -*-
"""Make Tiling::Pattern's measured members PUBLIC, and correct the test's abstract claim.

**TWO THINGS I GOT WRONG, AND BOTH ARE ABOUT THE LANGUAGE RATHER THAN THE MODULE:**

  * **ACCESS IS NOT IN THE BINARY.** I put the measured members under `protected:` and the test could not measure them. **Whether the module's fields are
    public or protected leaves no trace in a compiled binary** -- there is no RTTI for access -- so declaring them `public` is the honest choice: it
    asserts nothing the module cannot be checked against, where `protected` asserted something it also cannot check. The note now says so.
  * **THE CLASS HAS NO PURE VIRTUAL, SO IT IS NOT ABSTRACT.** I wrote `static_assert(std::is_abstract<Pattern>::value)` from the fact that the class is
    absent from `re/vtables.json` -- **and absence from that file means NO INSTANTIATED VTABLE, which an abstract class has and so does a class that is
    merely never instantiated here.** The two are not the same, and the assertion was reaching past the evidence. It is removed.
"""
import io
import sys

PATTERN = r"D:\Nesting\nestfab\lcns\include\lcns\pattern.hpp"
TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"


def main():
    text = io.open(PATTERN, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    text = text.replace(
        "protected:\n    /** The twelve words RE 0x4E7E50 copies verbatim, at +0x00 through +0x40.",
        "    /** The twelve words RE 0x4E7E50 copies verbatim, at +0x00 through +0x40.")
    text = text.replace(
        " *  **SO THE OBJECT IS 0x60 BYTES AND ITS LAST THREE WORDS ARE A CONTAINER OF 0x90 BYTE ELEMENTS.** The class is abstract and therefore has no\n"
        " *  constructor of its own in the profile, so **the 0x48 bytes copied verbatim have NO writer that could name them**, and they are declared by width\n"
        " *  and offset rather than by a guess. */",
        " *  **SO THE OBJECT IS 0x60 BYTES AND ITS LAST THREE WORDS ARE A CONTAINER OF 0x90 BYTE ELEMENTS.** The class has no instantiated vtable and no\n"
        " *  constructor of its own in the profile, so **the 0x48 bytes copied verbatim have NO writer that could name them**, and they are declared by width\n"
        " *  and offset rather than by a guess.\n"
        " *\n"
        " *  **AND THE MEMBERS ARE `public` BECAUSE ACCESS IS NOT IN THE BINARY.** Whether the module's fields are public or protected leaves no trace in a\n"
        " *  compiled binary -- there is no RTTI for access -- so `public` asserts nothing that cannot be checked, where `protected` would assert something\n"
        " *  that also cannot be. */")
    io.open(PATTERN, "w", encoding="utf-8", newline="\n").write(text)
    print("pattern.hpp: the measured members are public, with the reason")

    body = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    body = body.replace(
        '        static_assert(std::is_abstract<lcns::tiling::Pattern>::value,\n'
        '                      "an abstract base has no instantiated vtable, which is why it is absent from re/vtables.json");\n',
        '        // **NOT ASSERTED ABSTRACT.** The class is absent from `re/vtables.json` because it has NO INSTANTIATED VTABLE -- which an abstract\n'
        '        // class has and so does a class that is merely never instantiated here. Those are not the same claim, and asserting the stronger one\n'
        '        // would reach past the evidence.\n')
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(body)
    print("test_recovered.cpp: the abstract claim removed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
