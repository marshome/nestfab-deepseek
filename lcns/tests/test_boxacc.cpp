// tests/test_boxacc.cpp -- the box accumulator and the element accumulator, against the originals.
//
// 0x5C8A10 is callable as embedded; 0x50FD40 became executable once its four callees were relocated to embedded blocks,
// which is why both can be compared here rather than merely described. Elements are fabricated to the layout the
// accessors read (0x138 stride, sub-object pointer at +0x60, the pair at +0x28/+0x30 of that sub-object), so the
// original accepts exactly the same memory the C++ does.

#include "check.hpp"
#include "lcns/field_accessors.hpp"
#include "lcns/boxacc.hpp"
#include "lcns/boxmerge.hpp"
#include "lcns/embedded.hpp"

#include <cstdint>
#include <cstring>
#include <vector>

namespace emb = lcns::embedded;

namespace {

struct Sub {
    unsigned char pad[lcns::kBoxValueA];
    double a;
    double b;
    unsigned char tail[8];
};

struct Element {
    unsigned char pad[lcns::kBoxElementSubObject];
    Sub* sub;
    unsigned char rest[lcns::kBoxElementStride - lcns::kBoxElementSubObject - sizeof(Sub*)];
};

struct Range {
    const Element* begin;
    const Element* end;
};

/** Build a vector of elements carrying the given pairs, with storage that outlives the calls. */
struct Fixture {
    std::vector<Sub> subs;
    std::vector<Element> elements;
    Range range;

    explicit Fixture(const std::vector<std::pair<double, double>>& pairs) {
        subs.resize(pairs.size());
        elements.resize(pairs.size());
        for (std::size_t i = 0; i < pairs.size(); ++i) {
            subs[i].a = pairs[i].first;
            subs[i].b = pairs[i].second;
            std::memset(elements[i].pad, 0, sizeof(elements[i].pad));
            elements[i].sub = &subs[i];
            std::memset(elements[i].rest, 0, sizeof(elements[i].rest));
        }
        range.begin = elements.empty() ? nullptr : elements.data();
        range.end = elements.empty() ? nullptr : elements.data() + elements.size();
    }
};

double boxField(const unsigned char* box, std::size_t off) {
    double v = 0.0;
    std::memcpy(&v, box + off, sizeof(v));
    return v;
}

bool sameBytes(const unsigned char* a, const unsigned char* b, std::size_t n) {
    return std::memcmp(a, b, n) == 0;
}

const std::vector<std::pair<double, double>> kSets[] = {
    {},                                                    // empty: the box must stay untouched
    {{2.0, 3.0}},
    {{-1.0, -1.0}, {0.0, 0.0}},
    {{5.0, -2.0}, {-7.0, 4.0}, {1.0, 1.0}},
    {{0.5, 0.25}},
    {{-0.125, 8.0}, {8.0, -0.125}},
    {{1e3, 1e-3}, {-1e3, 0.0}},
};

}  // namespace

