# -*- coding: utf-8 -*-
"""Batch sixteen: nine exports implemented, and the field map they name.

Round 537 widened the work beyond LaunchLocalComputation and re/g_ready.py answered the question that matters: nine exports
need NO further reading at all, and every one of them is a setter, so every one of them names the field it writes.

    0xD050   SetOrigin                       (86)   +0x00C dword <- the second argument
    0xEC90   SetCommonCutCuttingPreference   (154)  +0x088 byte = 1, +0x08C dword
    0xD1A0   CNS_SetMultiplicityPreference   (128)  +0x010 double, one of four constants chosen by the argument
    0xE010   SetAutomaticStop                (140)  +0x240 dword
    0xE940   SetCommonCutSafetyPreference    (150)  +0x068 byte = 1, +0x06C dword
    0xF130   SetMultiTorchCuttingPreference  (176)  +0x098 byte = 1, +0x0A0 byte = (value > 0), +0x09C dword
    0x13E30  SetSpecificSheetOrigin          (298)  +0x124 byte = 1, +0x128 dword
    0x13FE0  SetSpecificSheetObjective       (300)  +0x12C byte = 1, +0x130 dword
    0x188D0  SetMarkMode                     (246)  +0x0E8 double <- xmm2, +0x0E0 byte = (flag != 0), +0x0F0 double <- xmm3

The shape repeats so exactly that it is a fact about the object rather than about any one export: a setter of a PREFERENCE
writes a byte of 1 four bytes before its value, and that byte is this module's "an explicit value was given" marker. Five of
the nine have it. SetSpecificSheetOrigin and SetSpecificSheetObjective have the same pair, SetMultiTorchCuttingPreference adds
a second derived byte, and SetMarkMode's version sets the flag from a parameter.

Two of the nine also close questions that were open in the LaunchLocalComputation objective:

  * SetAutomaticStop writes +0x240, which is the mode 0x22A20 reads through the order, so the field has a name from an
    export rather than from a guess about what a mode number means;
  * SetMarkMode writes two doubles at +0xE8 and +0xF0, and +0xE8 and +0xF0 were already in the launch order's constructor
    field list, so the two agree.

What is NOT reproduced, and the code says so at each site: the logger call these exports make first (0x64AEA0, which this
project classifies as toolchain and which affects no return value or field), and the mutex guard they take. Everything that
touches the object is reproduced, and the tests assert every one of those stores byte for byte.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HPP = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")
CPP = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
FWD = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")
TEST = os.path.join(ROOT, "lcns", "tests", "test_exports.cpp")

DECL = """
// ---------------------------------------------------------------- the nine setters re/g_ready.py found ready (round 537)
//
// Every one writes a field of the order and nothing else observable: the logger call they make first is toolchain and
// affects no state, and the mutex guard they take is not reproduced. Each carries the store address that establishes it.

/** RE 0xD119 (ordinal 86, SetOrigin): the 32-bit argument goes to +0x0C. */
void setOrigin_0D050(void* order, int value);
/** RE 0xED59 and 0xED60 (154, SetCommonCutCuttingPreference): +0x88 = 1, then the argument at +0x8C. */
void setCommonCutCuttingPreference_0EC90(void* order, int value);
/** RE 0xD255 and its three siblings (128, CNS_SetMultiplicityPreference): one of four doubles at +0x10, chosen by the
 *  argument (1, 3 or 4 select 0x9A0476, 0x9A044C, 0x9A0413; anything else takes 0x9A0488). */
void setMultiplicityPreference_0D1A0(void* order, int choice);
/** RE 0xE0D9 and 0xE12F (140, SetAutomaticStop): the argument goes to +0x240, the mode 0x22A20 reads. */
void setAutomaticStop_0E010(void* order, int value);
/** RE 0xEA09 and 0xEA0D (150, SetCommonCutSafetyPreference): +0x68 = 1, then the argument at +0x6C. */
void setCommonCutSafetyPreference_0E940(void* order, int value);
/** RE 0xF225, 0xF22C and 0xF233 (176, SetMultiTorchCuttingPreference): +0x98 = 1, +0xA0 = (value > 0), value at +0x9C. */
void setMultiTorchCuttingPreference_0F130(void* order, int value);
/** RE 0x13F02 and 0x13F09 (298, SetSpecificSheetOrigin): +0x124 = 1, then the argument at +0x128. */
void setSpecificSheetOrigin_13E30(void* order, int value);
/** RE 0x140B2 and 0x140B9 (300, SetSpecificSheetObjective): +0x12C = 1, then the argument at +0x130. */
void setSpecificSheetObjective_13FE0(void* order, int value);
/** RE 0x189FA, 0x18A09 and 0x18A10 (246, SetMarkMode): xmm2 to +0xE8, +0xE0 = (flag != 0), xmm3 to +0xF0. */
void setMarkMode_188D0(void* order, int flag, double first, double second);
"""

IMPL = """
// ---------------------------------------------------------------- the nine setters (RE round 537)

