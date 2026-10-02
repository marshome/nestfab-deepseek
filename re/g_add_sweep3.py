# -*- coding: utf-8 -*-
"""Third sweep: SetLocalEngine (ordinal 73) and SetLocalMaximumThreads (ordinal 82).

Both were read whole in round 503.

0xD370, ordinal 73, is thirteen instructions and complete:

    eax = edx ; ebx = edx
    ebx >>= 1 ; eax = ~eax ; ebx ^= 1
    byte [rsi + 0x200] = al ; ebx &= 1 ; byte [rsi + 0x200] &= 1 ; byte [rsi + 0x201] = bl

so +0x200 becomes the complement of the low bit of the argument and +0x201 the complement of bit one. Both are stored as
bytes and masked to one bit.

0xD3B0, ordinal 82, is also complete:

    if (value != 0) { eax = 0xB5B70() ; if (eax > value) eax = value ; dword [rsi + 0x1F8] = eax }
    else            { dword [rsi + 0x1F8] = 0xB5B50() }

and both helpers are the same seven instructions: call 0x8AB0E0, and if the result is zero use one. 0x8AB0E0 in turn calls
the import stub 0x63F6B0 and clamps a negative result to zero, so the number itself comes from the platform. What this
project can and does reproduce is the logic around it: the floor at one, the choice between the two branches, and the
minimum against the requested value. That logic is split out so the test can check it directly over a grid, and the
platform number is isolated behind one function that says where it comes from.
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
 * The two bytes and the thread count that SetLocalEngine and SetLocalMaximumThreads write, at RE 0xD390, RE 0xD3A0 and
 * RE 0xD3D5 / RE 0xD3E7.
 */
struct LocalEngineCarrier {
    unsigned char opaque00[0x1F8];
    std::uint32_t maxThreads;   // +0x1F8, RE 0xD3D5 and RE 0xD3E7
    unsigned char opaque1FC[0x04];
    unsigned char engineLo;     // +0x200, RE 0xD390, the complement of the argument low bit
    unsigned char engineHi;     // +0x201, RE 0xD3A0, the complement of bit one
};
static_assert(offsetof(LocalEngineCarrier, maxThreads) == 0x1F8, "RE 0xD3D5");
static_assert(offsetof(LocalEngineCarrier, engineLo) == 0x200, "RE 0xD390");
static_assert(offsetof(LocalEngineCarrier, engineHi) == 0x201, "RE 0xD3A0");

'''

DECL = '''/** RE 0xD370 (ordinal 73): +0x200 and +0x201 become the complements of bit zero and bit one. */
void setLocalEngine(void* object, int value);
/** RE 0x8AB0E0: the platform concurrency count, through the import stub 0x63F6B0, negatives clamped to zero. */
unsigned platformConcurrency();
/** RE 0xB5B70 with RE 0xB5B79, and RE 0xD3B0: floor at one, then the requested value or the minimum of the two. */
unsigned clampMaximumThreads(unsigned platformValue, int requested);
/** RE 0xD3B0 (ordinal 82): stores clampMaximumThreads(platformConcurrency(), value) at +0x1F8. */
void setLocalMaximumThreads(void* object, int value);

'''

BODY = '''void setLocalEngine(void* object, int value) {
    LocalEngineCarrier* carrier = static_cast<LocalEngineCarrier*>(object);
    const unsigned int bits = static_cast<unsigned int>(value);
    // RE 0xD38B: not, then RE 0xD399: and 1 -- the complement of the low bit, stored as a byte
    carrier->engineLo = static_cast<unsigned char>((~bits) & 1u);
    // RE 0xD389: shr 1, RE 0xD38D: xor 1, RE 0xD396: and 1 -- the complement of bit one
    carrier->engineHi = static_cast<unsigned char>(((bits >> 1) ^ 1u) & 1u);
}

unsigned platformConcurrency() {
    // RE 0x8AB0E0 calls the import stub 0x63F6B0 and clamps a negative result to zero. The stub is the platform, so this
    // is where the platform is asked, and it is the only platform number in these two exports.
    const unsigned int value = std::thread::hardware_concurrency();
    return value;   // hardware_concurrency returns zero when the value is unknown, which matches the stub contract
}

unsigned clampMaximumThreads(unsigned platformValue, int requested) {
    // RE 0xB5B79: if the count is zero use one. Both helpers do this, so it applies to either branch.
    const unsigned int floored = (platformValue == 0u) ? 1u : platformValue;
    if (requested == 0) {
        return floored;                                    // RE 0xD3E2: the branch that ignores the argument
    }
    const unsigned int want = static_cast<unsigned int>(requested);
    return (floored > want) ? want : floored;               // RE 0xD3D2: cmova takes the smaller of the two
}

void setLocalMaximumThreads(void* object, int value) {
    static_cast<LocalEngineCarrier*>(object)->maxThreads = clampMaximumThreads(platformConcurrency(), value);
}

'''

TESTS = '''    // ------------------- SetLocalEngine and SetLocalMaximumThreads, both read whole
    {
        lcns::dll::LocalEngineCarrier local{};
        std::memset(&local, 0x5A, sizeof(local));
        lcns::dll::exports::impl::setLocalEngine(&local, 0);
        CHECK(local.engineLo == 1);                     // bit zero is 0, so its complement is 1 (RE 0xD38B)
        CHECK(local.engineHi == 1);                     // bit one is 0 too
        lcns::dll::exports::impl::setLocalEngine(&local, 1);
        CHECK(local.engineLo == 0);                     // bit zero is 1, complement 0
        CHECK(local.engineHi == 1);
        lcns::dll::exports::impl::setLocalEngine(&local, 2);
        CHECK(local.engineLo == 1);
        CHECK(local.engineHi == 0);                     // bit one is 1, complement 0
        lcns::dll::exports::impl::setLocalEngine(&local, 3);
        CHECK(local.engineLo == 0);
        CHECK(local.engineHi == 0);
        CHECK(offsetof(lcns::dll::LocalEngineCarrier, engineLo) == 0x200);
        CHECK(offsetof(lcns::dll::LocalEngineCarrier, engineHi) == 0x201);

        // the recovered logic around the platform number, over a grid: floor at one, then the smaller of the two
        CHECK(lcns::dll::exports::impl::clampMaximumThreads(0u, 0) == 1u);      // zero becomes one (RE 0xB5B79)
        CHECK(lcns::dll::exports::impl::clampMaximumThreads(0u, 4) == 1u);      // min(1, 4)
        CHECK(lcns::dll::exports::impl::clampMaximumThreads(8u, 0) == 8u);      // the argument-zero branch (RE 0xD3E2)
        CHECK(lcns::dll::exports::impl::clampMaximumThreads(8u, 3) == 3u);      // min(8, 3), RE 0xD3D2
        CHECK(lcns::dll::exports::impl::clampMaximumThreads(8u, 12) == 8u);     // min(8, 12) keeps the platform value
        CHECK(lcns::dll::exports::impl::clampMaximumThreads(1u, 1) == 1u);
        for (unsigned hw = 0; hw <= 16u; ++hw) {
            for (int want = 0; want <= 16; ++want) {
                const unsigned expected = (want == 0) ? ((hw == 0u) ? 1u : hw)
                                                      : ((((hw == 0u) ? 1u : hw) > static_cast<unsigned>(want))
                                                             ? static_cast<unsigned>(want)
                                                             : ((hw == 0u) ? 1u : hw));
                CHECK(lcns::dll::exports::impl::clampMaximumThreads(hw, want) == expected);
            }
        }
    }

    return check::finish("exports");'''

ROWS = """    {73, reinterpret_cast<void*>(&lcns::dll::exports::impl::setLocalEngine)},
    {82, reinterpret_cast<void*>(&lcns::dll::exports::impl::setLocalMaximumThreads)},
