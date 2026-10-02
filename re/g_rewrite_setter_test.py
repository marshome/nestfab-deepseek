# -*- coding: utf-8 -*-
"""Rewrite the nine setters' test block against the NAMED fields, replacing the block a chain of regexes mangled.

Round 540. The goal was right -- a known structure's readers and writers must use the field name -- and the way it was done
was wrong: three regex passes over the same lines left unbalanced parentheses and a `dword` reader where a `double` was
needed. This replaces the whole block with a block written once, by hand, against lcns/launching_order.hpp's names, and it is
a script only so the replacement is recorded.

The block starts at the "the nine setters" comment and ends with the closing brace before `return check::finish("exports");`.
"""
import io
import os

PATH = r"D:\Nesting\nestfab\lcns\tests\test_exports.cpp"
START = "    // ------------------- the nine setters (round 537), every store against its RE address"
END = '    return check::finish("exports");'

BLOCK = '''    // ------------------- the nine setters (round 537), every store against its RE address
    //
    // The offsets come from lcns/launching_order.hpp by FIELD NAME, never as literals, and each reader has the width of the
    // field it reads. Both halves of that matter and both were learned here: the block was first written against bare
    // offsets with a 4-byte reader, so when the header's widths changed it silently compared the wrong half of an 8-byte
    // field and six checks failed at once. `dword`, `byte` and `dbl` take a FIELD, so the compiler moves the check when the
    // layout moves.
    {
        using Order = lcns::dll::LaunchingOrderLayout;
        std::vector<unsigned char> order(sizeof(Order), 0xA5);
        auto byte = [&order](std::size_t offset) { return order[offset]; };
        auto dword = [&order](std::size_t offset) {
            std::uint32_t value = 0;
            std::memcpy(&value, order.data() + offset, sizeof(value));
            return value;
        };
        auto dbl = [&order](std::size_t offset) {
            double value = 0.0;
            std::memcpy(&value, order.data() + offset, sizeof(value));
            return value;
        };
        constexpr std::size_t kOrigin = offsetof(Order, origin);
        constexpr std::size_t kMultiplicityPreference = offsetof(Order, multiplicityPreference);
        constexpr std::size_t kCommonCutSafetyGiven = offsetof(Order, commonCutSafetyPreferenceGiven);
        constexpr std::size_t kCommonCutSafety = offsetof(Order, commonCutSafetyPreference);
        constexpr std::size_t kCommonCutCuttingGiven = offsetof(Order, commonCutCuttingPreferenceGiven);
        constexpr std::size_t kCommonCutCutting = offsetof(Order, commonCutCuttingPreference);
        constexpr std::size_t kMultiTorchGiven = offsetof(Order, multiTorchCuttingPreferenceGiven);
        constexpr std::size_t kMultiTorchPositive = offsetof(Order, multiTorchCuttingPreferencePositive);
        constexpr std::size_t kMultiTorch = offsetof(Order, multiTorchCuttingPreference);
        constexpr std::size_t kAutomaticStop = offsetof(Order, automaticStop);
        constexpr std::size_t kSheetOriginGiven = offsetof(Order, specificSheetOriginGiven);
        constexpr std::size_t kSheetOrigin = offsetof(Order, specificSheetOrigin);
        constexpr std::size_t kSheetObjectiveGiven = offsetof(Order, specificSheetObjectiveGiven);
        constexpr std::size_t kSheetObjective = offsetof(Order, specificSheetObjective);
        constexpr std::size_t kMarkGiven = offsetof(Order, markModeGiven);
        constexpr std::size_t kMarkFirst = offsetof(Order, markModeFirst);
        constexpr std::size_t kMarkSecond = offsetof(Order, markModeSecond);

        // The offsets the names resolve to, asserted once so a layout edit is visible in one place.
        CHECK(kOrigin == 0x00C);                     // RE 0xD119
        CHECK(kAutomaticStop == 0x240);              // RE 0xE0D9
        CHECK(kCommonCutSafety == 0x06C);            // RE 0xEA0D
        CHECK(kMultiplicityPreference == 0x010);     // RE 0xD26A, a double
        CHECK(kMarkFirst == 0x0E8);                  // RE 0x189FA, a double

        // RE 0xD119: SetOrigin (86) writes the dword at +0x0C.
        ex::impl::setOrigin_0D050(order.data(), 7);
        CHECK(dword(kOrigin) == 7u);
        // RE 0xED59 and 0xED60: SetCommonCutCuttingPreference (154).
        std::memset(order.data(), 0, order.size());
        ex::impl::setCommonCutCuttingPreference_0EC90(order.data(), 11);
        CHECK(byte(kCommonCutCuttingGiven) == 1);
        CHECK(dword(kCommonCutCutting) == 11u);
        // RE 0xE0D9: SetAutomaticStop (140) writes the mode 0x22A20 reads.
        std::memset(order.data(), 0, order.size());
        ex::impl::setAutomaticStop_0E010(order.data(), 2);
        CHECK(dword(kAutomaticStop) == 2u);
        // RE 0xEA09 and 0xEA0D: SetCommonCutSafetyPreference (150).
        std::memset(order.data(), 0, order.size());
        ex::impl::setCommonCutSafetyPreference_0E940(order.data(), 13);
        CHECK(byte(kCommonCutSafetyGiven) == 1);
        CHECK(dword(kCommonCutSafety) == 13u);
        // RE 0xF225, 0xF22C and 0xF233: SetMultiTorchCuttingPreference (176) also derives a byte with setg.
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiTorchCuttingPreference_0F130(order.data(), 5);
        CHECK(byte(kMultiTorchGiven) == 1);
        CHECK(byte(kMultiTorchPositive) == 1);
        CHECK(dword(kMultiTorch) == 5u);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiTorchCuttingPreference_0F130(order.data(), 0);
        CHECK(byte(kMultiTorchPositive) == 0);       // setg: zero when the value is not positive
        // RE 0x13F02 and 0x13F09: SetSpecificSheetOrigin (298).
        std::memset(order.data(), 0, order.size());
        ex::impl::setSpecificSheetOrigin_13E30(order.data(), 17);
        CHECK(byte(kSheetOriginGiven) == 1);
        CHECK(dword(kSheetOrigin) == 17u);
        // RE 0x140B2 and 0x140B9: SetSpecificSheetObjective (300).
        std::memset(order.data(), 0, order.size());
        ex::impl::setSpecificSheetObjective_13FE0(order.data(), 19);
        CHECK(byte(kSheetObjectiveGiven) == 1);
        CHECK(dword(kSheetObjective) == 19u);
        // RE 0x189FA, 0x18A09 and 0x18A10: SetMarkMode (246) takes two doubles and a flag.
        std::memset(order.data(), 0, order.size());
        ex::impl::setMarkMode_188D0(order.data(), 0, -1.5, 2.5);
        CHECK(dbl(kMarkFirst) == -1.5);
        CHECK(byte(kMarkGiven) == 0);                // setne
        CHECK(dbl(kMarkSecond) == 2.5);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMarkMode_188D0(order.data(), 3, 0.0, 0.0);
        CHECK(byte(kMarkGiven) == 1);
        // RE 0x9AD6D8 (0.25), 0x9AD6E0 (0.05), 0x9AD6E8 (0.001) and 0x9AD6D0 (2.0): the four constants
        // CNS_SetMultiplicityPreference (128) chooses between, and the default when nothing matches.
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiplicityPreference_0D1A0(order.data(), 0);
        CHECK(dbl(kMultiplicityPreference) == 0.25);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiplicityPreference_0D1A0(order.data(), 1);
        CHECK(dbl(kMultiplicityPreference) == 0.001);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiplicityPreference_0D1A0(order.data(), 3);
        CHECK(dbl(kMultiplicityPreference) == 0.05);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiplicityPreference_0D1A0(order.data(), 4);
        CHECK(dbl(kMultiplicityPreference) == 2.0);
    }

'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.index(START)
    end = text.index(END, start)
    text = text[:start] + BLOCK + text[end:]
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("replaced the setter test block, %d characters" % len(BLOCK))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
