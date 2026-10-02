# -*- coding: utf-8 -*-
"""Second sweep: seven more small exports, all read whole first.

Read in round 502:

    0x10440 ord 316  setne byte [rbx + 0x41]                     CNS_SetEvaluateIntermediateNestingsAsLast
    0x10470 ord 336  setne byte [rbx + 0x22]                     SetReorganizeBiggestPartNearOrigin
    0x104A0 ord 338  setne byte [rbx + 0x23]                     SetReorganizeLongestPartNearOrigin
    0xC610  ord 334  byte [rbx + 0x20A] = 1, byte [rbx + 0x20B] = 0   ForcePartInsideHole
    0xCEC0  ord  78  dword [rsi + 8] = the 32-bit argument        SetObjective
    0xCEF0  ord 212  movsd [rbx + 0x50], xmm6  (a double)         SetShearGap
    0x89D0  ord 238  (end - begin) >> 4 then times 0xAAAAAAAAAAAAAAAB, i.e. a count of 48-byte elements
                                                                  NoFitGetNumberOfExternalPolygons

The first three continue the option flag object: +0x22, +0x23 and +0x41 sit between or beside the fields the previous sweep
pinned, and they are written the same way, so they go into the same carrier. ForcePartInsideHole writes two bytes near the
end of a part object, SetObjective and SetShearGap write to an object of their own, and the last one is not a setter at
all: it counts a container whose stride is the modular inverse of three, the same 48-byte family this project already has
as Element48, so it is written with modularInverse rather than with the magic number.

Three other functions read in the same round are tail calls into 0x132E0 and 0x2AB0 and are NOT landed here, because
those targets have not been read; landing them would be a guess.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
LAYOUT = os.path.join(ROOT, "lcns", "include", "lcns", "dll_layout.hpp")
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")
SRC = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
MAP = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")
TEST = os.path.join(ROOT, "lcns", "tests", "test_exports.cpp")

NEW_CARRIERS = '''/**
 * The object SetObjective and SetShearGap write: a 32-bit objective at +0x08 (RE 0xCEE3) and a double gap at +0x50
 * (RE 0xCF0D). Separate from the option flag carrier because the two exports write different offsets of a different
 * shape, and nothing read so far connects them.
 */
struct SolverOptionCarrier {
    unsigned char opaque00[0x08];
    std::int32_t objective;    // +0x08, RE 0xCEE3
    unsigned char opaque0C[0x44];
    double shearGap;           // +0x50, RE 0xCF0D
};
static_assert(offsetof(SolverOptionCarrier, objective) == 0x08, "RE 0xCEE3");
static_assert(offsetof(SolverOptionCarrier, shearGap) == 0x50, "RE 0xCF0D");

/** The two bytes ForcePartInsideHole sets: RE 0xC627 writes +0x20A and RE 0xC62E writes +0x20B. */
struct HoleForceCarrier {
    unsigned char opaque00[0x20A];
    unsigned char insideHole;   // +0x20A, RE 0xC627, set to 1
    unsigned char something;    // +0x20B, RE 0xC62E, set to 0
};
static_assert(offsetof(HoleForceCarrier, insideHole) == 0x20A, "RE 0xC627");
static_assert(offsetof(HoleForceCarrier, something) == 0x20B, "RE 0xC62E");

'''

DECL = '''/** RE 0x10440 (ordinal 316): byte at +0x41 becomes the truth value of the argument. */
void setEvaluateIntermediateNestingsAsLast(void* object, int value);
/** RE 0x10470 (ordinal 336): byte at +0x22. */
void setReorganizeBiggestPartNearOrigin(void* object, int value);
/** RE 0x104A0 (ordinal 338): byte at +0x23. */
void setReorganizeLongestPartNearOrigin(void* object, int value);
/** RE 0xC610 (ordinal 334): sets +0x20A to 1 and +0x20B to 0. No argument beyond the object. */
void forcePartInsideHole(void* part);
/** RE 0xCEC0 (ordinal 78): the 32-bit argument goes to +0x08. */
void setObjective(void* options, int value);
/** RE 0xCEF0 (ordinal 212): the double argument goes to +0x50. */
void setShearGap(void* options, double gap);
/** RE 0x89D0 (ordinal 238): counts the 48-byte elements of the container at +0 and +8. */
std::size_t noFitGetNumberOfExternalPolygons(const void* owner);

'''

BODY = '''void setEvaluateIntermediateNestingsAsLast(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag41 = (value != 0) ? 1 : 0;   // RE 0x1045F: setne
}

void setReorganizeBiggestPartNearOrigin(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag22 = (value != 0) ? 1 : 0;   // RE 0x1048F: setne
}

void setReorganizeLongestPartNearOrigin(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag23 = (value != 0) ? 1 : 0;   // RE 0x104BF: setne
}

void forcePartInsideHole(void* part) {
    HoleForceCarrier* carrier = static_cast<HoleForceCarrier*>(part);
    carrier->insideHole = 1;   // RE 0xC627
    carrier->something = 0;    // RE 0xC62E
}

void setObjective(void* options, int value) {
    static_cast<SolverOptionCarrier*>(options)->objective = value;   // RE 0xCEE3 stores the integer itself
}

void setShearGap(void* options, double gap) {
    static_cast<SolverOptionCarrier*>(options)->shearGap = gap;      // RE 0xCF0D
}

std::size_t noFitGetNumberOfExternalPolygons(const void* owner) {
    const unsigned char* o = static_cast<const unsigned char*>(owner);
    std::uintptr_t begin = 0;   // RE 0x89E7: [rbx]
    std::uintptr_t end = 0;     // RE 0x89F5 reads [rbx + 8]
    std::memcpy(&begin, o, sizeof(begin));
    std::memcpy(&end, o + 8, sizeof(end));
    const std::uint64_t units = static_cast<std::uint64_t>(end - begin) >> 4;   // RE 0x89F8: sar 4
    // RE 0x89EB multiplies by 0xAAAAAAAAAAAAAAAB, which is the modular inverse of three: 48-byte elements.
    return static_cast<std::size_t>(units * lcns::dll::modularInverse(3));
}

'''

TESTS = '''    // ------------------- second sweep: seven more exports, each against its decoded offset
    {
        lcns::dll::OptionFlagCarrier flags{};
        std::memset(&flags, 0x5A, sizeof(flags));
        lcns::dll::exports::impl::setEvaluateIntermediateNestingsAsLast(&flags, 5);
        CHECK(flags.flag41 == 1);                       // RE 0x1045F stores the truth value
        lcns::dll::exports::impl::setEvaluateIntermediateNestingsAsLast(&flags, 0);
        CHECK(flags.flag41 == 0);
        lcns::dll::exports::impl::setReorganizeBiggestPartNearOrigin(&flags, -2);
        CHECK(flags.flag22 == 1);                       // RE 0x1048F
        lcns::dll::exports::impl::setReorganizeLongestPartNearOrigin(&flags, 9);
        CHECK(flags.flag23 == 1);                       // RE 0x104BF
        CHECK(offsetof(lcns::dll::OptionFlagCarrier, flag22) == 0x22);
        CHECK(offsetof(lcns::dll::OptionFlagCarrier, flag23) == 0x23);
        CHECK(offsetof(lcns::dll::OptionFlagCarrier, flag41) == 0x41);

        lcns::dll::HoleForceCarrier part{};
        std::memset(&part, 0x5A, sizeof(part));
        lcns::dll::exports::impl::forcePartInsideHole(&part);
        CHECK(part.insideHole == 1);                    // RE 0xC627
        CHECK(part.something == 0);                     // RE 0xC62E
        CHECK(offsetof(lcns::dll::HoleForceCarrier, insideHole) == 0x20A);
        CHECK(offsetof(lcns::dll::HoleForceCarrier, something) == 0x20B);

        lcns::dll::SolverOptionCarrier options{};
        std::memset(&options, 0x5A, sizeof(options));
        lcns::dll::exports::impl::setObjective(&options, 4321);
        CHECK(options.objective == 4321);               // RE 0xCEE3 stores the integer, not its truth value
        lcns::dll::exports::impl::setShearGap(&options, 2.5);
        CHECK(options.shearGap == 2.5);                 // RE 0xCF0D
        CHECK(offsetof(lcns::dll::SolverOptionCarrier, objective) == 0x08);
        CHECK(offsetof(lcns::dll::SolverOptionCarrier, shearGap) == 0x50);

        // three 48-byte elements: the count must be three, which only holds if the stride is 48 and not 16
        std::vector<unsigned char> storage(3 * 48, 0);
        unsigned char owner[16];
        const std::uintptr_t begin = reinterpret_cast<std::uintptr_t>(storage.data());
        const std::uintptr_t end = begin + storage.size();
        std::memcpy(owner, &begin, sizeof(begin));
        std::memcpy(owner + 8, &end, sizeof(end));
        CHECK(lcns::dll::exports::impl::noFitGetNumberOfExternalPolygons(owner) == 3u);
        CHECK(lcns::dll::modularInverse(3) == 0xAAAAAAAAAAAAAAABull);   // the multiplier in RE 0x89EB
    }

    return check::finish("exports");'''

ROWS = """    {316, reinterpret_cast<void*>(&lcns::dll::exports::impl::setEvaluateIntermediateNestingsAsLast)},
    {336, reinterpret_cast<void*>(&lcns::dll::exports::impl::setReorganizeBiggestPartNearOrigin)},
    {338, reinterpret_cast<void*>(&lcns::dll::exports::impl::setReorganizeLongestPartNearOrigin)},
    {334, reinterpret_cast<void*>(&lcns::dll::exports::impl::forcePartInsideHole)},
    {78, reinterpret_cast<void*>(&lcns::dll::exports::impl::setObjective)},
    {212, reinterpret_cast<void*>(&lcns::dll::exports::impl::setShearGap)},
    {238, reinterpret_cast<void*>(&lcns::dll::exports::impl::noFitGetNumberOfExternalPolygons)},