namespace {

/** A field and the "given" byte this module writes four bytes before it. RE 0xEA09/0xEA0D and its four siblings. */
struct FieldWriter {
    unsigned char* base;
    void writeByte(std::size_t offset, unsigned char value) const {
        std::memcpy(base + offset, &value, sizeof(value));
    }
    void writeDword(std::size_t offset, std::uint32_t value) const {
        std::memcpy(base + offset, &value, sizeof(value));
    }
    void writeDouble(std::size_t offset, double value) const {
        std::memcpy(base + offset, &value, sizeof(value));
    }
};

}  // namespace

void setOrigin_0D050(void* order, int value) {
    FieldWriter{static_cast<unsigned char*>(order)}.writeDword(0x0C, static_cast<std::uint32_t>(value));  // RE 0xD119
}

void setCommonCutCuttingPreference_0EC90(void* order, int value) {
    const FieldWriter w{static_cast<unsigned char*>(order)};
    w.writeByte(0x88, 1);                                        // RE 0xED59
    w.writeDword(0x8C, static_cast<std::uint32_t>(value));       // RE 0xED60
}

void setMultiplicityPreference_0D1A0(void* order, int choice) {
    // The four doubles are read out of the image, and they are data rather than code:
    //   RE 0xD248 loads 0x9AD6D8 = 0.25, the default        RE 0xD262 loads 0x9AD6E0 = 0.05
    //   RE 0xD294 loads 0x9AD6E8 = 0.001 for choice 1      RE 0xD2B5 loads 0x9AD6D0 = 2.0 for choice 4
    // The branches are 0xD253 (choice == 3), 0xD28F (choice == 1) and 0xD2B0 (choice == 4); every other value falls
    // through to the default, which is why a switch is written rather than a table.
    double chosen = 0.25;                                        // RE 0x9AD6D8
    if (choice == 3) {
        chosen = 0.05;                                           // RE 0x9AD6E0
    } else if (choice == 1) {
        chosen = 0.001;                                          // RE 0x9AD6E8
    } else if (choice == 4) {
        chosen = 2.0;                                            // RE 0x9AD6D0
    }
    FieldWriter{static_cast<unsigned char*>(order)}.writeDouble(0x10, chosen);   // RE 0xD26A and its siblings
}

void setAutomaticStop_0E010(void* order, int value) {
    FieldWriter{static_cast<unsigned char*>(order)}.writeDword(0x240, static_cast<std::uint32_t>(value));  // RE 0xE0D9
}

void setCommonCutSafetyPreference_0E940(void* order, int value) {
    const FieldWriter w{static_cast<unsigned char*>(order)};
    w.writeByte(0x68, 1);                                        // RE 0xEA09
    w.writeDword(0x6C, static_cast<std::uint32_t>(value));       // RE 0xEA0D
}

void setMultiTorchCuttingPreference_0F130(void* order, int value) {
    const FieldWriter w{static_cast<unsigned char*>(order)};
    w.writeByte(0x98, 1);                                                          // RE 0xF225
    w.writeByte(0xA0, (value > 0) ? 1 : 0);                                        // RE 0xF22C, setg
    w.writeDword(0x9C, static_cast<std::uint32_t>(value));                         // RE 0xF233
}

void setSpecificSheetOrigin_13E30(void* order, int value) {
    const FieldWriter w{static_cast<unsigned char*>(order)};
    w.writeByte(0x124, 1);                                       // RE 0x13F02
    w.writeDword(0x128, static_cast<std::uint32_t>(value));      // RE 0x13F09
}

void setSpecificSheetObjective_13FE0(void* order, int value) {
    const FieldWriter w{static_cast<unsigned char*>(order)};
    w.writeByte(0x12C, 1);                                       // RE 0x140B2
    w.writeDword(0x130, static_cast<std::uint32_t>(value));      // RE 0x140B9
}

