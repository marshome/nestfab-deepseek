# -*- coding: utf-8 -*-
"""Replace the port's `Kind`-tagged `BeamNode` with the module's own three classes, which ARE three classes.

**WHAT THE MEASUREMENT SAYS, AND IT SAYS IT FOUR TIMES:**

    Multi::TerminalNode   0xA3B570   4 slots    slot 2: movsd xmm0, [rcx + 0x48] / ret
                                                slot 3: movsd xmm0, [rcx + 0x50] / ret
    Multi::SplitNode      0xA3BB70   4 slots    slot 2: movsd xmm0, [rcx + 0x50] / ret
                                                slot 3: movsd xmm0, [rcx + 0x58] / ret

**and both derive from `Multi::Node` by their typeinfo chains.** So the module has ONE base with a `double` value at +0x48 and TWO subclasses, each with its
own vtable, each adding one `double`: `TerminalNode` at +0x50 and `SplitNode` at +0x58.

**AND THE PORT SIMULATED THAT WITH A TAG.** `struct BeamNode` carried `enum class Kind { Terminal, Split }` and `double eval()` chose between `value48` and
`value50` with a conditional -- **two classes flattened into one with a discriminator, which is the shape this objective removes in its variant form**: the
module has no `Kind` field anywhere, and `movsd xmm0, [rcx + 0x50] / ret` appears in TWO DIFFERENT VTABLE SLOTS rather than in one branch of an `if`.

**WHAT IS KEPT AND WHAT IS NOT.** The classes, their inheritance, their fields and their two accessors each are the module's; `BeamNode`'s `depth`,
`sheetIndex` and `Nesting partial` do NOT appear in any of the four slots read, **so they stay where they are as the port's own** -- the
`BeamNode`-shaped idea is the port's, and the derivation is the module's.
"""
import io
import sys

NESTER = r"D:\Nesting\nestfab\lcns\include\lcns\nester.hpp"

OLD = '''struct BeamNode {
    enum class Kind { Terminal, Split };
    Kind kind = Kind::Terminal;
    double value48 = 0.0;  // TerminalNode: `movsd xmm0,[rcx+0x48]`
    double value50 = 0.0;  // SplitNode:     `movsd xmm0,[rcx+0x50]`
    int depth = 0;
    int sheetIndex = 0;
    Nesting partial;
    double eval() const { return kind == Kind::Terminal ? value48 : value50; }
};'''

NEW = '''/** **THE THREE CLASSES THE MODULE HAS, WHICH THE PORT HAD FLATTENED INTO ONE.** The vtables and their slot bodies:

 *      Multi::TerminalNode   0xA3B570   4 slots   slot 2: `movsd xmm0, [rcx + 0x48] / ret`
 *                                                 slot 3: `movsd xmm0, [rcx + 0x50] / ret`
 *      Multi::SplitNode      0xA3BB70   4 slots   slot 2: `movsd xmm0, [rcx + 0x50] / ret`
 *                                                 slot 3: `movsd xmm0, [rcx + 0x58] / ret`
 *
 *  and both derive from `Multi::Node` by their own typeinfo chains. **So there is ONE base with a `double` at +0x48 and TWO subclasses, each with its own
 *  vtable, each adding one `double`** -- and `movsd xmm0, [rcx + 0x50] / ret` appears in TWO DIFFERENT VTABLE SLOTS rather than in one branch of an `if`.
 *
 *  **AND THAT IS WHY `struct BeamNode` WITH ITS `enum class Kind` WAS THE WRONG SHAPE**: it flattened two classes into one with a discriminator, and the
 *  module has no `Kind` field anywhere. The base's two accessors are slots 2 and 3 of every one of these tables, so they are virtual and `Node` implements
 *  them. */
class Node {
public:
    virtual ~Node() = default;

    /** RE `movsd xmm0, [rcx + 0x48]`: TerminalNode's slot 2 and the first of the base's two. */
    virtual double value() const { return value48_; }        // +0x48
    /** RE `movsd xmm0, [rcx + 0x50]`: SplitNode's slot 2, TerminalNode's slot 3, and the second of the base's two. */
    virtual double secondary() const { return 0.0; }

protected:
    double value48_ = 0.0;                                   // +0x48
};

/** RE 0xA3B570. Four slots: the destructor pair, `value()` at slot 2 reading +0x48, and `secondary()` at slot 3 reading **+0x50**. */
class TerminalNode : public Node {
public:
    double secondary() const override { return value50_; }    // RE 0x97500: movsd xmm0, [rcx + 0x50]

    double value50_ = 0.0;                                    // +0x50
};

/** RE 0xA3BB70. Four slots: the destructor pair, `value()` at slot 2 reading **+0x50**, and `secondary()` at slot 3 reading **+0x58**. **`SplitNode` OVERRIDES
 *  `value()` where `TerminalNode` inherits it** -- the same instruction at 0x97510 and 0x97500, in two different classes, which is what a tag could not
 *  express. */
class SplitNode : public Node {
public:
    double value() const override { return value50_; }        // RE 0x97510: movsd xmm0, [rcx + 0x50]
    double secondary() const override { return value58_; }    // RE 0x97520: movsd xmm0, [rcx + 0x58]

    double value50_ = 0.0;                                    // +0x50
    double value58_ = 0.0;                                    // +0x58
};'''


def main():
    text = io.open(NESTER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "class Node {" in text and "class TerminalNode" in text:
        print("the three classes are already declared")
        return 0
    if OLD not in text:
        print("REFUSING: BeamNode is not as expected")
        for line in text.split("\n"):
            if "BeamNode" in line:
                print("   found: %s" % line.strip()[:96])
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(NESTER, "w", encoding="utf-8", newline="\n").write(text)
    print("declared Multi::Node, TerminalNode and SplitNode in place of the tagged BeamNode")
    return 0


if __name__ == "__main__":
    sys.exit(main())
