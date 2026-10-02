// re/_probe_invalid.cpp -- run me: the narrowed 0x5C8C50 experiment.
//
// Round 386 found 521 of 5000 random boxes disagreeing; round 389's sweep showed the model already agrees with the
// original on VALID boxes (maxX = max(dst.maxX, src.maxX), 9 of 9), so the disagreement is confined to invalid ones
// (minX > maxX), where only the exact capture/reload order of xmm1/xmm3/xmm2 decides. This probe prints both 0x28-byte
// boxes for three explicitly invalid cases and then counts mismatches over 5000 random boxes that are ALLOWED to be
// invalid, so the ordering slip shows up with its inputs attached.
//
// Build and run (from lcns/):
//   g++ -std=c++17 -I include -DLCNS_HAS_EMBEDDED_ASM=1 ..\re\_probe_invalid.cpp \
//       build\liblcns_geom.a build\liblcns_embedded.a -o probe_invalid.exe
//   .\probe_invalid.exe
//
// The model below is the round-380 transcription, deliberately unchanged: the point is to see WHERE it parts company.
#include "lcns/boxacc.hpp"
#include "lcns/embedded.hpp"

#include <cstdint>
#include <cstdio>
#include <cstring>

namespace emb = lcns::embedded;

static double loadD(const void* b, std::size_t o) {
    double v = 0.0;
    std::memcpy(&v, static_cast<const unsigned char*>(b) + o, sizeof(v));
    return v;
}
static void storeD(void* b, std::size_t o, double v) {
    std::memcpy(static_cast<unsigned char*>(b) + o, &v, sizeof(v));
}

static void model(unsigned char* dst, const unsigned char* src) {
    if (src[0] != 0) {
        return;
    }
    double x0 = 0.0, x1 = 0.0, x2 = 0.0, x3 = 0.0;
    if (dst[0] != 0) {
        const double mnx = loadD(src, lcns::kBoxMinX);
        const double mny = loadD(src, lcns::kBoxMinY);
        dst[0] = 0;
        storeD(dst, lcns::kBoxMinX, mnx);
        storeD(dst, lcns::kBoxMinY, mny);
        storeD(dst, lcns::kBoxMaxX, mnx);
        storeD(dst, lcns::kBoxMaxY, mny);
        x1 = loadD(dst, lcns::kBoxMinX);
        x3 = loadD(dst, lcns::kBoxMinY);
        x2 = loadD(dst, lcns::kBoxMaxY);
        x0 = loadD(src, lcns::kBoxMaxX);
        if (x1 > x0) {
            storeD(dst, lcns::kBoxMinX, x0);
            x0 = loadD(src, lcns::kBoxMaxX);
        }
        // The original's INIT path jumps to 0x5C8CDB -- the maxX check -- which runs BEFORE the tail at 0x5C8CE7.
        // Omitting this store on the INIT path was the whole of round 386's 521 failures: every mismatching fixture had
        // a destination flag of 1.
        if (x0 > loadD(dst, lcns::kBoxMaxX)) {
            storeD(dst, lcns::kBoxMaxX, x0);
        }
    } else {
        x0 = loadD(src, lcns::kBoxMinX);
        x1 = loadD(dst, lcns::kBoxMinX);
        if (x1 > x0) {
            storeD(dst, lcns::kBoxMinX, x0);
            x0 = loadD(src, lcns::kBoxMinX);
            x1 = loadD(dst, lcns::kBoxMinX);
        }
        if (x0 > loadD(dst, lcns::kBoxMaxX)) {
            storeD(dst, lcns::kBoxMaxX, x0);
        }
        x0 = loadD(src, lcns::kBoxMinY);
        x3 = loadD(dst, lcns::kBoxMinY);
        if (x3 > x0) {
            storeD(dst, lcns::kBoxMinY, x0);
            x3 = x0;
            x0 = loadD(src, lcns::kBoxMinY);
        }
        x2 = loadD(dst, lcns::kBoxMaxY);
        if (x0 > x2) {
            storeD(dst, lcns::kBoxMaxY, x0);
            x2 = x0;
        }
        x0 = loadD(src, lcns::kBoxMaxX);
        if (x1 > x0) {
            storeD(dst, lcns::kBoxMinX, x0);
            x0 = loadD(src, lcns::kBoxMaxX);
        }
        if (x0 > loadD(dst, lcns::kBoxMaxX)) {
            storeD(dst, lcns::kBoxMaxX, x0);
        }
    }
    x0 = loadD(src, lcns::kBoxMaxY);
    if (x3 > x0) {
        storeD(dst, lcns::kBoxMinY, x0);
        x0 = loadD(src, lcns::kBoxMaxY);
    }
    if (x0 > x2) {
        storeD(dst, lcns::kBoxMaxY, x0);
    }
}

static void dump(const char* tag, const unsigned char* b) {
    const std::size_t offs[4] = {lcns::kBoxMinX, lcns::kBoxMinY, lcns::kBoxMaxX, lcns::kBoxMaxY};
    const char* names[4] = {"minX", "minY", "maxX", "maxY"};
    std::printf("%-7s flag=%u", tag, (unsigned)b[0]);
    for (int i = 0; i < 4; ++i) {
        std::uint64_t u = 0;
        std::memcpy(&u, b + offs[i], 8);
        std::printf("  %s=%016llx(%.17g)", names[i], (unsigned long long)u, loadD(b, offs[i]));
    }
    std::printf("\n");
}

