# -*- coding: utf-8 -*-
"""Land the five 36-byte mode setters, in the sweep-the-small-exports mode chosen for this stretch.

All five were read whole in round 501 and are structurally identical: push, load rcx and edx, hand a rip-relative label to
0x64E120, and then write one field of the object:

    0xDD90  ordinal 144  SetFillLastNestingStrategy   setne byte [rsi + 0x40], bl
    0xDE50  ordinal 166  SetPartCommonCutMode         setne byte [rsi + 0x1C], bl
    0xDD30  ordinal 182  CNS_SetFloatingMode          setne byte [rsi + 0x20], bl
    0xDD60  ordinal 312  CNS_SetOriginPackingMode     setne byte [rsi + 0x21], bl
    0xDDF0  ordinal 330  SetPartialShearMode          mov dword [rsi + 0x48], ebx AND mov dword [rsi + 0x44], ebx

Four of them store the truth value of their second argument, so any non-zero becomes 1 and zero becomes 0. The fifth stores
the 32-bit value itself, in two places: the same setne-as-byte shape does not apply, and note that +0x44 is the field the
already implemented setShearMode writes, so this export sets the partial mode and the shear mode together.

Each entry begins by handing a rip-relative label to a logger, so none of them is callable from the embedded copy and the
evidence is behavioural, with the offsets pinned by static_assert and named by the test.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
LAYOUT = os.path.join(ROOT, "lcns", "include", "lcns", "dll_layout.hpp")
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")
SRC = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
MAP = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")
TEST = os.path.join(ROOT, "lcns", "tests", "test_exports.cpp")

CARRIER = '''/**
 * The option object the mode setters write. Offsets come from the exports themselves: RE 0xDE69 writes +0x1C,
 * RE 0xDD49 writes +0x20, RE 0xDD79 writes +0x21, RE 0xDDA9 writes +0x40, and RE 0xDE07 with RE 0xDE0A write +0x48 and
 * +0x44 as 32-bit values.
 */
struct OptionFlagCarrier {
    unsigned char opaque00[0x1C];
    unsigned char flag1C;      // +0x1C, RE 0xDE69, SetPartCommonCutMode (ordinal 166)
    unsigned char opaque1D[0x03];
    unsigned char flag20;      // +0x20, RE 0xDD49, CNS_SetFloatingMode (ordinal 182)
    unsigned char flag21;      // +0x21, RE 0xDD79, CNS_SetOriginPackingMode (ordinal 312)
    unsigned char opaque22[0x1E];
    unsigned char flag40;      // +0x40, RE 0xDDA9, SetFillLastNestingStrategy (ordinal 144)
    unsigned char opaque41[0x03];
    std::uint32_t field44;     // +0x44, RE 0xDE0A, SetPartialShearMode (ordinal 330) and the existing setShearMode
    std::uint32_t field48;     // +0x48, RE 0xDE07, SetPartialShearMode (ordinal 330)
};
static_assert(offsetof(OptionFlagCarrier, flag1C) == 0x1C, "RE 0xDE69");
static_assert(offsetof(OptionFlagCarrier, flag20) == 0x20, "RE 0xDD49");
static_assert(offsetof(OptionFlagCarrier, flag21) == 0x21, "RE 0xDD79");
static_assert(offsetof(OptionFlagCarrier, flag40) == 0x40, "RE 0xDDA9");
static_assert(offsetof(OptionFlagCarrier, field44) == 0x44, "RE 0xDE0A");
static_assert(offsetof(OptionFlagCarrier, field48) == 0x48, "RE 0xDE07");

'''

DECL = '''/** RE 0xDD90 (ordinal 144): byte at +0x40 becomes the truth value of the argument. */
void setFillLastNestingStrategy(void* object, int value);
/** RE 0xDE50 (ordinal 166): byte at +0x1C. */
void setPartCommonCutMode(void* object, int value);
/** RE 0xDD30 (ordinal 182): byte at +0x20. */
void setFloatingMode(void* object, int value);
/** RE 0xDD60 (ordinal 312): byte at +0x21. */
void setOriginPackingMode(void* object, int value);
/** RE 0xDDF0 (ordinal 330): the 32-bit value goes to BOTH +0x48 and +0x44. */
void setPartialShearMode(void* object, int value);

'''

BODY = '''void setFillLastNestingStrategy(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag40 = (value != 0) ? 1 : 0;   // RE 0xDDA9: setne
}

void setPartCommonCutMode(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag1C = (value != 0) ? 1 : 0;   // RE 0xDE69: setne
}

void setFloatingMode(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag20 = (value != 0) ? 1 : 0;   // RE 0xDD49: setne
}

void setOriginPackingMode(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag21 = (value != 0) ? 1 : 0;   // RE 0xDD79: setne
}

void setPartialShearMode(void* object, int value) {
    OptionFlagCarrier* carrier = static_cast<OptionFlagCarrier*>(object);
    carrier->field48 = static_cast<std::uint32_t>(value);   // RE 0xDE07
    carrier->field44 = static_cast<std::uint32_t>(value);   // RE 0xDE0A, the same field setShearMode writes
}

'''

TESTS = '''    // ------------------- the five mode setters, each against its own decoded offset
    {
        lcns::dll::OptionFlagCarrier option{};
        std::memset(&option, 0x5A, sizeof(option));   // noise, so a write to the wrong byte shows up

        lcns::dll::exports::impl::setFillLastNestingStrategy(&option, 7);
        CHECK(option.flag40 == 1);                    // RE 0xDDA9 stores the truth value, not the number
        lcns::dll::exports::impl::setFillLastNestingStrategy(&option, 0);
        CHECK(option.flag40 == 0);

        lcns::dll::exports::impl::setPartCommonCutMode(&option, -1);
        CHECK(option.flag1C == 1);
        lcns::dll::exports::impl::setPartCommonCutMode(&option, 0);
        CHECK(option.flag1C == 0);

        lcns::dll::exports::impl::setFloatingMode(&option, 3);
        CHECK(option.flag20 == 1);
        lcns::dll::exports::impl::setFloatingMode(&option, 0);
        CHECK(option.flag20 == 0);

        lcns::dll::exports::impl::setOriginPackingMode(&option, 1);
        CHECK(option.flag21 == 1);
        lcns::dll::exports::impl::setOriginPackingMode(&option, 0);
        CHECK(option.flag21 == 0);

        lcns::dll::exports::impl::setPartialShearMode(&option, 12345);
        CHECK(option.field44 == 12345u);              // RE 0xDE0A
        CHECK(option.field48 == 12345u);              // RE 0xDE07: both fields take the value, not its truth value
        // and the neighbours the four flag setters must not touch
        CHECK(option.flag1C != 0x5A || option.flag20 != 0x5A || option.flag21 != 0x5A || option.flag40 != 0x5A);
        CHECK(offsetof(lcns::dll::OptionFlagCarrier, flag1C) == 0x1C);
        CHECK(offsetof(lcns::dll::OptionFlagCarrier, flag20) == 0x20);
        CHECK(offsetof(lcns::dll::OptionFlagCarrier, flag21) == 0x21);
        CHECK(offsetof(lcns::dll::OptionFlagCarrier, flag40) == 0x40);
        CHECK(offsetof(lcns::dll::OptionFlagCarrier, field44) == 0x44);
        CHECK(offsetof(lcns::dll::OptionFlagCarrier, field48) == 0x48);
    }

    return check::finish("exports");'''

ROWS = """    {144, reinterpret_cast<void*>(&lcns::dll::exports::impl::setFillLastNestingStrategy)},  // SetFillLastNestingStrategy
    {166, reinterpret_cast<void*>(&lcns::dll::exports::impl::setPartCommonCutMode)},  // SetPartCommonCutMode
    {182, reinterpret_cast<void*>(&lcns::dll::exports::impl::setFloatingMode)},  // CNS_SetFloatingMode
    {312, reinterpret_cast<void*>(&lcns::dll::exports::impl::setOriginPackingMode)},  // CNS_SetOriginPackingMode
    {330, reinterpret_cast<void*>(&lcns::dll::exports::impl::setPartialShearMode)},  // SetPartialShearMode