"""


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    t = read(LAYOUT)
    a = "}  // namespace dll"
    assert a in t, "the dll namespace close is not in dll_layout.hpp"
    write(LAYOUT, t.replace(a, CARRIER + a, 1))
    print("dll_layout.hpp    LocalEngineCarrier with three offset assertions")

    h = read(HDR)
    b = "void setShearMode(void* order, int value);"
    assert b in h, "setShearMode declaration not found"
    write(HDR, h.replace(b, DECL + b, 1))
    print("exports_impl.hpp  four declarations")

    s = read(SRC)
    c = "void setShearMode(void* order, int value)"
    assert c in s, "setShearMode body not found"
    src = s.replace(c, BODY + c, 1)
    if "#include <thread>" not in src:
        inc = '#include <cstring>'
        assert inc in src, "the cstring include added last round was not found"
        src = src.replace(inc, inc + "\n#include <thread>", 1)
        print("exports_impl.cpp  thread included for the platform concurrency query")
    write(SRC, src)
    print("exports_impl.cpp  four bodies")

    m = read(MAP)
    d = "    {33, reinterpret_cast<void*>(&lcns::dll::exports::impl::getSolutionIdentity)},  // GetSolution"
    assert d in m, "the GetSolution forwarding row was not found"
    write(MAP, m.replace(d, d + "\n" + ROWS.rstrip("\n"), 1))
    print("exports_forwarding.inc  two rows")

    e = read(TEST)
    f = '    return check::finish("exports");'
    assert f in e, "the exports finish anchor is missing"
    e = e.replace(f, TESTS, 1)
    start = e.find("const bool expected = ")
    assert start > 0, "the expected-ordinal expression was not found"
    end = e.find(";", start)
    assert end > start
    e = e[:end] + " || e->ordinal0 == 73 || e->ordinal0 == 82" + e[end:]
    old_count = "CHECK(ex::forwardedCount() == 27u);"
    assert old_count in e, "the forwardedCount assertion was not found at 27"
    e = e.replace(old_count, "CHECK(ex::forwardedCount() == 29u);", 1)
    write(TEST, e)
    print("test_exports.cpp  grid checks on the recovered logic, count 27 -> 29")

    print("")
    print("two exports. forwardedCount goes from 27 to 29 if the gate is green")


if __name__ == "__main__":
    main()
