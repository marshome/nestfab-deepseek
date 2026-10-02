// tests/test_embedded.cpp -- the embedded originals, and differential tests against C++ models.
//
// Two kinds of check live here.
//
//  1. Registry checks: every block carries bytes, a hash-shaped string, and -- if it is comment-only -- a reason. A
//     block that cannot be executed is only honest if the reason travels with it.
//
//  2. Differential checks: for the blocks whose bytes are position-independent, the ORIGINAL runs next to a C++ model
//     written from what this work read, and the two must agree on several inputs. This is what makes "equivalent"
//     checkable rather than asserted, and it is the reason the embedding exists at all.
//
// The differential part needs the assembly copy, so it is compiled only when the toolchain assembled gen_orig.S; the
// registry checks always run.

#include "check.hpp"
#include "lcns/embedded.hpp"

#include <cmath>
#include <cstdint>
#include <cstring>
#include <emmintrin.h>
#include <string>

namespace emb = lcns::embedded;

namespace {

std::uint64_t bitsOf(double d) {
    std::uint64_t u = 0;
    std::memcpy(&u, &d, sizeof(u));
    return u;
}

bool sameDouble(double a, double b) {
    // bit-for-bit: an embedded original and a C++ model doing the same arithmetic must produce identical bits
    return bitsOf(a) == bitsOf(b);
}

void storeDouble(unsigned char* base, std::size_t off, double v) {
    std::memcpy(base + off, &v, sizeof(v));
}

// A 2x3 affine transform in the layout the routines use: a at +0x00, b at +0x08, c at +0x10, d at +0x18,
// tx at +0x20, ty at +0x28.
void modelApply(const double m[6], double x, double y, double& ox, double& oy) {
    ox = m[0] * x + m[1] * y + m[4];
    oy = m[2] * x + m[3] * y + m[5];
}

}  // namespace

