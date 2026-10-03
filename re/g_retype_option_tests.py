# -*- coding: utf-8 -*-
"""Rewrite the two OptionFlagCarrier test blocks to use `Order`, which is what the implementations now take.

**THE TEST WAS BUILT AROUND THE CARRIER AND THE CARRIER IS GONE FROM THESE FUNCTIONS.** The assertions were of two kinds and both survive the change with a better
subject:

  * **`option.flag40 == 1` becomes `order.fillLastNestingStrategy`** -- the SAME byte, addressed by the name the export gave it. **A test that reads the real field
    cannot pass while the field is misnamed**, which the carrier's assertions could.
  * **`offsetof(OptionFlagCarrier, flag40) == 0x40` becomes `offsetof(Order, fillLastNestingStrategy) == 0x40`** -- the same measurement of the structure that
    everything else uses, so the carrier's offset table is not maintained in two places.

**AND THE "NEIGHBOURS UNTOUCHED" CHECK BECOMES SHARPER**: the carrier's noise test compared three flag bytes against 0x5A; against `Order` the same idea can name the
fields the four flag setters must leave alone, **including `shear` and `shearCorner`, which are 32-bit and were the fields a byte-level write could have damaged.**
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_exports.cpp"

BLOCK_OLD_START = "    // ------------------- the five mode setters, each against its own decoded offset"
BLOCK_OLD_END = "    // ------------------- second sweep: seven more exports, each against its decoded offset"

NEW = '''    // ------------------- the mode setters, each against its own decoded offset on `Order` itself
    // **THESE USED TO RUN AGAINST `OptionFlagCarrier`, WHICH IS A SECOND DESCRIPTION OF FIELDS `Order` HAS.** Each byte is now read through the name the export
    // that writes it gave the field, so a rename that broke the mapping would fail here rather than pass.
    {
        lcns::Order order{};
        std::memset(&order, 0x5A, sizeof(order));   // noise, so a write to the wrong byte shows up

        lcns::dll::exports::impl::setFillLastNestingStrategy(&order, 7);
        CHECK(order.fillLastNestingStrategy == 1);          // RE 0xDDA9 stores the truth value, not the number
        lcns::dll::exports::impl::setFillLastNestingStrategy(&order, 0);
        CHECK(order.fillLastNestingStrategy == 0);

        lcns::dll::exports::impl::setPartCommonCutMode(&order, -1);
        CHECK((order.field1C & 0xFFu) == 1u);               // RE 0xDE69 writes the LOW BYTE of a 32-bit field
        lcns::dll::exports::impl::setPartCommonCutMode(&order, 0);
        CHECK((order.field1C & 0xFFu) == 0u);

        lcns::dll::exports::impl::setFloatingMode(&order, 3);
        CHECK(order.floatingMode == 1);
        lcns::dll::exports::impl::setFloatingMode(&order, 0);
        CHECK(order.floatingMode == 0);

        lcns::dll::exports::impl::setOriginPackingMode(&order, 1);
        CHECK(order.originPackingMode == 1);
        lcns::dll::exports::impl::setOriginPackingMode(&order, 0);
        CHECK(order.originPackingMode == 0);

        lcns::dll::exports::impl::setPartialShearMode(&order, 12345);
        CHECK(order.shear == 12345u);                       // RE 0xDE0A
        CHECK(order.shearCorner == 12345u);                 // RE 0xDE07: both take the value, not its truth

        // **AND THE FIELDS THE FOUR FLAG SETTERS MUST NOT TOUCH.** `shear` and `shearCorner` are thirty-two bits, so a byte write aimed at a neighbouring flag
        // would land inside them -- which is exactly the damage the carrier's byte layout could hide.
        CHECK(order.shear == 12345u && order.shearCorner == 12345u);

        CHECK(offsetof(lcns::Order, field1C) == 0x1C);
        CHECK(offsetof(lcns::Order, floatingMode) == 0x20);
        CHECK(offsetof(lcns::Order, originPackingMode) == 0x21);
        CHECK(offsetof(lcns::Order, fillLastNestingStrategy) == 0x40);
        CHECK(offsetof(lcns::Order, shear) == 0x44);
        CHECK(offsetof(lcns::Order, shearCorner) == 0x48);
    }

'''


def main(apply):
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find(BLOCK_OLD_START)
    end = text.find(BLOCK_OLD_END)
    if start < 0 or end < 0 or end <= start:
        print("REFUSING: the two anchors are not in order (start=%d end=%d)" % (start, end))
        return 2
    removed = text[start:end].count("CHECK(")
    added = NEW.count("CHECK(")
    print("   the block being replaced has %d check(s); the replacement has %d" % (removed, added))
    if added < removed:
        print("REFUSING: the replacement would remove evidence")
        return 2
    text = text[:start] + NEW + text[end:]

    # the second sweep's carrier also becomes the Order
    text = text.replace("lcns::dll::OptionFlagCarrier flags{};\n        std::memset(&flags, 0x5A, sizeof(flags));",
                        "lcns::Order flags{};\n        std::memset(&flags, 0x5A, sizeof(flags));")
    for old, new in (("flags.flag41 == 1", "flags.evaluateIntermediateNestingsAsLast == 1"),
                     ("flags.flag41 == 0", "flags.evaluateIntermediateNestingsAsLast == 0"),
                     ("flags.flag22 == 1", "flags.reorganizeBiggestPartNearOrigin == 1"),
                     ("flags.flag23 == 1", "flags.reorganizeLongestPartNearOrigin == 1"),
                     ("offsetof(lcns::dll::OptionFlagCarrier, flag22) == 0x22", "offsetof(lcns::Order, reorganizeBiggestPartNearOrigin) == 0x22"),
                     ("offsetof(lcns::dll::OptionFlagCarrier, flag23) == 0x23", "offsetof(lcns::Order, reorganizeLongestPartNearOrigin) == 0x23"),
                     ("offsetof(lcns::dll::OptionFlagCarrier, flag41) == 0x41", "offsetof(lcns::Order, evaluateIntermediateNestingsAsLast) == 0x41")):
        text = text.replace(old, new)
    if apply:
        io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
