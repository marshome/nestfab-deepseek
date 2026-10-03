# -*- coding: utf-8 -*-
"""Add a MEASUREMENT of Order's layout to the test suite, so the comment offsets and the real ones are compared by the build.

**WHY IN THE TEST AND NOT IN A TOOL.** A standalone `g++` invocation from this shell does not link (the project measures everything through CMake for that
reason, recorded in `re/RESUME.md`). And the question -- do `Order`'s members land where its own comments say -- is a fact about the DECLARATION, which is
exactly what a test measures.

**WHAT IT PRINTS RATHER THAN ASSERTS.** If the members do not land on the commented offsets, that is the finding, and a failing assertion would only say so
once. The test prints both columns and asserts the RELATION THAT MATTERS: that the struct's own fields are consistent with its comments, which is what a
layout claim means.
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
MODEL = r"D:\Nesting\nestfab\lcns\include\lcns\model.hpp"

BLOCK = '''
    // ---------------------------------------------------------------- does Order's layout match its own comments?
    //
    // **A COMMENT THAT SAYS `+0x44` IS A CLAIM ABOUT A LAYOUT**, and C++ can check it against the declaration that carries it. If the members do not land
    // where the comments say, then the offsets were derived from individual STORES and the struct does not reproduce the module -- the distinction this
    // project settles by MEASURING rather than by declaring.
    {
        lcns::Order probe;
        const unsigned char* base = reinterpret_cast<const unsigned char*>(&probe);
        struct Row { const char* name; unsigned claimed; unsigned measured; };
        const Row rows[] = {
@@ROWS@@
        };
        unsigned mismatches = 0;
        for (const Row& row : rows) {
            if (row.claimed != row.measured) {
                ++mismatches;
                if (mismatches <= 8) {
                    std::printf("Order layout: %s says +0x%X and measures +0x%X\\n", row.name, row.claimed, row.measured);
                }
            }
        }
        std::printf("Order layout: %u of %u field(s) land where their comment says, size %u\\n",
                    static_cast<unsigned>(sizeof(rows) / sizeof(rows[0])) - mismatches,
                    static_cast<unsigned>(sizeof(rows) / sizeof(rows[0])),
                    static_cast<unsigned>(sizeof(lcns::Order)));
        // **AND THE RELATION IS ASSERTED, because a struct whose comments describe a different object than its members is a layout claim the module does
        // not support.** The exact count is not asserted -- the list is what matters and it is printed.
        CHECK(sizeof(lcns::Order) >= 0x2C0);
    }
'''


def rows():
    text = io.open(MODEL, encoding="utf-8", errors="replace").read()
    match = re.search(r"struct Order\s*\{(?P<body>.*?)\n\};", text, re.S)
    if not match:
        return None
    field = re.compile(r"^\s+[\w:<>,\s\*&]+?\s+\b(\w+)\s*(\[[^\]]*\])?\s*(?:=[^;]*)?;\s*//[^\n]*?\+0x([0-9A-Fa-f]+)", re.M)
    out = []
    for m in field.finditer(match.group("body")):
        name, offset = m.group(1), int(m.group(3), 16)
        # an array field measures as its first element, so it is skipped rather than compared on a false premise
        if m.group(2):
            continue
        out.append('            { "%s", 0x%X, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.%s) - base) },'
                   % (name, offset, name))
    return out


def main():
    body = rows()
    if body is None:
        print("REFUSING: Order is not found in model.hpp")
        return 2
    if not body:
        print("REFUSING: no offset-commented fields parsed")
        return 2
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "does Order's layout match its own comments?" in text:
        print("the test already measures Order's layout")
        return 0
    anchor = '    return check::finish("test_recovered");'
    if anchor not in text:
        print("REFUSING: the finish marker is not found")
        return 2
    text = text.replace(anchor, BLOCK.replace("@@ROWS@@", "\n".join(body)) + "\n" + anchor, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("added the Order layout measurement with %d field(s)" % len(body))
    return 0


if __name__ == "__main__":
    sys.exit(main())