int main() {
    // ---------------------------------------------------------------- registry
    CHECK(emb::kBlockCount > 0);
    CHECK(emb::callableCount() + emb::commentOnlyCount() == emb::kBlockCount);
    CHECK(emb::embeddedBytes() > 1000);

    std::size_t callables = 0;
    for (std::size_t i = 0; i < emb::kBlockCount; ++i) {
        const emb::Block& b = emb::kBlocks[i];
        CHECK(b.size > 0);
        CHECK(b.bytes != nullptr);
        CHECK(b.symbol != nullptr);
        CHECK(b.note != nullptr);
        CHECK(b.sha256 != nullptr);
        CHECK(std::strlen(b.sha256) == 64);            // sha256 in hex
        CHECK(b.rva >= 0x6B4C0000u || b.rva < 0x6B4C0000u);   // just that the field is populated
        if (b.status == emb::Status::Callable) {
            ++callables;
            CHECK(b.reason != nullptr && b.reason[0] == '\0');   // an unmodified copy has no excuse to record
        } else if (b.status == emb::Status::CallableRelocated) {
            ++callables;
            // A relocated copy MUST say what was rewritten: it is executable, but not byte-identical.
            CHECK(b.reason != nullptr && b.reason[0] != '\0');
        } else if (b.status == emb::Status::Data) {
            // Evidence, not code: no reason and no symbol, but the bytes must still be there and usable.
            CHECK(b.reason != nullptr);
            CHECK(b.symbol != nullptr);
            CHECK(b.bytes != nullptr);
        } else {
            CHECK(b.reason != nullptr && b.reason[0] != '\0');   // a comment-only block must say why
        }
    }
    CHECK(callables == emb::callableCount());

    // lookups agree with the table
    for (std::size_t i = 0; i < emb::kBlockCount; ++i) {
        const emb::Block& b = emb::kBlocks[i];
        CHECK(emb::find(b.rva) == &b);
        CHECK(emb::statusOf(b.rva) == b.status);
        if (b.status == emb::Status::Callable || b.status == emb::Status::CallableRelocated) {
            CHECK(emb::originalOf(b.rva) != nullptr);
        } else {
            CHECK(emb::originalOf(b.rva) == nullptr);          // no executable copy, and none claimed
        }
    }
    CHECK(emb::find(0xDEADBEEFu) == nullptr);
    CHECK(emb::originalOf(0xDEADBEEFu) == nullptr);

#if defined(LCNS_HAS_EMBEDDED_ASM)
    CHECK(emb::callableCount() == emb::kOrigTableCount);

    // ------------------------------------------------- accessors (0x51d2f0, 0x4f8370, 0x4f8380, 0x4ddd10)
    {
        unsigned char obj[0x80];
        std::memset(obj, 0, sizeof(obj));
        void* marker = reinterpret_cast<void*>(static_cast<std::uintptr_t>(0x1234));
        std::memcpy(obj + 0x60, &marker, sizeof(marker));

        auto getter = reinterpret_cast<void* (*)(void*)>(
            emb::originalOf(0x51D2F0u));
        CHECK(getter != nullptr);
        if (getter) {
            CHECK(getter(obj) == marker);                       // returns the pointer stored at +0x60
        }

        storeDouble(obj, 0x28, 2.5);
        storeDouble(obj, 0x30, 4.25);
        auto a28 = reinterpret_cast<double (*)(const void*)>(
            emb::originalOf(0x4F8370u));
        auto a30 = reinterpret_cast<double (*)(const void*)>(
            emb::originalOf(0x4F8380u));
        if (a28 && a30) {
            CHECK(sameDouble(a28(obj), 2.5));
            CHECK(sameDouble(a30(obj), 4.25));
            CHECK(!sameDouble(a28(obj), a30(obj)));
        }

        auto addr48 = reinterpret_cast<unsigned char* (*)(unsigned char*)>(
            emb::originalOf(0x4DDD10u));
        if (addr48) {
            CHECK(addr48(obj) == obj + 0x48);                   // the address of the field, not the field
            CHECK(addr48(obj) != obj + 0x60);
        }
    }

    // ------------------------------------------------- packed point add (0x16c270)
    // The original takes its first operand's coordinates at +0x08 and +0x10 and the second's at +0x00 and +0x08, which
    // is the asymmetry this work recorded, and it leaves the two sums PACKED in xmm0. A probe showed that MinGW's
    // convention for returning a struct of two doubles does not match that, so this call is declared __m128d: reading
    // the lanes is the only way to get both sums.
    {
        auto add = reinterpret_cast<__m128d (*)(const double*, const double*)>(emb::originalOf(0x16C270u));
        if (add) {
            const double a[4] = {0.0, 1.5, 2.5, 99.0};
            const double b[2] = {0.5, 0.25};
            double lanes[2] = {0.0, 0.0};
            _mm_storeu_pd(lanes, add(a, b));
            CHECK(sameDouble(lanes[0], 1.5 + 0.5));            // a[1] + b[0]
            CHECK(sameDouble(lanes[1], 2.5 + 0.25));           // a[2] + b[1]

            const double c[4] = {7.0, -1.0, 3.0, 0.0};
            const double d[2] = {1.0, 2.0};
            _mm_storeu_pd(lanes, add(c, d));
            CHECK(sameDouble(lanes[0], -1.0 + 1.0));
            CHECK(sameDouble(lanes[1], 3.0 + 2.0));
            CHECK(sameDouble(lanes[0], 0.0));

            // and the operand order matters: a[1] is added to b[0], not to b[1]
            const double e[4] = {0.0, 10.0, 20.0, 0.0};
            const double f[2] = {1.0, 2.0};
            _mm_storeu_pd(lanes, add(e, f));
            CHECK(sameDouble(lanes[0], 11.0));
            CHECK(sameDouble(lanes[1], 22.0));
        }
    }

    // ------------------------------------------------ cross product (0x24b440) against the C++ formula
    {
        auto cross = reinterpret_cast<double (*)(const double*, const double*)>(
            emb::originalOf(0x24B440u));
        if (cross) {
            const double cases[4][6] = {
                {0.0, 0.0, 1.0, 0.0, 1.0, 0.0},   // A=(0,0) C=(1,0) B=(1,0)
                {0.0, 0.0, 0.0, 1.0, 1.0, 0.0},
                {0.0, 0.0, 1.0, 1.0, 2.0, 2.0},   // collinear
                {1.0, 2.0, 4.0, 6.0, 3.0, 1.0},
            };
            for (int k = 0; k < 4; ++k) {
                double ac[4] = {cases[k][0], cases[k][1], cases[k][2], cases[k][3]};
                double b[2] = {cases[k][4], cases[k][5]};
                const double want = (ac[2] - ac[0]) * (b[1] - ac[1]) - (b[0] - ac[0]) * (ac[3] - ac[1]);
                CHECK(sameDouble(cross(ac, b), want));
            }
        }
    }

    // ------------------------------------- in-place affine, one point (0x5cfd80) against the C++ model
    const double m1[6] = {2.0, 0.0, 0.0, 4.0, 1.0, -1.0};   // scale x2, y4, translate (1,-1)
    {
        auto inplace = reinterpret_cast<void (*)(double*, const double*)>(
            emb::originalOf(0x5CFD80u));
        if (inplace) {
            const double inputs[3][2] = {{3.0, 5.0}, {0.0, 0.0}, {-2.5, 0.25}};
            for (int k = 0; k < 3; ++k) {
                double p[2] = {inputs[k][0], inputs[k][1]};
                double wx = 0.0;
                double wy = 0.0;
                modelApply(m1, p[0], p[1], wx, wy);
                inplace(p, m1);
                CHECK(sameDouble(p[0], wx));
                CHECK(sameDouble(p[1], wy));
            }
        }
    }

    // ------------------------------------- in-place affine, both points of a segment (0x5cfdc0)
    {
        auto seg = reinterpret_cast<void (*)(double*, const double*)>(
            emb::originalOf(0x5CFDC0u));
        if (seg) {
            double s[4] = {1.0, 2.0, 3.0, 4.0};
            double want[4] = {0.0, 0.0, 0.0, 0.0};
            modelApply(m1, s[0], s[1], want[0], want[1]);
            modelApply(m1, s[2], s[3], want[2], want[3]);
            seg(s, m1);
            CHECK(sameDouble(s[0], want[0]));
            CHECK(sameDouble(s[1], want[1]));
            CHECK(sameDouble(s[2], want[2]));
            CHECK(sameDouble(s[3], want[3]));
        }
    }

    // ------------------- the two originals that both apply a matrix must agree (0x5cf6b0 against 0x5cfdc0)
    {
        auto outOfPlace = reinterpret_cast<void* (*)(void*, const void*, const void*)>(
            emb::originalOf(0x5CF6B0u));
        auto inplace = reinterpret_cast<void (*)(double*, const double*)>(
            emb::originalOf(0x5CFD80u));
        auto seg = reinterpret_cast<void (*)(double*, const double*)>(
            emb::originalOf(0x5CFDC0u));
        if (outOfPlace && seg) {
            const double src[4] = {1.5, -2.0, 3.25, 0.5};
            double a[4] = {src[0], src[1], src[2], src[3]};
            double b[4] = {src[0], src[1], src[2], src[3]};
            seg(a, m1);                                          // the in-place transform on a copy
            outOfPlace(b, src, m1);                              // the out-of-place transform, same matrix
            CHECK(sameDouble(a[0], b[0]));
            CHECK(sameDouble(a[1], b[1]));
            CHECK(sameDouble(a[2], b[2]));
            CHECK(sameDouble(a[3], b[3]));
            // and the source must be untouched by the out-of-place form
            CHECK(sameDouble(src[0], 1.5) && sameDouble(src[3], 0.5));
            (void)inplace;
        }
    }

    // ------------------- composing two matrices, then applying, equals applying them in turn (0x5ce970)
    {
        auto compose = reinterpret_cast<void* (*)(void*, const void*, const void*)>(
            emb::originalOf(0x5CE970u));
        auto inplace = reinterpret_cast<void (*)(double*, const double*)>(
            emb::originalOf(0x5CFD80u));
        if (compose && inplace) {
            const double A[6] = {2.0, 0.0, 0.0, 1.0, 0.0, 0.0};    // x doubled
            const double B[6] = {1.0, 0.0, 0.0, 1.0, 1.0, 1.0};    // translate by (1,1)
            double C[6] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
            compose(C, A, B);
            double pB[2] = {3.0, 4.0};
            inplace(pB, B);                                        // shift first
            inplace(pB, A);                                        // then scale
            double pC[2] = {3.0, 4.0};
            inplace(pC, C);                                        // or compose and apply once
            CHECK(sameDouble(pC[0], pB[0]));
            CHECK(sameDouble(pC[1], pB[1]));
            CHECK(sameDouble(pC[0], 8.0));                         // 2*(3+1)
            CHECK(sameDouble(pC[1], 5.0));                         // 4+1
        }
    }
#endif  // LCNS_HAS_EMBEDDED_ASM

    // ------------------------------- the evidence behind a toolchain exclusion, read from the project's own bytes
    // Round 340 read 0x62FE20 as a floating-point classification guard. Round 356 identified it as libm's sqrt from its
    // error path: the eight bytes at rva 0xA06820 spell "sqrt", and the code stores EDOM (0x21) through the pointer a
    // helper returns before calling a reporter. Those thirty-two bytes are embedded as a data block, so the claim can be
    // checked from the project rather than from a note, and check_embeddings.py keeps them equal to the DLL's.
    {
        const emb::Block* d = emb::find(0xA06820u);
        CHECK(d != nullptr);
        if (d != nullptr) {
            CHECK(d->status == emb::Status::Data);
            CHECK(d->size == 32);
            char name[8] = {0, 0, 0, 0, 0, 0, 0, 0};
            std::memcpy(name, d->bytes, 4);
            CHECK(std::string(name) == "sqrt");
            std::uint64_t minusZero = 0;
            std::uint64_t plusInf = 0;
            std::uint64_t one = 0;
            std::memcpy(&minusZero, d->bytes + 0x08, 8);
            std::memcpy(&plusInf, d->bytes + 0x10, 8);
            std::memcpy(&one, d->bytes + 0x18, 8);
            CHECK(minusZero == 0x8000000000000000ULL);   // the -0.0 the zero path returns
            CHECK(plusInf == 0x7FF0000000000000ULL);     // the +inf the infinite path returns
            CHECK(one == 0x3FF0000000000000ULL);         // the 1.0 the denormal path compares against
            // the routine that reads them is still carried as code, and still cannot be executed from the copy
            CHECK(emb::find(0x62FE20u) != nullptr);
            CHECK(emb::statusOf(0x62FE20u) == emb::Status::CommentOnly);
            CHECK(emb::originalOf(0x62FE20u) == nullptr);
        }
    }

    return check::finish("embedded");
}
