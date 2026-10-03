# -*- coding: utf-8 -*-
"""Declare the module's three node classes IN ONE PASS, laid out at the offsets their accessors read, and replace the port's tagged BeamNode.

**THE MEASUREMENT, WHICH IS FOUR INSTRUCTIONS AND TWO TYPEINFO CHAINS:**

    Multi::TerminalNode   0xA3B570   4 slots   slot 2: `movsd xmm0, [rcx + 0x48] / ret`
                                                slot 3: `movsd xmm0, [rcx + 0x50] / ret`
    Multi::SplitNode      0xA3BB70   4 slots   slot 2: `movsd xmm0, [rcx + 0x50] / ret`
                                                slot 3: `movsd xmm0, [rcx + 0x58] / ret`
    both derive from `Multi::Node`, and no function in the profile installs either vtable.

**SO**: the base has `value()` reading +0x48 and a default `secondary()`; `TerminalNode` supplies `secondary()` at +0x50; **`SplitNode` overrides `value()` to
read +0x50 as well** and supplies `secondary()` at +0x58. **The two tables put the SAME offset +0x50 in DIFFERENT SLOTS**, which is precisely what the port's
`enum class Kind` with a conditional could not express -- and the module has no `Kind` field anywhere.

**AND THE LAYOUT IS MEASURED RATHER THAN ARRANGED**: the first attempt put the three doubles at +8, +0x10 and +0x18, because a vptr and three doubles is
sixteen bytes; the module's are sixty-four bytes further in, so **+0x08..+0x47 is a region no accessor reads and no recovered function writes**. It is explicit
`std::byte` padding, because a name needs an oracle and none of the module's strings, setters or accessors names it.

    python -u g_layout_node_family.py
"""
import io
import sys

NESTER = r"D:\Nesting\nestfab\lcns\include\lcns\nester.hpp"
TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD_BEAMNODE = '''struct BeamNode {
    enum class Kind { Terminal, Split };
    Kind kind = Kind::Terminal;
    double value48 = 0.0;  // TerminalNode: `movsd xmm0,[rcx+0x48]`
    double value50 = 0.0;  // SplitNode:     `movsd xmm0,[rcx+0x50]`
    int depth = 0;
    int sheetIndex = 0;
    Nesting partial;
    double eval() const { return kind == Kind::Terminal ? value48 : value50; }
};'''

NEW_FAMILY = '''/** **THE THREE CLASSES THE MODULE HAS, WHICH THE PORT HAD FLATTENED INTO ONE.** The vtables and the bodies of their slots:

 *      Multi::TerminalNode   0xA3B570   4 slots   slot 2: `movsd xmm0, [rcx + 0x48] / ret`
 *                                                 slot 3: `movsd xmm0, [rcx + 0x50] / ret`
 *      Multi::SplitNode      0xA3BB70   4 slots   slot 2: `movsd xmm0, [rcx + 0x50] / ret`
 *                                                 slot 3: `movsd xmm0, [rcx + 0x58] / ret`
 *
 *  and both derive from `Multi::Node` by their typeinfo chains. **So `value()` reads +0x48 in the base, `secondary()` is the slot each class supplies, and
 *  `SplitNode` OVERRIDES `value()` as well** -- **the same offset +0x50 sits in a DIFFERENT SLOT in the two tables**, which is what a `Kind` tag with a
 *  conditional could not say, and the module has no `Kind` field anywhere.
 *
 *  **AND +0x08..+0x47 IS A REGION NO ACCESSOR READS.** The three doubles are at +0x48, +0x50 and +0x58, while a vptr and three doubles is sixteen bytes, so
 *  sixty-four bytes sit between them that no recovered function reads or writes. **They are explicit `std::byte` padding rather than named fields, because a
 *  name needs an oracle and none of the module's strings, setters or accessors names them.**
 *
 *  **AND THE ACCESSORS KEEP NEUTRAL NAMES FOR THE SAME REASON**: the module exposes them through vtable slots 2 and 3 and never names what they return. No
 *  function in the profile installs either vtable, so there is no constructor to initialise these and the members are public rather than protected. */
class Node {
public:
    virtual ~Node() = default;

    /** RE `movsd xmm0, [rcx + 0x48]`: `TerminalNode`'s slot 2, and what `SplitNode` overrides with +0x50. */
    virtual double value() const { return value48; }
    /** RE slot 3 of both tables: +0x50 in `TerminalNode` and +0x58 in `SplitNode`, so the base supplies only a default. */
    virtual double secondary() const { return 0.0; }

    std::byte reserved08[0x40];                              // +0x08..+0x47: **NO ACCESSOR READS THIS**, so it is padded rather than named
    double value48 = 0.0;                                    // +0x48
};

/** RE 0xA3B570. Four slots: the destructor pair, `value()` at slot 2 reading **+0x48** (inherited), and `secondary()` at slot 3 reading **+0x50**. */
class TerminalNode : public Node {
public:
    double secondary() const override { return value50; }     // RE 0x97500: movsd xmm0, [rcx + 0x50]

    double value50 = 0.0;                                     // +0x50
};

/** RE 0xA3BB70. Four slots: the destructor pair, `value()` at slot 2 reading **+0x50** -- an OVERRIDE, where `TerminalNode` inherits -- and `secondary()` at
 *  slot 3 reading **+0x58**. */
class SplitNode : public Node {
public:
    double value() const override { return value50; }         // RE 0x97510: movsd xmm0, [rcx + 0x50]
    double secondary() const override { return value58; }     // RE 0x97520: movsd xmm0, [rcx + 0x58]

    double value50 = 0.0;                                     // +0x50
    double value58 = 0.0;                                     // +0x58
};'''