int main() {
    // ---------------------------------------------------------------- properties of the box accumulator
    {
        unsigned char box[lcns::kBoxBytes];
        std::memset(box, 0, sizeof(box));
        box[lcns::kBoxFlag] = 1;                       // callers mark it uninitialised before the first pair
        const double first[2] = {3.0, -4.0};
        lcns::boxAccumulate(box, first);
        CHECK(box[lcns::kBoxFlag] == 0);               // the first call clears the flag
        CHECK(boxField(box, lcns::kBoxMinX) == 3.0);
        CHECK(boxField(box, lcns::kBoxMinY) == -4.0);
        CHECK(boxField(box, lcns::kBoxMaxX) == 3.0);
        CHECK(boxField(box, lcns::kBoxMaxY) == -4.0);
        const double second[2] = {-1.0, 2.0};
        lcns::boxAccumulate(box, second);
        CHECK(boxField(box, lcns::kBoxMinX) == -1.0);
        CHECK(boxField(box, lcns::kBoxMinY) == -4.0);
        CHECK(boxField(box, lcns::kBoxMaxX) == 3.0);
        CHECK(boxField(box, lcns::kBoxMaxY) == 2.0);
        // a pair inside the box changes nothing
        const double inside[2] = {0.0, 0.0};
        lcns::boxAccumulate(box, inside);
        CHECK(boxField(box, lcns::kBoxMinX) == -1.0 && boxField(box, lcns::kBoxMaxY) == 2.0);
    }

    // ---------------------------------------------------------------- properties of the element accumulator
    {
        // one element: the box is the origin unioned with the pair, then its own size is folded in
        Fixture f({{2.0, 3.0}});
        unsigned char box[lcns::kBoxBytes];
        std::memset(box, 0xAA, sizeof(box));
        CHECK(lcns::boxAccumulateRange(box, &f.range) == box);
        CHECK(box[lcns::kBoxFlag] == 0);
        CHECK(boxField(box, lcns::kBoxMinX) == 0.0);      // the origin is always seeded in
        CHECK(boxField(box, lcns::kBoxMinY) == 0.0);
        CHECK(boxField(box, lcns::kBoxMaxX) == 2.0);
        CHECK(boxField(box, lcns::kBoxMaxY) == 3.0);

        // An empty range: CORRECTED in round 358. The seeding call at 0x50FD84 takes the initialise path, which
        // CLEARS the flag, so the box is all zeros with a cleared flag -- the "uninitialised" guard at 0x50FDDC is not
        // reachable through this entry. My first version of this check expected the flag to stay set.
        Fixture empty({});
        unsigned char zeroBox[lcns::kBoxBytes];
        std::memset(zeroBox, 0x5A, sizeof(zeroBox));
        lcns::boxAccumulateRange(zeroBox, &empty.range);
        CHECK(zeroBox[lcns::kBoxFlag] == 0);
        CHECK(boxField(zeroBox, lcns::kBoxMinX) == 0.0);
        CHECK(boxField(zeroBox, lcns::kBoxMaxX) == 0.0);
        CHECK(boxField(zeroBox, lcns::kBoxMinY) == 0.0);
        CHECK(boxField(zeroBox, lcns::kBoxMaxY) == 0.0);

        // (2,3) and (-1,-1): after the walk the box is [-1,2] x [-1,3], width 3, height 4, and folding (3,4) in widens
        // it to [-1,3] x [-1,4]
        Fixture two({{2.0, 3.0}, {-1.0, -1.0}});
        unsigned char box2[lcns::kBoxBytes];
        std::memset(box2, 0, sizeof(box2));
        lcns::boxAccumulateRange(box2, &two.range);
        CHECK(boxField(box2, lcns::kBoxMinX) == -1.0);
        CHECK(boxField(box2, lcns::kBoxMinY) == -1.0);
        CHECK(boxField(box2, lcns::kBoxMaxX) == 3.0);
        CHECK(boxField(box2, lcns::kBoxMaxY) == 4.0);
    }

    // ---------------------------------------------------------------- differential against both originals
#if defined(LCNS_HAS_EMBEDDED_ASM)
    {
        auto originalPair = reinterpret_cast<void (*)(unsigned char*, const double*)>(emb::originalOf(0x5C8A10u));
        auto originalRange = reinterpret_cast<void* (*)(unsigned char*, const void*)>(emb::originalOf(0x50FD40u));
        CHECK(originalPair != nullptr);
        CHECK(originalRange != nullptr);
        const emb::Block* rb = emb::find(0x50FD40u);
        CHECK(rb != nullptr);
        if (rb != nullptr) {
            CHECK(rb->status == emb::Status::CallableRelocated);
            CHECK(rb->reason != nullptr && rb->reason[0] != '\0');   // names the six rewritten calls
        }

        if (originalPair != nullptr) {
            // the pair accumulator, over the pairs the boxes meet
            const double pairs[][2] = {{0.0, 0.0}, {1.0, -1.0}, {-5.0, 5.0}, {0.25, 0.75}, {-0.0, -0.0}};
            for (const double* p : pairs) {
                for (int flag = 0; flag <= 1; ++flag) {
                    unsigned char mine[lcns::kBoxBytes];
                    unsigned char theirs[lcns::kBoxBytes];
                    std::memset(mine, 0, sizeof(mine));
                    std::memset(theirs, 0, sizeof(theirs));
                    mine[lcns::kBoxFlag] = static_cast<unsigned char>(flag);
                    theirs[lcns::kBoxFlag] = static_cast<unsigned char>(flag);
                    lcns::boxAccumulate(mine, p);
                    originalPair(theirs, p);
                    CHECK(sameBytes(mine, theirs, sizeof(mine)));
                }
            }
        }

        if (originalRange != nullptr) {
            std::size_t compared = 0;
            for (const auto& set : kSets) {
                Fixture f(set);
                unsigned char mine[lcns::kBoxBytes];
                unsigned char theirs[lcns::kBoxBytes];
                std::memset(mine, 0x5A, sizeof(mine));
                std::memset(theirs, 0x5A, sizeof(theirs));
                lcns::boxAccumulateRange(mine, &f.range);
                originalRange(theirs, &f.range);
                // every byte, not only the four doubles: the flag is part of the answer
                CHECK(sameBytes(mine, theirs, sizeof(mine)));
                ++compared;
            }
            CHECK(compared == 7u);
        }
    }
#endif

    // ------------------- 0x5C8C50: src/boxmerge.cpp against the original over random boxes
#if defined(LCNS_HAS_EMBEDDED_ASM)
    {
        auto orig = reinterpret_cast<void (*)(void*, const void*)>(emb::originalOf(0x5C8C50u));
        CHECK(orig != nullptr);
        if (orig != nullptr) {
            const double vals[] = {-9.0, -1.5, -0.0, 0.0, 1.5, 7.0, 100.0, -100.0};
            const std::size_t offs[4] = {lcns::kBoxMinX, lcns::kBoxMinY, lcns::kBoxMaxX, lcns::kBoxMaxY};
            std::uint64_t s = 99991;
            std::size_t mismatches = 0;
            for (int t = 0; t < 2000; ++t) {
                unsigned char src[lcns::kBoxBytes];
                unsigned char mineBox[lcns::kBoxBytes];
                unsigned char theirBox[lcns::kBoxBytes];
                std::memset(src, 0, sizeof(src));
                std::memset(mineBox, 0x5A, sizeof(mineBox));
                s = s * 6364136223846793005ull + 1442695040888963407ull;
                src[0] = static_cast<unsigned char>((s >> 33) & 1u);
                s = s * 6364136223846793005ull + 1442695040888963407ull;
                mineBox[0] = static_cast<unsigned char>((s >> 33) & 1u);
                for (int i = 0; i < 4; ++i) {
                    s = s * 6364136223846793005ull + 1442695040888963407ull;
                    const double v = vals[(s >> 33) % 8u];
                    std::memcpy(src + offs[i], &v, 8);
                }
                std::memcpy(theirBox, mineBox, sizeof(mineBox));
                lcns::dll::exports::impl::mergeBoxInto(mineBox, src);
                orig(theirBox, src);
                if (std::memcmp(mineBox, theirBox, lcns::kBoxBytes) != 0) {
                    ++mismatches;
                }
            }
            // The destination flag is randomised above, so the INIT path -- the one this implementation got wrong
            // twice -- is inside the sample, and invalid boxes are allowed for the same reason.
            CHECK(mismatches == 0);
        }
    }
#endif

    // ------------------- the two accessors behind 0x524EE0, against the original
#if defined(LCNS_HAS_EMBEDDED_ASM)
    {
        // Both were embedded in round 444 and classified callable, so the original can be called and its answer compared
        // with the field access decoded from its own instructions. Four and five byte functions are the bottom of the
        // dependency chain that leads to GetLength and GetHeight.
        auto get20 = reinterpret_cast<std::uint32_t (*)(const void*)>(emb::originalOf(0x5203C0u));
        auto at18 = reinterpret_cast<void* (*)(void*)>(emb::originalOf(0x547620u));
        CHECK(get20 != nullptr);
        CHECK(at18 != nullptr);
        if (get20 != nullptr && at18 != nullptr) {
            std::vector<unsigned char> obj(0x40, 0);
            const std::uint32_t vals[4] = {0u, 1u, 0x12345678u, 0xFEDCBA98u};
            for (int i = 0; i < 4; ++i) {
                std::memcpy(obj.data() + 0x20, &vals[i], 4);
                CHECK(get20(obj.data()) == vals[i]);   // mov eax, dword ptr [rcx + 0x20]
            }
            CHECK(at18(obj.data()) == obj.data() + 0x18);   // lea rax, [rcx + 0x18]
        }
    }
#endif

    // ------------------------- the two window spans behind GetLength and GetHeight, box max minus window low
    {
        // Hand computed so that a mix-up cannot pass: 30 - 4 = 26 for the length and 17 - 2 = 15 for the height.
        unsigned char box[0x28];
        std::memset(box, 0, sizeof(box));
        double maxX = 30.0;
        double maxY = 17.0;
        std::memcpy(box + 0x18, &maxX, sizeof(maxX));
        std::memcpy(box + 0x20, &maxY, sizeof(maxY));
        lcns::dll::WindowSlots window{};
        window.slot08 = 4.0;
        window.slot10 = 2.0;
        CHECK(lcns::dll::exports::impl::windowSpanLength(window, box, true) == 26.0);
        CHECK(lcns::dll::exports::impl::windowSpanHeight(window, box, true) == 15.0);
        CHECK(lcns::dll::exports::impl::windowSpanLength(window, box, false) == 0.0);   // no geometry returns zero
        CHECK(lcns::dll::exports::impl::windowSpanHeight(window, box, false) == 0.0);
        // the slots these spans must not read are moved far away, so reading the wrong pair fails loudly
        window.slot18 = 1000.0;
        window.slot20 = -1000.0;
        CHECK(lcns::dll::exports::impl::windowSpanLength(window, box, true) == 26.0);
        CHECK(lcns::dll::exports::impl::windowSpanHeight(window, box, true) == 15.0);
    }

    // ---------------- 0x5203D0 and 0x5203F0 against the original, which is callable for both
#if defined(LCNS_HAS_EMBEDDED_ASM)
    {
        auto orig38 = reinterpret_cast<void (*)(void*, const void*)>(emb::originalOf(0x5203D0u));
        auto orig28 = reinterpret_cast<void (*)(void*, const void*)>(emb::originalOf(0x5203F0u));
        CHECK(orig38 != nullptr);
        CHECK(orig28 != nullptr);
        if (orig38 != nullptr && orig28 != nullptr) {
            // Awkward bit patterns, and the two pairs deliberately swapped in value, so reading the wrong offset fails.
            const std::uint64_t bits28[4] = {0x8000000000000000ull, 0x0000000000000001ull,
                                             0x3FF0000000000000ull, 0xBFF8000000000000ull};
            const std::uint64_t bits38[4] = {0x7FEFFFFFFFFFFFFFull, 0x0000000000000000ull,
                                             0x400921FB54442D18ull, 0xC01921FB54442D18ull};
            unsigned char element[0x60];
            std::memset(element, 0x5A, sizeof(element));   // fills everything else with noise
            std::memcpy(element + 0x28, bits28, sizeof(bits28));
            std::memcpy(element + 0x38, bits38, sizeof(bits38));
            unsigned char mine[16];
            unsigned char theirs[16];
            for (int which = 0; which < 2; ++which) {
                std::memset(mine, 0, sizeof(mine));
                std::memset(theirs, 0, sizeof(theirs));
                if (which == 0) {
                    lcns::dll::exports::impl::copyPair38(mine, element);
                    orig38(theirs, element);
                } else {
                    lcns::dll::exports::impl::copyPair28(mine, element);
                    orig28(theirs, element);
                }
                CHECK(std::memcmp(mine, theirs, sizeof(mine)) == 0);   // bit for bit, not approximately
            }
        }
    }
#endif

    // ------------------------- the angle axes of 0x5D3EA0, compared on the bits
    {
        double s = 99.0;
        double c = 99.0;
        CHECK(lcns::dll::exports::impl::axisSinCos(lcns::dll::exports::impl::kAngleAxisZero, &s, &c));
        CHECK(s == 0.0);
        CHECK(c == 1.0);
        // the zero must be NEGATIVE, which a value comparison cannot see: RE 0x9DE948
        std::uint64_t sinBits = 0;
        std::memcpy(&sinBits, &s, sizeof(sinBits));
        CHECK(sinBits == 0x8000000000000000ull);   // minus zero, not plus zero
        CHECK(lcns::dll::exports::impl::axisSinCos(lcns::dll::exports::impl::kAngleAxisQuarter, &s, &c));
        CHECK(s == 1.0);
        std::uint64_t cosBits = 0;
        std::memcpy(&cosBits, &c, sizeof(cosBits));
        CHECK(cosBits == 0x8000000000000000ull);   // again minus zero
        CHECK(lcns::dll::exports::impl::axisSinCos(lcns::dll::exports::impl::kAngleAxisHalf, &s, &c));
        CHECK(s == 0.0);
        CHECK(c == -1.0);
        CHECK(lcns::dll::exports::impl::axisSinCos(lcns::dll::exports::impl::kAngleAxisThreeQuarter, &s, &c));
        CHECK(s == -1.0);
        CHECK(c == 0.0);
        // a non-axis angle is not handled here; the caller falls through to the trigonometry
        CHECK(!lcns::dll::exports::impl::axisSinCos(12345LL, &s, &c));
        // and a full turn lands back on the first axis
        CHECK(lcns::dll::exports::impl::axisSinCos(static_cast<long long>(lcns::dll::exports::impl::kAngleUnitsPerTurn), &s, &c));
        CHECK(c == 1.0);
        // the four constants are the four quarters of one turn, which is what makes them the axes
        CHECK(lcns::dll::exports::impl::kAngleAxisQuarter * 4 == static_cast<long long>(lcns::dll::exports::impl::kAngleUnitsPerTurn));
        CHECK(lcns::dll::exports::impl::kAngleAxisHalf * 2 == static_cast<long long>(lcns::dll::exports::impl::kAngleUnitsPerTurn));
        CHECK(lcns::dll::exports::impl::kAngleAxisThreeQuarter * 4 == static_cast<long long>(lcns::dll::exports::impl::kAngleUnitsPerTurn) * 3);
    }

    // ------------------- the field accessors, each against its own offset and width
    {
        // A large noisy buffer, so writing the wrong offset or the wrong width shows up immediately.
        unsigned char object[0x800];
        std::memset(object, 0xA5, sizeof(object));
        {
            const std::uint32_t put = 0x12345678;
            std::memcpy(object + 0x00, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getDword00_52F920(object) == put);   // RE 0x52F920
        }
        {
            const std::uint32_t put = 0x12345678;
            std::memcpy(object + 0x00, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getDword00_54CE90(object) == put);   // RE 0x54CE90
        }
        lcns::dll::accessors::setByte00_54D110(object, 0x5A);   // RE 0x54D110
        {
            std::uint8_t got = 0;
            std::memcpy(&got, object + 0x00, sizeof(got));
            CHECK(got == 0x5A);
        }
        {
            const std::uint32_t put = 0x12345678;
            std::memcpy(object + 0x60, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getDword60_4F8C60(object) == put);   // RE 0x4F8C60
        }
        lcns::dll::accessors::setDword64_4F8CC0(object, 0x12345678);   // RE 0x4F8CC0
        {
            std::uint32_t got = 0;
            std::memcpy(&got, object + 0x64, sizeof(got));
            CHECK(got == 0x12345678);
        }
        lcns::dll::accessors::setDword6C_4F76C0(object, 0x12345678);   // RE 0x4F76C0
        {
            std::uint32_t got = 0;
            std::memcpy(&got, object + 0x6C, sizeof(got));
            CHECK(got == 0x12345678);
        }
        lcns::dll::accessors::setDword28_4F7270(object, 0x12345678);   // RE 0x4F7270
        {
            std::uint32_t got = 0;
            std::memcpy(&got, object + 0x28, sizeof(got));
            CHECK(got == 0x12345678);
        }
        lcns::dll::accessors::setByte2C_4F7290(object, 0x5A);   // RE 0x4F7290
        {
            std::uint8_t got = 0;
            std::memcpy(&got, object + 0x2C, sizeof(got));
            CHECK(got == 0x5A);
        }
    }

    // ------------------- field accessors, second batch
    {
        unsigned char object[0x800];
        std::memset(object, 0xA5, sizeof(object));
        lcns::dll::accessors::setByte6A_4F7380(object, 0x5A);   // RE 0x4F7380
        {
            std::uint8_t got = 0;
            std::memcpy(&got, object + 0x6A, sizeof(got));
            CHECK(got == 0x5A);
        }
        {
            const std::uint32_t put = 0x12345678;
            std::memcpy(object + 0x20, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getDword20_4F8360(object) == put);   // RE 0x4F8360
        }
        {
            const std::uint32_t put = 0x12345678;
            std::memcpy(object + 0x64, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getDword64_4F8CD0(object) == put);   // RE 0x4F8CD0
        }
        {
            const std::uint32_t put = 0x12345678;
            std::memcpy(object + 0x24, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getDword24_4F7060(object) == put);   // RE 0x4F7060
        }
        {
            const std::uint32_t put = 0x12345678;
            std::memcpy(object + 0x6C, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getDword6C_4F76D0(object) == put);   // RE 0x4F76D0
        }
        lcns::dll::accessors::setByte20_52F8D0(object, 0x5A);   // RE 0x52F8D0
        {
            std::uint8_t got = 0;
            std::memcpy(&got, object + 0x20, sizeof(got));
            CHECK(got == 0x5A);
        }
        lcns::dll::accessors::setByte21_52F8E0(object, 0x5A);   // RE 0x52F8E0
        {
            std::uint8_t got = 0;
            std::memcpy(&got, object + 0x21, sizeof(got));
            CHECK(got == 0x5A);
        }
    }

    // ------------------- field accessors, third batch
    {
        unsigned char object[0x800];
        std::memset(object, 0xA5, sizeof(object));
        {
            const std::uint8_t put = 0x5Aull;
            std::memcpy(object + 0x00, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getByte00_54D100(object) == put);   // RE 0x54D100
        }
        {
            const std::uint8_t put = 0x5Aull;
            std::memcpy(object + 0x00, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getByte00_5C4CD0(object) == put);   // RE 0x5C4CD0
        }
        {
            const std::uint32_t put = 0x12345678ull;
            std::memcpy(object + 0x24, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getDword24_4F7050(object) == put);   // RE 0x4F7050
        }
        {
            const std::uint64_t put = 0x1122334455667788ull;
            std::memcpy(object + 0x00, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getPtr00_4FC1D0(object) == put);   // RE 0x4FC1D0
        }
        {
            const std::uint64_t put = 0x1122334455667788ull;
            std::memcpy(object + 0x00, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getPtr00_5FC7E0(object) == put);   // RE 0x5FC7E0
        }
        {
            const std::uint64_t put = 0x1122334455667788ull;
            std::memcpy(object + 0x00, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getPtr00_4FC200(object) == put);   // RE 0x4FC200
        }
        lcns::dll::accessors::setDword60_4F8C70(object, 0x12345678ull);   // RE 0x4F8C70
        {
            std::uint32_t got = 0;
            std::memcpy(&got, object + 0x60, sizeof(got));
            CHECK(got == 0x12345678ull);
        }
        lcns::dll::accessors::setDword20_4F76B0(object, 0x12345678ull);   // RE 0x4F76B0
        {
            std::uint32_t got = 0;
            std::memcpy(&got, object + 0x20, sizeof(got));
            CHECK(got == 0x12345678ull);
        }
        {
            const std::uint32_t put = 0x12345678ull;
            std::memcpy(object + 0x20, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getDword20_548390(object) == put);   // RE 0x548390
        }
    }

    // ------------------- field accessors, fourth batch: values, addresses and a copy
    {
        unsigned char object[0x800];
        std::memset(object, 0xA5, sizeof(object));
        {
            const std::uint8_t put = 0x5Aull;
            std::memcpy(object + 0x20, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getByte20_52F930(object) == put);   // RE 0x52F930
        }
        {
            const std::uint8_t put = 0x5Aull;
            std::memcpy(object + 0x21, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getByte21_52F940(object) == put);   // RE 0x52F940
        }
        {
            const std::uint8_t put = 0x5Aull;
            std::memcpy(object + 0x68, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getByte68_4F7350(object) == put);   // RE 0x4F7350
        }
        {
            const std::uint8_t put = 0x5Aull;
            std::memcpy(object + 0x69, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getByte69_4F7360(object) == put);   // RE 0x4F7360
        }
        {
            const std::uint8_t put = 0x5Aull;
            std::memcpy(object + 0x6A, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getByte6A_4F73A0(object) == put);   // RE 0x4F73A0
        }
        {
            const std::uint8_t put = 0x5Aull;
            std::memcpy(object + 0x08, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getByte08_5FBC70(object) == put);   // RE 0x5FBC70
        }
        {
            const std::uint64_t put = 0x1122334455667788ull;
            std::memcpy(object + 0x08, &put, sizeof(put));
            CHECK(lcns::dll::accessors::getPtr08_5C4CE0(object) == put);   // RE 0x5C4CE0
        }
        CHECK(lcns::dll::accessors::addr70_4F73C0(object) == object + 0x70);   // RE 0x4F73C0, an address not a value
        CHECK(lcns::dll::accessors::addr18_5C5F40(object) == object + 0x18);   // RE 0x5C5F40, an address not a value
        CHECK(lcns::dll::accessors::addr08_54D120(object) == object + 0x08);   // RE 0x54D120, an address not a value
        CHECK(lcns::dll::accessors::addr18_5C5F60(object) == object + 0x18);   // RE 0x5C5F60, an address not a value
        CHECK(lcns::dll::accessors::addr38_5483B0(object) == object + 0x38);   // RE 0x5483B0, an address not a value
        CHECK(lcns::dll::accessors::addr28_5483A0(object) == object + 0x28);   // RE 0x5483A0, an address not a value
        {
            unsigned char source[8];
            unsigned char destination[8];
            const std::uint32_t put = 0x0BADF00Du;
            std::memcpy(source, &put, sizeof(put));
            std::memset(destination, 0, sizeof(destination));
            lcns::dll::accessors::copyDword_54CE60(destination, source);   // RE 0x54CE60
            std::uint32_t got = 0;
            std::memcpy(&got, destination, sizeof(got));
            CHECK(got == put);
            std::uint32_t untouched = 0;
            std::memcpy(&untouched, destination + 4, sizeof(untouched));
            CHECK(untouched == 0u);   // exactly one dword is copied, not two
        }
        {
            unsigned char source[8];
            unsigned char destination[8];
            const std::uint32_t put = 0x0BADF00Du;
            std::memcpy(source, &put, sizeof(put));
            std::memset(destination, 0, sizeof(destination));
            lcns::dll::accessors::copyDword_52F8A0(destination, source);   // RE 0x52F8A0
            std::uint32_t got = 0;
            std::memcpy(&got, destination, sizeof(got));
            CHECK(got == put);
            std::uint32_t untouched = 0;
            std::memcpy(&untouched, destination + 4, sizeof(untouched));
            CHECK(untouched == 0u);   // exactly one dword is copied, not two
        }
    }

    // ------------------- accessors eaten mechanically from the closure (g_eat_leaves.py)
    {
        unsigned char object[0x800];
        std::memset(object, 0xA5, sizeof(object));
        { const std::uint32_t put = 0x12345678ull; std::memcpy(object + 0xA0, &put, sizeof(put)); CHECK(lcns::dll::accessors::getA0_4F8F80(object) == put); }   // RE 0x4F8F80
        { const std::uint32_t put = 0x12345678ull; std::memcpy(object + 0xA4, &put, sizeof(put)); CHECK(lcns::dll::accessors::getA4_4F8F90(object) == put); }   // RE 0x4F8F90
        { const std::uint32_t put = 0x12345678ull; std::memcpy(object + 0xA0, &put, sizeof(put)); CHECK(lcns::dll::accessors::getA0_4F73B0(object) == put); }   // RE 0x4F73B0
        { const std::uint8_t put = 0x5Aull; std::memcpy(object + 0x90, &put, sizeof(put)); CHECK(lcns::dll::accessors::get90_4F8540(object) == put); }   // RE 0x4F8540
        { lcns::dll::accessors::setA0_4F7390(object, 0x12345678ull); std::uint32_t got = 0; std::memcpy(&got, object + 0xA0, sizeof(got)); CHECK(got == 0x12345678ull); }   // RE 0x4F7390
        { lcns::dll::accessors::set00_895F80(object, 0x1122334455667788ull); std::uint64_t got = 0; std::memcpy(&got, object + 0x00, sizeof(got)); CHECK(got == 0x1122334455667788ull); }   // RE 0x895F80
        CHECK(lcns::dll::accessors::addr68_5479B0(object) == object + 0x68);   // RE 0x5479B0
        CHECK(lcns::dll::accessors::addr88_4F77C0(object) == object + 0x88);   // RE 0x4F77C0
        CHECK(lcns::dll::accessors::addr90_547670(object) == object + 0x90);   // RE 0x547670
        CHECK(lcns::dll::accessors::addrA8_4F8FA0(object) == object + 0xA8);   // RE 0x4F8FA0
    }

    // ------------------- accessors eaten mechanically from the closure (g_eat_leaves.py)
    {
        unsigned char object[0x800];
        std::memset(object, 0xA5, sizeof(object));
        { const double put = -13.25; std::memcpy(object + 0x28, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble28_4F8370(object) == put); }   // RE 0x4F8370
        { const double put = -13.25; std::memcpy(object + 0x30, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble30_4F8380(object) == put); }   // RE 0x4F8380
        { const double put = -13.25; std::memcpy(object + 0x38, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble38_4F8C80(object) == put); }   // RE 0x4F8C80
        { const double put = -13.25; std::memcpy(object + 0x40, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble40_4F8C90(object) == put); }   // RE 0x4F8C90
        { const double put = -13.25; std::memcpy(object + 0x48, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble48_4F8CA0(object) == put); }   // RE 0x4F8CA0
        { const double put = -13.25; std::memcpy(object + 0x50, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble50_4F8CB0(object) == put); }   // RE 0x4F8CB0
        { const double put = -13.25; std::memcpy(object + 0x58, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble58_4F9C30(object) == put); }   // RE 0x4F9C30
        { const double put = -13.25; std::memcpy(object + 0x10, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble10_52F900(object) == put); }   // RE 0x52F900
        { const double put = -13.25; std::memcpy(object + 0x18, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble18_52F910(object) == put); }   // RE 0x52F910
        { const double put = -13.25; std::memcpy(object + 0x60, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble60_4F7330(object) == put); }   // RE 0x4F7330
        { const double put = -13.25; std::memcpy(object + 0x58, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble58_547650(object) == put); }   // RE 0x547650
        { const double put = -13.25; std::memcpy(object + 0x48, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble48_547630(object) == put); }   // RE 0x547630
        { lcns::dll::accessors::setDouble58_4F9C20(object, -13.25); double got = 0.0; std::memcpy(&got, object + 0x58, sizeof(got)); CHECK(got == -13.25); }   // RE 0x4F9C20
        { lcns::dll::accessors::setDouble60_4F7340(object, -13.25); double got = 0.0; std::memcpy(&got, object + 0x60, sizeof(got)); CHECK(got == -13.25); }   // RE 0x4F7340
        { lcns::dll::accessors::setDouble18_52F8B0(object, -13.25); double got = 0.0; std::memcpy(&got, object + 0x18, sizeof(got)); CHECK(got == -13.25); }   // RE 0x52F8B0
    }

    // ------------------- accessors eaten mechanically from the closure (g_eat_leaves.py)
    {
        unsigned char object[0x800];   // the largest field offset an accessor touches
        std::memset(object, 0xA5, sizeof(object));
        { const double put = -13.25; std::memcpy(object + 0x08, &put, sizeof(put)); CHECK(lcns::dll::accessors::getDouble08_52F8F0(object) == put); }   // RE 0x52F8F0
    }

    // ------------------- accessors eaten mechanically from the closure (g_eat_leaves.py)
    {
        unsigned char object[0x800];   // the largest field offset an accessor touches
        std::memset(object, 0xA5, sizeof(object));
        { unsigned char s[8]; const std::uint32_t put = 0x0BADF00Du; std::memcpy(s, &put, sizeof(put)); lcns::dll::accessors::copyDwordToA4_4F8D20(object, s); std::uint32_t got = 0; std::memcpy(&got, object + 0xA4, sizeof(got)); CHECK(got == put); }   // RE 0x4F8D20
        { unsigned char s[8]; const std::uint32_t put = 0x0BADF00Du; std::memcpy(s, &put, sizeof(put)); lcns::dll::accessors::copyDwordToA0_4F8D10(object, s); std::uint32_t got = 0; std::memcpy(&got, object + 0xA0, sizeof(got)); CHECK(got == put); }   // RE 0x4F8D10
        { const void* put = reinterpret_cast<const void*>(0x1234); std::memcpy(object + 0x70, &put, sizeof(put)); CHECK(lcns::dll::accessors::member70_4F7600(object) == put); }   // RE 0x4F7600
    }

    // ------------------- accessors eaten mechanically from the closure (g_eat_leaves.py)
    {
        unsigned char object[0x800];   // the largest field offset an accessor touches
        std::memset(object, 0xA5, sizeof(object));
        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner)); const std::uint32_t put = 0x12345678ull; std::memcpy(inner + 0xA8, &put, sizeof(put)); unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::igetA8_4FC240(outer) == put); }   // RE 0x4FC240, read through the first member
        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner)); const std::uint32_t put = 0x12345678ull; std::memcpy(inner + 0xAC, &put, sizeof(put)); unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::igetAC_4FC250(outer) == put); }   // RE 0x4FC250, read through the first member
        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner)); const std::uint8_t put = 0x5Aull; std::memcpy(inner + 0x170, &put, sizeof(put)); unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::iget170_4FC2F0(outer) == put); }   // RE 0x4FC2F0, read through the first member
        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner)); const std::uint8_t put = 0x5Aull; std::memcpy(inner + 0x1A0, &put, sizeof(put)); unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::iget1A0_4FC300(outer) == put); }   // RE 0x4FC300, read through the first member
        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner)); const std::uint8_t put = 0x5Aull; std::memcpy(inner + 0xC8, &put, sizeof(put)); unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::igetC8_4FC260(outer) == put); }   // RE 0x4FC260, read through the first member
        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner)); const std::uint8_t put = 0x5Aull; std::memcpy(inner + 0xE8, &put, sizeof(put)); unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::igetE8_4FC2D0(outer) == put); }   // RE 0x4FC2D0, read through the first member
        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner)); const std::uint8_t put = 0x5Aull; std::memcpy(inner + 0x1E8, &put, sizeof(put)); unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::iget1E8_4FC320(outer) == put); }   // RE 0x4FC320, read through the first member
        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner)); const std::uint8_t put = 0x5Aull; std::memcpy(inner + 0x1E9, &put, sizeof(put)); unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::iget1E9_4FC340(outer) == put); }   // RE 0x4FC340, read through the first member
        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner)); const std::uint8_t put = 0x5Aull; std::memcpy(inner + 0xE0, &put, sizeof(put)); unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::igetE0_4FC290(outer) == put); }   // RE 0x4FC290, read through the first member
        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner)); unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p)); lcns::dll::accessors::isetA8_4FBE90(outer, 0x12345678ull); std::uint32_t got = 0; std::memcpy(&got, inner + 0xA8, sizeof(got)); CHECK(got == 0x12345678ull); }   // RE 0x4FBE90
        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner)); unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p)); lcns::dll::accessors::isetAC_4FBEA0(outer, 0x12345678ull); std::uint32_t got = 0; std::memcpy(&got, inner + 0xAC, sizeof(got)); CHECK(got == 0x12345678ull); }   // RE 0x4FBEA0
        { unsigned char inner[0x400]; std::memset(inner, 0, sizeof(inner)); unsigned char outer[8]; unsigned char* p = inner; std::memcpy(outer, &p, sizeof(p)); lcns::dll::accessors::iset1E8_4FC330(outer, 0x5Aull); std::uint8_t got = 0; std::memcpy(&got, inner + 0x1E8, sizeof(got)); CHECK(got == 0x5Aull); }   // RE 0x4FC330
    }

    // ------------------- accessors eaten mechanically from the closure (g_eat_leaves.py)
    {
        unsigned char object[0x800];   // the largest field offset an accessor touches
        std::memset(object, 0xA5, sizeof(object));
        { std::memset(object, 0xA5, sizeof(object)); CHECK(lcns::dll::accessors::init00_54CBC0(object) == object); std::uint32_t got = 0; std::memcpy(&got, object + 0x00, sizeof(got)); CHECK(got == 0x0); }   // RE 0x54CBC0
        { unsigned char innerObject[0x400]; std::memset(innerObject, 0, sizeof(innerObject)); unsigned char outer[8]; void* p = innerObject; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::compose70_90_4F7690(outer) == innerObject + 0x90); }   // RE 0x4F7690
        { unsigned char innerObject[0x400]; std::memset(innerObject, 0, sizeof(innerObject)); const double put = 4.5; std::memcpy(innerObject + 0x58, &put, sizeof(put)); unsigned char outer[8]; const void* p = innerObject; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::compose70_58_4F7660(outer) == put); }   // RE 0x4F7660
        { unsigned char innerObject[0x400]; std::memset(innerObject, 0, sizeof(innerObject)); const double put = 4.5; std::memcpy(innerObject + 0x48, &put, sizeof(put)); unsigned char outer[8]; const void* p = innerObject; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::compose70_48_4F7640(outer) == put); }   // RE 0x4F7640
        { unsigned char innerObject[0x400]; std::memset(innerObject, 0, sizeof(innerObject)); unsigned char outer[8]; void* p = innerObject; std::memcpy(outer, &p, sizeof(p)); CHECK(lcns::dll::accessors::compose70_68_4F7680(outer) == innerObject + 0x68); }   // RE 0x4F7680
    }

    // ------------------- accessors eaten mechanically from the closure (g_eat_leaves.py)
    {
        unsigned char object[0x800];   // the largest field offset an accessor touches
        std::memset(object, 0xA5, sizeof(object));
        { std::memset(object, 0xA5, sizeof(object)); lcns::dll::accessors::clear2_8774E0(object); std::uint64_t got64 = 1; std::memcpy(&got64, object, sizeof(got64)); CHECK(got64 == 0u); std::uint8_t got8 = 1; std::memcpy(&got8, object + 0x08, sizeof(got8)); CHECK(got8 == 0); }   // RE 0x8774E0
    }

    // ------------------- two accessors the pattern matcher missed, written by hand
    {
        unsigned char innerObject[0x400];
        std::memset(innerObject, 0, sizeof(innerObject));
        unsigned char outer[8];
        unsigned char* p = innerObject;
        std::memcpy(outer, &p, sizeof(p));
        lcns::dll::accessors::isetDouble98_4FBE70(outer, 12.5);
        double got = 0.0;
        std::memcpy(&got, innerObject + 0x98, sizeof(got));
        CHECK(got == 12.5);                                  // RE 0x4FBE70
        CHECK(lcns::dll::accessors::notNullMember_822590(outer));   // RE 0x822590, the member is set
        const void* nothing = nullptr;
        std::memcpy(outer, &nothing, sizeof(nothing));
        CHECK(!lcns::dll::accessors::notNullMember_822590(outer));  // and now it is not
    }

    // ------------------- the empty container initialiser
    {
        unsigned char container[0x60];
        std::memset(container, 0xA5, sizeof(container));
        lcns::dll::accessors::initEmptyContainer_51BFC0(container);
        std::uint64_t zero = 1;
        std::memcpy(&zero, container + 0x00, sizeof(zero));
        CHECK(zero == 0u);
        std::memcpy(&zero, container + 0x20, sizeof(zero));
        CHECK(zero == 0u);
        std::memcpy(&zero, container + 0x48, sizeof(zero));
        CHECK(zero == 0u);
        void* begin = nullptr;
        void* end = nullptr;
        std::memcpy(&begin, container + 0x38, sizeof(begin));
        std::memcpy(&end, container + 0x40, sizeof(end));
        CHECK(begin == container + 0x28);              // RE 0x51BFFA
        CHECK(end == container + 0x28);                // RE 0x51BFFE, empty
    }

    // ------------------- the timer assignment leaf (RE 0x5F3900)
    {
        void* slot = nullptr;
        lcns::dll::accessors::assignTimer_5F3900(&slot);
        // RE 0x5F390D: the accessor's result is what lands in the caller's object. It is freshly allocated on each call,
        // so two calls cannot return the same object.
        CHECK(slot != nullptr);
        void* again = nullptr;
        lcns::dll::accessors::assignTimer_5F3900(&again);
        CHECK(again != nullptr);
        CHECK(again != slot);
    }

    // ------------------- the candidate object the orchestration builds (RE 0x22E30 and 0x22A20)
    {
        // The constructor reads the order at +0x220 and +0x238, so the test owns a buffer large enough for both. The
        // object itself is the 0x1C8 bytes that 0x2AB0 allocates at 0x2D31.
        unsigned char order[0x300];
        std::memset(order, 0, sizeof(order));
        unsigned char object[0x1C8];
        std::memset(object, 0xA5, sizeof(object));
        lcns::dll::accessors::constructCandidate_22E30(object, order, -13.25, 1);
        void* got_order = nullptr;
        std::memcpy(&got_order, object + 0x00, sizeof(got_order));
        CHECK(got_order == order);                       // RE 0x22A43
        double got_value = 0.0;
        std::memcpy(&got_value, object + 0x40, sizeof(got_value));
        CHECK(got_value == -13.25);                      // RE 0x22AD1
        CHECK(object[0x48] == 1);                        // RE 0x22AD6, the flag the thunk widened
        std::uint32_t nine = 0;
        std::memcpy(&nine, object + 0x4C, sizeof(nine));
        CHECK(nine == 9u);                               // RE 0x22ADD
        void* begin = nullptr;
        void* end = nullptr;
        std::memcpy(&begin, object + 0x10, sizeof(begin));
        std::memcpy(&end, object + 0x18, sizeof(end));
        CHECK(begin == object + 0x18);                   // RE 0x22A55, the inline buffer
        CHECK(end == object + 0x18);                     // RE 0x22A61, so the container is empty
        void* inner_begin = nullptr;
        void* inner_end = nullptr;
        std::memcpy(&inner_begin, object + 0x50 + 0x38, sizeof(inner_begin));
        std::memcpy(&inner_end, object + 0x50 + 0x40, sizeof(inner_end));
        CHECK(inner_begin == object + 0x50 + 0x28);      // RE 0x22AE9 through 0x51BFC0
        CHECK(inner_end == object + 0x50 + 0x28);
    }

    // ------------------- the candidate object's mode-dependent tail (RE 0x22A20 from 0x22C1F)
    {
        unsigned char order[0x300];
        unsigned char object[0x1C8];
        // The mode at [order+0x240] selects the parameters; 1 and 2 are the two the code tests for, 0 and 3 fall through
        // to the default, so all four are checked.
        const std::uint32_t modes[4] = {0, 1, 2, 3};
        const std::uint8_t expect_flag[4] = {0, 1, 1, 0};
        const std::uint32_t expect_cap[4] = {10, 500, 10, 10};
        const double expect_first[4] = {4.0, 10.0, 3.0, 4.0};
        const double expect_second[4] = {0.1, 0.2, 0.1, 0.1};
        for (int mode = 0; mode < 4; ++mode) {
            std::memset(order, 0, sizeof(order));
            std::memcpy(order + 0x240, &modes[mode], sizeof(modes[mode]));
            std::memset(object, 0xA5, sizeof(object));
            lcns::dll::accessors::constructCandidate_22E30(object, order, 0.5, 1);
            CHECK(object[0x150] == expect_flag[mode]);            // RE 0x22C41
            std::uint32_t cap = 0;
            std::memcpy(&cap, object + 0x154, sizeof(cap));
            CHECK(cap == expect_cap[mode]);                       // RE 0x22BF1
            double first = 0.0;
            double second = 0.0;
            std::memcpy(&first, object + 0x158, sizeof(first));
            std::memcpy(&second, object + 0x160, sizeof(second));
            CHECK(first == expect_first[mode]);                   // RE 0x22BFB
            CHECK(second == expect_second[mode]);                 // RE 0x22C03
        }
    }

    // ------------------- the module switch and the engine fetch (RE 0x1BF00 and 0x1BF40)
    {
        unsigned char module_static[0x10];
        std::memset(module_static, 0, sizeof(module_static));
        module_static[0] = 1;                       // RE 0x1BF4A: the static says the engine is on
        module_static[1] = 1;                       // RE 0x1BF09: the switch 0x1BF00 returns
        CHECK(lcns::dll::accessors::moduleSwitch_1BF00(module_static) == 1);
        module_static[1] = 0;
        CHECK(lcns::dll::accessors::moduleSwitch_1BF00(module_static) == 0);

        std::uint8_t header_flag = 1;               // RE 0x1BF4F: the header was already built
        std::uint32_t build_id = 0;                 // RE 0x1BF62: a zero build id is the one that lets the fetch through
        int header = 0;
        CHECK(lcns::dll::accessors::engineFetch_1BF40(module_static, &header_flag, &build_id, &header) == &header);
        // RE 0x1BF4D: the static's first byte is clear, so the fetch returns null whatever else says.
        module_static[0] = 0;
        CHECK(lcns::dll::accessors::engineFetch_1BF40(module_static, &header_flag, &build_id, &header) == nullptr);
        module_static[0] = 1;
        // RE 0x1BF62: a non-zero build id returns null, which is the case where the module recorded one.
        build_id = 7;
        CHECK(lcns::dll::accessors::engineFetch_1BF40(module_static, &header_flag, &build_id, &header) == nullptr);
        build_id = 0;
        // RE 0x1BF56 to 0x1BF90: the header is not built yet, which is the branch that calls 0x7BB430. It must not change
        // the result, because that call only writes the header the caller owns.
        header_flag = 0;
        CHECK(lcns::dll::accessors::engineFetch_1BF40(module_static, &header_flag, &build_id, &header) == &header);
    }

    return check::finish("boxacc");
}