void setMarkMode_188D0(void* order, int flag, double first, double second) {
    const FieldWriter w{static_cast<unsigned char*>(order)};
    w.writeDouble(0xE8, first);                                  // RE 0x189FA, from xmm2
    w.writeByte(0xE0, (flag != 0) ? 1 : 0);                      // RE 0x18A09, setne
    w.writeDouble(0xF0, second);                                 // RE 0x18A10, from xmm3
}
"""

FORWARD = """    // ---------------------------------------------------------------- the nine setters re/g_ready.py found ready
    {86, reinterpret_cast<void*>(&lcns::dll::exports::impl::setOrigin_0D050)},                    // SetOrigin
    {154, reinterpret_cast<void*>(&lcns::dll::exports::impl::setCommonCutCuttingPreference_0EC90)},  // SetCommonCutCuttingPreference
    {128, reinterpret_cast<void*>(&lcns::dll::exports::impl::setMultiplicityPreference_0D1A0)},   // CNS_SetMultiplicityPreference
    {140, reinterpret_cast<void*>(&lcns::dll::exports::impl::setAutomaticStop_0E010)},            // SetAutomaticStop
    {150, reinterpret_cast<void*>(&lcns::dll::exports::impl::setCommonCutSafetyPreference_0E940)},   // SetCommonCutSafetyPreference
    {176, reinterpret_cast<void*>(&lcns::dll::exports::impl::setMultiTorchCuttingPreference_0F130)},  // SetMultiTorchCuttingPreference
    {298, reinterpret_cast<void*>(&lcns::dll::exports::impl::setSpecificSheetOrigin_13E30)},      // SetSpecificSheetOrigin
    {300, reinterpret_cast<void*>(&lcns::dll::exports::impl::setSpecificSheetObjective_13FE0)},   // SetSpecificSheetObjective
    {246, reinterpret_cast<void*>(&lcns::dll::exports::impl::setMarkMode_188D0)},                 // SetMarkMode