"""


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    t = read(LAYOUT)
    a = "}  // namespace dll"
    assert a in t, "the dll namespace close is not in dll_layout.hpp"
    t = t.replace(a, NEW_CARRIERS + a, 1)
    # extend the option flag carrier with the three fields this sweep pinned
    old1 = "    unsigned char opaque22[0x1E];"
    new1 = ("    unsigned char flag22;      // +0x22, RE 0x1048F, SetReorganizeBiggestPartNearOrigin (ordinal 336)\n"
            "    unsigned char flag23;      // +0x23, RE 0x104BF, SetReorganizeLongestPartNearOrigin (ordinal 338)\n"
            "    unsigned char opaque24[0x1C];")
    assert old1 in t, "the opaque22 field was not found in OptionFlagCarrier"
    t = t.replace(old1, new1, 1)
    old2 = "    unsigned char opaque41[0x03];"
    new2 = ("    unsigned char flag41;      // +0x41, RE 0x1045F, CNS_SetEvaluateIntermediateNestingsAsLast (ordinal 316)\n"
            "    unsigned char opaque42[0x02];")
    assert old2 in t, "the opaque41 field was not found in OptionFlagCarrier"
    t = t.replace(old2, new2, 1)
    asserts = ('static_assert(offsetof(OptionFlagCarrier, flag22) == 0x22, "RE 0x1048F");\n'
               'static_assert(offsetof(OptionFlagCarrier, flag23) == 0x23, "RE 0x104BF");\n'
               'static_assert(offsetof(OptionFlagCarrier, flag41) == 0x41, "RE 0x1045F");\n')
    anchor = 'static_assert(offsetof(OptionFlagCarrier, field48) == 0x48, "RE 0xDE07");\n'
    assert anchor in t, "the field48 assertion was not found"
    t = t.replace(anchor, anchor + asserts, 1)
    write(LAYOUT, t)
    print("dll_layout.hpp    two carriers added, OptionFlagCarrier extended by three fields")

    h = read(HDR)
    b = "void setShearMode(void* order, int value);"
    assert b in h, "setShearMode declaration not found"
    write(HDR, h.replace(b, DECL + b, 1))
    print("exports_impl.hpp  seven declarations")

    s = read(SRC)
    c = "void setShearMode(void* order, int value)"
    assert c in s, "setShearMode body not found"
    write(SRC, s.replace(c, BODY + c, 1))
    print("exports_impl.cpp  seven bodies")

    m = read(MAP)
    d = "    {33, reinterpret_cast<void*>(&lcns::dll::exports::impl::getSolutionIdentity)},  // GetSolution"
    assert d in m, "the GetSolution forwarding row was not found"
    write(MAP, m.replace(d, d + "\n" + ROWS.rstrip("\n"), 1))
    print("exports_forwarding.inc  seven rows")

    e = read(TEST)
    f = '    return check::finish("exports");'
    assert f in e, "the exports finish anchor is missing"
    e = e.replace(f, TESTS, 1)
    start = e.find("const bool expected = ")
    assert start > 0, "the expected-ordinal expression was not found"
    end = e.find(";", start)
    assert end > start
    e = e[:end] + (" || e->ordinal0 == 316 || e->ordinal0 == 336 || e->ordinal0 == 338 || e->ordinal0 == 334"
                   " || e->ordinal0 == 78 || e->ordinal0 == 212 || e->ordinal0 == 238") + e[end:]
    old_count = "CHECK(ex::forwardedCount() == 20u);"
    assert old_count in e, "the forwardedCount assertion was not found at 20"
    e = e.replace(old_count, "CHECK(ex::forwardedCount() == 27u);", 1)
    write(TEST, e)
    print("test_exports.cpp  behavioural checks, expected ordinals and count 20 -> 27")

    print("")
    print("seven exports in one landing. forwardedCount goes from 20 to 27 if the gate is green")


if __name__ == "__main__":
    main()