static void runCase(const char* title, double sMinX, double sMinY, double sMaxX, double sMaxY, unsigned char sFlag,
                    double dMinX, double dMinY, double dMaxX, double dMaxY, unsigned char dFlag,
                    void (*merge)(void*, const void*)) {
    unsigned char src[lcns::kBoxBytes], mine[lcns::kBoxBytes], theirs[lcns::kBoxBytes];
    std::memset(src, 0, sizeof(src));
    src[0] = sFlag;
    storeD(src, lcns::kBoxMinX, sMinX);
    storeD(src, lcns::kBoxMinY, sMinY);
    storeD(src, lcns::kBoxMaxX, sMaxX);
    storeD(src, lcns::kBoxMaxY, sMaxY);
    std::memset(mine, 0x5A, sizeof(mine));
    mine[0] = dFlag;
    storeD(mine, lcns::kBoxMinX, dMinX);
    storeD(mine, lcns::kBoxMinY, dMinY);
    storeD(mine, lcns::kBoxMaxX, dMaxX);
    storeD(mine, lcns::kBoxMaxY, dMaxY);
    std::memcpy(theirs, mine, sizeof(mine));
    std::printf("--- %s ---\n", title);
    dump("src", src);
    model(mine, src);
    merge(theirs, src);
    dump("model", mine);
    dump("orig", theirs);
    std::printf("%s\n", std::memcmp(mine, theirs, lcns::kBoxBytes) == 0 ? "agree" : "DISAGREE");
}

int main() {
    auto merge = reinterpret_cast<void (*)(void*, const void*)>(emb::originalOf(0x5C8C50u));
    if (merge == nullptr) {
        std::printf("the original is not available (LCNS_HAS_EMBEDDED_ASM off?)\n");
        return 1;
    }
    // Explicitly invalid boxes: minX above maxX, on both sides.
    runCase("invalid source, valid destination", 100.0, -9.0, -9.0, -1.0, 0, 5.0, 6.0, 50.0, 50.0, 0, merge);
    runCase("valid source, invalid destination", 1.0, 2.0, 3.0, 4.0, 0, 100.0, -9.0, -9.0, -1.0, 0, merge);
    runCase("invalid source, uninitialised destination", 100.0, -9.0, -9.0, -1.0, 0, 0.0, 0.0, 0.0, 0.0, 1, merge);

    // Then the randomised comparison, this time ALLOWING invalid boxes (round 386's generator did the same).
    const double vals[] = {-9.0, -1.5, -0.0, 0.0, 1.5, 7.0, 100.0, -100.0};
    const int nv = 8;
    const std::size_t offs[4] = {lcns::kBoxMinX, lcns::kBoxMinY, lcns::kBoxMaxX, lcns::kBoxMaxY};
    std::uint64_t s = 12345;
    int mismatches = 0;
    for (int t = 0; t < 5000; ++t) {
        unsigned char dstA[lcns::kBoxBytes], dstB[lcns::kBoxBytes], src[lcns::kBoxBytes];
        std::memset(dstA, 0x5A, sizeof(dstA));
        std::memset(src, 0, sizeof(src));
        s = s * 6364136223846793005ull + 1442695040888963407ull;
        src[0] = (unsigned char)((s >> 33) & 1u);
        s = s * 6364136223846793005ull + 1442695040888963407ull;
        dstA[0] = (unsigned char)((s >> 33) & 1u);
        for (int i = 0; i < 4; ++i) {
            s = s * 6364136223846793005ull + 1442695040888963407ull;
            const double v = vals[(s >> 33) % nv];
            std::memcpy(src + offs[i], &v, 8);
        }
        std::memcpy(dstA + 8, src + 8, 0x20);
        s = s * 6364136223846793005ull + 1442695040888963407ull;
        const double d = vals[(s >> 33) % nv];
        std::memcpy(dstA + offs[(s >> 40) % 4], &d, 8);
        std::memcpy(dstB, dstA, lcns::kBoxBytes);
        unsigned char dstIn[lcns::kBoxBytes];
        std::memcpy(dstIn, dstA, lcns::kBoxBytes);
        unsigned char srcCopy[lcns::kBoxBytes];
        std::memcpy(srcCopy, src, lcns::kBoxBytes);
        model(dstA, srcCopy);
        merge(dstB, srcCopy);
        if (std::memcmp(dstA, dstB, lcns::kBoxBytes) != 0) {
            // The three hand-made invalid cases agreed, so the failing pattern is one the hand did not think of: print
            // the inputs alongside both outputs for the first few, instead of only counting them.
            if (mismatches < 3) {
                char title[64];
                std::snprintf(title, sizeof(title), "random mismatch #%d (case %d)", mismatches, t);
                dump("src", src);
                dump("dst-in", dstIn);
                dump("model", dstA);
                dump("orig", dstB);
                std::printf("(%s)\n", title);
            }
            ++mismatches;
        }
    }
    std::printf("\nmismatches over 5000 random boxes (invalid ones allowed): %d\n", mismatches);
    std::printf("when this prints 0, move the model into lcns/src/boxmerge.cpp\n");
    return 0;
}