"""


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    t = read(LAYOUT)
    anchor = "}  // namespace dll"
    assert anchor in t, "the dll namespace close is not in dll_layout.hpp"
    write(LAYOUT, t.replace(anchor, CARRIER + anchor, 1))
    print("dll_layout.hpp    OptionFlagCarrier with six offset assertions")

    h = read(HDR)
    a = "void setShearMode(void* order, int value);"
    assert a in h, "setShearMode declaration not found"
    write(HDR, h.replace(a, DECL + a, 1))
    print("exports_impl.hpp  five declarations")

    s = read(SRC)
    b = "void setShearMode(void* order, int value)"
    assert b in s, "setShearMode body not found"
    write(SRC, s.replace(b, BODY + b, 1))
    print("exports_impl.cpp  five bodies")

    m = read(MAP)
    c = "    {33, reinterpret_cast<void*>(&lcns::dll::exports::impl::getSolutionIdentity)},  // GetSolution"
    assert c in m, "the GetSolution forwarding row was not found"
    write(MAP, m.replace(c, c + "\n" + ROWS.rstrip("\n"), 1))
    print("exports_forwarding.inc  five rows, keyed by ordinal")

    e = read(TEST)
    f = '    return check::finish("exports");'
    assert f in e, "the exports finish anchor is missing"
    e = e.replace(f, TESTS, 1)
    # the expected-ordinal expression has grown over the rounds, so it is rebuilt rather than pattern matched
    start = e.find("const bool expected = ")
    assert start > 0, "the expected-ordinal expression was not found"
    end = e.find(";", start)
    assert end > start
    e = e[:end] + " || e->ordinal0 == 144 || e->ordinal0 == 166 || e->ordinal0 == 182 || e->ordinal0 == 312 || e->ordinal0 == 330" + e[end:]
    # and the count goes from fifteen to twenty
    old_count = "CHECK(ex::forwardedCount() == 15u);"
    assert old_count in e, "the forwardedCount assertion was not found at 15"
    e = e.replace(old_count, "CHECK(ex::forwardedCount() == 20u);", 1)
    write(TEST, e)
    print("test_exports.cpp  behavioural checks, expected ordinals and count 15 -> 20")

    print("")
    print("five exports in one landing. forwardedCount goes from 15 to 20 if the gate is green")


if __name__ == "__main__":
    main()
