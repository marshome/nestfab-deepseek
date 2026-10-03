// tests/test_boxacc.cpp -- the box accumulator and the element accumulator, against the originals.
//
// 0x5C8A10 is callable as embedded; 0x50FD40 became executable once its four callees were relocated to embedded blocks,
// which is why both can be compared here rather than merely described. Elements are fabricated to the layout the
// accessors read (0x138 stride, sub-object pointer at +0x60, the pair at +0x28/+0x30 of that sub-object), so the
// original accepts exactly the same memory the C++ does.

#include "check.hpp"
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
        // **THE SIX SLOTS THIS USED TO PERTURB ARE GONE, BECAUSE NOTHING READ THEM.** The assertion used to move slot18 and slot20 far away and re-check the
        // result, which proved the implementation reads slot08 and slot10 -- and the six other members existed only to be moved aside. **Deleting them keeps what
        // the test established and drops what it was maintaining on nothing's behalf.**
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

    // ------------------------------------------------------------------ the field accessors, SECTION DELETED
    //
    // Several hundred lines stood here checking 96 generated accessors against their own offsets. **Every block was a tautology**:
    // it wrote a value into a local buffer with memcpy and read it back with memcpy, so it proved memcpy and not the module. The
    // accessors are deleted with lcns/field_accessors.hpp, their offsets and RVAs are in re/all_class_fields.json and the ledger, and
    // the operations among them that HAD a name are recorded as work in re/pending_operations.md.

}
