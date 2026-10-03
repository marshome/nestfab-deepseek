# -*- coding: utf-8 -*-
"""Replace the test's assertions on the flattened `BeamNode` with the module's own DISPATCH, which is the thing a tag could not express.

**THE OLD TEST ASSERTED THE PORT'S OWN SHAPE**: `value48 == 0.0`, `value50 == 0.0`, `depth == 0`, `sheetIndex == 0` -- four ports members and a tag it was the
whole point to remove. **The module's fact is not that a field exists; it is that `value()` and `secondary()` are VIRTUAL and each class supplies its own.**

    Multi::TerminalNode  slot 2: movsd xmm0, [rcx + 0x48] / ret      slot 3: movsd xmm0, [rcx + 0x50] / ret
    Multi::SplitNode     slot 2: movsd xmm0, [rcx + 0x50] / ret      slot 3: movsd xmm0, [rcx + 0x58] / ret

**so a call through `Multi::Node*` reaches three DIFFERENT BODIES at three different offsets**, and the test drives that rather than reading fields:

  * `TerminalNode` inherits `value()` (+0x48) and overrides `secondary()` (+0x50);
  * `SplitNode` OVERRIDES `value()` (+0x50) and overrides `secondary()` (+0x58);
  * **and the same offset +0x50 is `secondary()` in one class and `value()` in the other** -- which is exactly what a `Kind` tag with a conditional could
    not say.
"""
import io
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

OLD = """        BeamNode b_beamnode;
        CHECK(b_beamnode.value48 == 0.0);
        CHECK(b_beamnode.value50 == 0.0);
        CHECK(b_beamnode.depth == 0);
        CHECK(b_beamnode.sheetIndex == 0);"""

NEW = """        // **THE THREE CLASSES THE MODULE HAS, DRIVEN THROUGH THE BASE POINTER.** RE 0xA3B570 (TerminalNode) and 0xA3BB70 (SplitNode) are two four slot
        // tables whose slot 2 and slot 3 each read a double at a fixed offset -- so what the test has to show is that the SAME CALL reaches DIFFERENT
        // OFFSETS, which a `Kind` tag and a conditional cannot express.
        lcns::TerminalNode terminal;
        lcns::SplitNode split;
        terminal.value48_ = 1.5;      // +0x48, TerminalNode slot 2: movsd xmm0, [rcx + 0x48]
        terminal.value50_ = 2.5;      // +0x50, TerminalNode slot 3
        split.value50_ = 3.5;         // +0x50, SplitNode slot 2 -- THE SAME OFFSET, A DIFFERENT SLOT
        split.value58_ = 4.5;         // +0x58, SplitNode slot 3

        lcns::Node* as_base = &terminal;
        CHECK(as_base->value() == 1.5);        // the base's slot 2 reads +0x48 through TerminalNode
        CHECK(as_base->secondary() == 2.5);    // and ITS slot 3 is the override that reads +0x50
        as_base = &split;
        CHECK(as_base->value() == 3.5);        // SplitNode OVERRIDES value(), reading +0x50
        CHECK(as_base->secondary() == 4.5);    // and adds its own +0x58

        // and the offsets themselves, which is what makes the four numbers above a layout rather than four literals
        CHECK(reinterpret_cast<const unsigned char*>(&terminal.value48_) - reinterpret_cast<const unsigned char*>(&terminal) == 0x48);
        CHECK(reinterpret_cast<const unsigned char*>(&terminal.value50_) - reinterpret_cast<const unsigned char*>(&terminal) == 0x50);
        CHECK(reinterpret_cast<const unsigned char*>(&split.value50_) - reinterpret_cast<const unsigned char*>(&split) == 0x50);
        CHECK(reinterpret_cast<const unsigned char*>(&split.value58_) - reinterpret_cast<const unsigned char*>(&split) == 0x58);"""


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "lcns::TerminalNode terminal;" in text:
        print("the test already drives the three classes")
        return 0
    if OLD not in text:
        print("REFUSING: the BeamNode assertions are not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("the test now drives the two classes through the base pointer, at four measured offsets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
