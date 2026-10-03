# -*- coding: utf-8 -*-
"""Rebuild the Order measurement so its CLAIMED column comes from the DECLARATION rather than from a list baked in when the test was generated.

**THE MEASUREMENT WAS BAKED AND BECAME A LIE.** `re/g_test_order_layout.py` read the offsets out of `model.hpp` when it ran and wrote them into the test as
literals -- so after the comments were corrected, the test still compared the fields against the OLD offsets and reported `41 of 48`, and it would keep
reporting that no matter how right the declaration became. **A measurement whose expected value is a copy taken once is a measurement of the copy.**

**SO IT IS REGENERATED HERE, WITH THE CORRECTED COMMENTS**, and the same tool can regenerate it again after any change. And what it asserts is only what covers
every row: that none of them disagrees, once the tool has placed them.
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
MODEL = r"D:\Nesting\nestfab\lcns\include\lcns\model.hpp"

FIELD = re.compile(r"^\s+[\w:<>,\s\*&]+?\s+\b(\w+)\s*(\[[^\]]*\])?\s*(?:=[^;]*)?;\s*//[^\n]*?\+0x([0-9A-Fa-f]+)", re.M)
BLOCK_START = "    // ---------------------------------------------------------------- does Order's layout match its own comments?"
BLOCK_END = '    return check::finish("test_recovered");'

BODY = '''    // ---------------------------------------------------------------- does Order's layout match its own comments?
    //
    // **A COMMENT THAT SAYS `+0x44` IS A CLAIM ABOUT A LAYOUT**, and C++ can check it against the declaration that carries it. **AND THE CLAIMED COLUMN
    // COMES FROM THE DECLARATION, because the first version of this test had the offsets baked in from a generation run -- so it kept comparing against
    // the OLD offsets after the comments were corrected and reported a mismatch that no longer existed.** Regenerate with `python -u re/g_test_order_layout.py`.
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
        // **AND EVERY ROW MUST AGREE, WHICH IS THE ASSERTION THE WHOLE EXERCISE IS FOR.** An earlier version asserted a constant shift after seeing three
        // rows that looked like one, and the measurement refuted it: **a pattern seen in three examples is not a pattern.**
        CHECK(mismatches == 0);
        std::printf("Order layout: sizeof(Order) = %u, the module's object = 0x2C0 = %u\\n",
                    static_cast<unsigned>(sizeof(lcns::Order)), 0x2C0u);
    }
'''


def main():
    text = io.open(MODEL, encoding="utf-8", errors="replace").read()
    match = re.search(r"struct Order\s*\{(?P<body>.*?)\n\};", text, re.S)
    if not match:
        print("REFUSING: Order is not found")
        return 2
    rows = []
    for found in FIELD.finditer(match.group("body")):
        name, array, offset = found.group(1), found.group(2), int(found.group(3), 16)
        if array:
            continue
        rows.append('            { "%s", 0x%X, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.%s) - base) },'
                    % (name, offset, name))
    if not rows:
        print("REFUSING: no offset-commented fields parsed")
        return 2

    body = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start, end = body.find(BLOCK_START), body.find(BLOCK_END)
    if start < 0 or end < 0:
        print("REFUSING: the measurement block is not where expected")
        return 2
    body = body[:start] + BODY.replace("@@ROWS@@", "\n".join(rows)) + "\n" + body[end:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(body)
    print("regenerated the measurement with %d field(s) from the corrected declaration" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