OLD_TEST = """        BeamNode b_beamnode;
        CHECK(b_beamnode.value48 == 0.0);
        CHECK(b_beamnode.value50 == 0.0);
        CHECK(b_beamnode.depth == 0);
        CHECK(b_beamnode.sheetIndex == 0);"""

NEW_TEST = """        // **THE THREE CLASSES THE MODULE HAS, DRIVEN THROUGH THE BASE POINTER.** RE 0xA3B570 (TerminalNode) and 0xA3BB70 (SplitNode) are two four slot
        // tables whose slots 2 and 3 each read a double at a fixed offset -- so what the test has to show is that THE SAME CALL REACHES DIFFERENT OFFSETS,
        // which a `Kind` tag and a conditional cannot express.
        lcns::TerminalNode terminal;
        lcns::SplitNode split;
        terminal.value48 = 1.5;      // +0x48, TerminalNode slot 2: movsd xmm0, [rcx + 0x48]
        terminal.value50 = 2.5;      // +0x50, TerminalNode slot 3
        split.value50 = 3.5;         // +0x50, SplitNode slot 2 -- THE SAME OFFSET, A DIFFERENT SLOT
        split.value58 = 4.5;         // +0x58, SplitNode slot 3

        lcns::Node* as_base = &terminal;
        CHECK(as_base->value() == 1.5);        // the base's slot 2 reads +0x48 through TerminalNode
        CHECK(as_base->secondary() == 2.5);    // and TerminalNode's slot 3 override reads +0x50
        as_base = &split;
        CHECK(as_base->value() == 3.5);        // SplitNode OVERRIDES value(), reading +0x50 in ITS table
        CHECK(as_base->secondary() == 4.5);    // and adds +0x58

        // **AND THE OFFSETS, WHICH IS WHAT MAKES THE FOUR NUMBERS ABOVE A LAYOUT.** The first declaration of these classes put the doubles at +8, +0x10 and
        // +0x18, and these four lines are what caught it.
        CHECK(reinterpret_cast<const unsigned char*>(&terminal.value48) - reinterpret_cast<const unsigned char*>(&terminal) == 0x48);
        CHECK(reinterpret_cast<const unsigned char*>(&terminal.value50) - reinterpret_cast<const unsigned char*>(&terminal) == 0x50);
        CHECK(reinterpret_cast<const unsigned char*>(&split.value50) - reinterpret_cast<const unsigned char*>(&split) == 0x50);
        CHECK(reinterpret_cast<const unsigned char*>(&split.value58) - reinterpret_cast<const unsigned char*>(&split) == 0x58);"""


def main():
    text = io.open(NESTER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "class TerminalNode" in text:
        print("the family is already declared")
        return 0
    if OLD_BEAMNODE not in text:
        print("REFUSING: BeamNode is not as expected")
        return 2
    text = text.replace(OLD_BEAMNODE, NEW_FAMILY, 1)
    io.open(NESTER, "w", encoding="utf-8", newline="\n").write(text)
    print("nester.hpp: declared Node, TerminalNode and SplitNode in place of the tagged BeamNode")

    body = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD_TEST not in body:
        print("REFUSING: the test's BeamNode assertions are not as expected")
        return 2
    body = body.replace(OLD_TEST, NEW_TEST, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(body)
    print("test_recovered.cpp: the assertions now drive the two classes through the base pointer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