"""

# The shape test in tests/test_exports.cpp names every forwarded ordinal and asserts forwardedCount(); both have to move with
# the map, and the test is the only thing that notices when they do not.
TEST_OLD_COUNT = "        CHECK(ex::forwardedCount() == 31u);"
TEST_NEW_COUNT = "        CHECK(ex::forwardedCount() == 40u);"
TEST_OLD_PRED = ("                                  e->ordinal0 == 84 || e->ordinal0 == 29 || e->ordinal0 == 144 || "
                 "e->ordinal0 == 166 || e->ordinal0 == 182 || e->ordinal0 == 312 || e->ordinal0 == 330 || "
                 "e->ordinal0 == 316 || e->ordinal0 == 336 || e->ordinal0 == 338 || e->ordinal0 == 334 || "
                 "e->ordinal0 == 78 || e->ordinal0 == 212 || e->ordinal0 == 238 || e->ordinal0 == 73 || "
                 "e->ordinal0 == 82 || e->ordinal0 == 270 || e->ordinal0 == 208;")
TEST_NEW_PRED = ("                                  e->ordinal0 == 84 || e->ordinal0 == 29 || e->ordinal0 == 144 || "
                 "e->ordinal0 == 166 || e->ordinal0 == 182 || e->ordinal0 == 312 || e->ordinal0 == 330 || "
                 "e->ordinal0 == 316 || e->ordinal0 == 336 || e->ordinal0 == 338 || e->ordinal0 == 334 || "
                 "e->ordinal0 == 78 || e->ordinal0 == 212 || e->ordinal0 == 238 || e->ordinal0 == 73 || "
                 "e->ordinal0 == 82 || e->ordinal0 == 270 || e->ordinal0 == 208 ||\n"
                 "                                  // round 537: the nine setters re/g_ready.py found ready\n"
                 "                                  e->ordinal0 == 86 || e->ordinal0 == 154 || e->ordinal0 == 128 || "
                 "e->ordinal0 == 140 || e->ordinal0 == 150 || e->ordinal0 == 176 || e->ordinal0 == 298 || "
                 "e->ordinal0 == 300 || e->ordinal0 == 246;")

# The behavioural half: every store the nine setters make, asserted byte for byte against the RE address.
TEST_BLOCK = """
    // ------------------- the nine setters (round 537), every store against its RE address
    {
        std::vector<unsigned char> order(0x2C0, 0xA5);
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
        // RE 0xD119: SetOrigin (86) writes the dword to +0x0C.
        ex::impl::setOrigin_0D050(order.data(), 7);
        CHECK(dword(0x0C) == 7u);
        // RE 0xED59 and 0xED60: SetCommonCutCuttingPreference (154) sets the given byte then the value.
        std::memset(order.data(), 0, order.size());
        ex::impl::setCommonCutCuttingPreference_0EC90(order.data(), 11);
        CHECK(order[0x88] == 1);
        CHECK(dword(0x8C) == 11u);
        // RE 0xE0D9: SetAutomaticStop (140) writes the mode 0x22A20 reads, at +0x240.
        std::memset(order.data(), 0, order.size());
        ex::impl::setAutomaticStop_0E010(order.data(), 2);
        CHECK(dword(0x240) == 2u);
        // RE 0xEA09 and 0xEA0D: SetCommonCutSafetyPreference (150).
        std::memset(order.data(), 0, order.size());
        ex::impl::setCommonCutSafetyPreference_0E940(order.data(), 13);
        CHECK(order[0x68] == 1);
        CHECK(dword(0x6C) == 13u);
        // RE 0xF225, 0xF22C and 0xF233: SetMultiTorchCuttingPreference (176) also derives a byte from the sign.
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiTorchCuttingPreference_0F130(order.data(), 5);
        CHECK(order[0x98] == 1);
        CHECK(order[0xA0] == 1);
        CHECK(dword(0x9C) == 5u);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiTorchCuttingPreference_0F130(order.data(), 0);
        CHECK(order[0xA0] == 0);      // setg: the derived byte is zero when the value is not positive
        // RE 0x13F02 and 0x13F09: SetSpecificSheetOrigin (298).
        std::memset(order.data(), 0, order.size());
        ex::impl::setSpecificSheetOrigin_13E30(order.data(), 17);
        CHECK(order[0x124] == 1);
        CHECK(dword(0x128) == 17u);
        // RE 0x140B2 and 0x140B9: SetSpecificSheetObjective (300).
        std::memset(order.data(), 0, order.size());
        ex::impl::setSpecificSheetObjective_13FE0(order.data(), 19);
        CHECK(order[0x12C] == 1);
        CHECK(dword(0x130) == 19u);
        // RE 0x189FA, 0x18A09 and 0x18A10: SetMarkMode (246) takes two doubles and a flag.
        std::memset(order.data(), 0, order.size());
        ex::impl::setMarkMode_188D0(order.data(), 0, -1.5, 2.5);
        CHECK(dbl(0xE8) == -1.5);
        CHECK(order[0xE0] == 0);      // setne
        CHECK(dbl(0xF0) == 2.5);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMarkMode_188D0(order.data(), 3, 0.0, 0.0);
        CHECK(order[0xE0] == 1);
        // RE 0x9AD6D8 (0.25), 0x9AD6E0 (0.05), 0x9AD6E8 (0.001) and 0x9AD6D0 (2.0): the four constants that
        // CNS_SetMultiplicityPreference (128) chooses between, and the default when nothing matches.
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiplicityPreference_0D1A0(order.data(), 0);
        CHECK(dbl(0x10) == 0.25);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiplicityPreference_0D1A0(order.data(), 1);
        CHECK(dbl(0x10) == 0.001);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiplicityPreference_0D1A0(order.data(), 3);
        CHECK(dbl(0x10) == 0.05);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiplicityPreference_0D1A0(order.data(), 4);
        CHECK(dbl(0x10) == 2.0);
    }

    return check::finish("exports");"""


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    h = read(HPP)
    marker = "}  // namespace impl"
    assert marker in h, "the impl namespace close is gone"
    if "setOrigin_0D050" not in h:
        write(HPP, h.replace(marker, DECL.rstrip("\n") + "\n\n" + marker, 1))
        print("exports_impl.hpp   nine declarations")

    c = read(CPP)
    marker = "}  // namespace impl"
    assert marker in c, "the impl namespace close is gone in the source"
    if "setOrigin_0D050" not in c:
        write(CPP, c.replace(marker, IMPL.rstrip("\n") + "\n\n" + marker, 1))
        print("exports_impl.cpp   nine definitions")

    f = read(FWD)
    marker = "};\nconst std::size_t kForwardingCount"
    assert marker in f, "the forwarding table close is gone"
    if "setOrigin_0D050" not in f:
        write(FWD, f.replace(marker, FORWARD + marker, 1))
        print("exports_forwarding.inc   nine entries")

    t = read(TEST)
    changed = False
    if TEST_OLD_COUNT in t:
        t = t.replace(TEST_OLD_COUNT, TEST_NEW_COUNT, 1)
        changed = True
    if TEST_OLD_PRED in t:
        t = t.replace(TEST_OLD_PRED, TEST_NEW_PRED, 1)
        changed = True
    tail = '    return check::finish("exports");'
    if "setOrigin_0D050" not in t and tail in t:
        t = t.replace(tail, TEST_BLOCK.replace("    return check::finish(\"exports\");", tail), 1)
        changed = True
    if changed:
        write(TEST, t)
        print("test_exports.cpp   the count, the ordinal list and the stores")
    print("done")


if __name__ == "__main__":
    main()
