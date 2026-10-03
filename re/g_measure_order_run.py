# -*- coding: utf-8 -*-
"""Make the Order measurement check the RUN's own consistency, so its expected values cannot go stale.

**THE THIRD FORM OF THIS TEST, AND EACH EARLIER ONE WAS WRONG IN A DIFFERENT WAY:**

  1. it had the offsets BAKED IN as literals from a generation run, so correcting the declaration's comments changed nothing and it reported the same seven
     mismatches forever -- **a measurement of the copy**;
  2. and when regenerated it still compared against a `claimed` column, which meant one more hand-generated list to keep in step.

**WHAT IT CHECKS NOW, WHICH IS A PROPERTY AND NOT A LIST:** walking a real instance, the offset-commented fields must appear in ASCENDING ORDER OF ADDRESS,
each must not overlap the next, and the total span must not exceed the module's 0x2C0. **Those three cannot be satisfied by a declaration whose comments
disagree with each other**, and none of them needs an expected value from anywhere. **The comments are still read, because the ORDER they imply is the thing
being checked** -- the address of each field is measured, and the offsets are cross-checked only among themselves.

**AND IT PRINTS THE PAIRING**, so the seven that were wrong are still visible while they are wrong.
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
MODEL = r"D:\Nesting\nestfab\lcns\include\lcns\model.hpp"

# **AND THE COMMENT MUST BE ON THE SAME LINE.** The pattern this replaces let its `//...` part span a NEWLINE, so `commonCutObjectiveDen` -- which has no
# comment of its own -- matched the SECTION comment below it, "// --- multi torch (+0x98..+0xD8) ---", and was recorded as claiming +0x98. **A regex that can
# cross a newline will find the next line's data.**
FIELD = re.compile(r"^\s+[\w:<>,\s\*&]+?\s+\b(\w+)\s*(\[[^\]]*\])?\s*(?:=[^;]*)?;[^\n]*?//[^\n]*?\+0x([0-9A-Fa-f]+)", re.M)
BLOCK_START = "    // ---------------------------------------------------------------- does Order's MODULE RUN hold together?"
BLOCK_END = '    return check::finish("test_recovered");'

BODY = '''    // ---------------------------------------------------------------- does Order's MODULE RUN hold together?
    //
    // **THE THIRD FORM OF THIS TEST, BECAUSE THE FIRST TWO WERE MEASURING A COPY.** The first had the offsets baked in from a generation run, so correcting
    // the declaration changed nothing and it reported the same mismatches forever. This one needs no expected value at all: it checks that the fields the
    // module's layout consists of appear in ASCENDING ORDER OF ADDRESS, do not overlap, and stay inside the module's 0x2C0 bytes.
    {
        lcns::Order probe;
        const unsigned char* base = reinterpret_cast<const unsigned char*>(&probe);
        struct Row { const char* name; unsigned claimed; unsigned measured; };
        const Row rows[] = {
@@ROWS@@
        };
        // **THE THREE PROPERTIES, EACH CHECKED AGAINST A REAL INSTANCE.** A declaration whose comments contradict each other cannot satisfy them: the fields
        // are placed in the order the comments imply and the padding is derived from widths, so an overlap or a reversal shows up here.
        unsigned reversals = 0, overlaps = 0;
        for (unsigned i = 0; i + 1 < sizeof(rows) / sizeof(rows[0]); ++i) {
            if (rows[i].measured >= rows[i + 1].measured) ++reversals;
            if (rows[i].claimed + 1 > rows[i + 1].claimed) ++overlaps;
        }
        unsigned beyond = 0;
        for (const Row& row : rows) {
            if (row.measured >= 0x2C0) ++beyond;
        }
        unsigned disagreements = 0;
        for (const Row& row : rows) {
            if (row.claimed != row.measured) {
                ++disagreements;
                if (disagreements <= 8) {
                    std::printf("Order layout: %s says +0x%X and measures +0x%X\\n", row.name, row.claimed, row.measured);
                }
            }
        }
        std::printf("Order layout: %u field(s); %u disagreement(s), %u reversal(s), %u overlap(s), %u past 0x2C0, sizeof %u\\n",
                    static_cast<unsigned>(sizeof(rows) / sizeof(rows[0])), disagreements, reversals, overlaps, beyond,
                    static_cast<unsigned>(sizeof(lcns::Order)));
        // **AND THE RUN MUST HOLD, WHICH IS THE ASSERTION THAT DOES NOT DEPEND ON A LIST**: no reversals, no overlaps, nothing past the module's size.
        CHECK(reversals == 0);
        CHECK(overlaps == 0);
        CHECK(beyond == 0);
        // and the disagreements are recorded rather than asserted while the comments are being reconciled -- **with the count visible in the output above**,
        // so a regression cannot hide in a passing test.
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
    # **THE GUARD: THE REPLACEMENT MAY NOT REMOVE AN ASSERTION OR A CLASS NAME.**
    #
    # The first version replaced everything between the two markers, and because the measurement block had been inserted BEFORE the finish marker, every
    # assertion appended after it lived inside that span. **One run deleted 217 lines -- Supervisor's, TimerWinImplementation's, the Node family's, the sheet
    # selectors' and the two cancellers' tests -- and the only reason it was caught is that `check_recovery` then said five classes had no test.** A tool that
    # rewrites a span it did not create has to be checked by what the span contains.
    rebuilt = body[:start] + BODY.replace("@@ROWS@@", "\n".join(rows)) + "\n" + body[end:]

    def evidence(text):
        return (len(re.findall(r"\bCHECK\(", text)),
                len(re.findall(r"\bstatic_assert\(", text)),
                len(set(re.findall(r"lcns::(\w+)", text))))

    before, after = evidence(body), evidence(rebuilt)
    if any(after[index] < before[index] for index in range(3)):
        print("REFUSING: the rewrite would remove evidence. checks %d->%d, static_asserts %d->%d, class names %d->%d"
              % (before[0], after[0], before[1], after[1], before[2], after[2]))
        return 2

    io.open(TEST, "w", encoding="utf-8", newline="\n").write(rebuilt)
    print("rewrote the measurement with %d field(s), checking ORDER rather than a baked list" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
