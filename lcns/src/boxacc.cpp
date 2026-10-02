// lcns/src/boxacc.cpp -- RE 0x5C8A10 and 0x50FD40.
//
// Two details are reproduced deliberately rather than simplified away, because the differential test compares bit for bit:
//
//   * boxAccumulate follows the original's two paths exactly, including the instruction order of each comparison
//     (ucomisd against the current bound, then a conditional store). The comparisons use `<=`/`>` in the same direction
//     as `jbe`/`ja`, which is what decides the NaN behaviour;
//   * the final fold-in of the box's size keeps the original's two branches, each of which multiplies a zero by one of
//     the extents before adding it. For finite inputs both branches store the same thing and the multiply is dead
//     arithmetic -- but zero times an infinity is a NaN, so a simplified single branch would NOT agree with the original
//     on infinite extents. Faithfulness wins over tidiness here.

#include "lcns/boxacc.hpp"

#include <cstring>

namespace lcns {
namespace {

double loadDouble(const void* base, std::size_t offset) {
    double v = 0.0;
    std::memcpy(&v, static_cast<const unsigned char*>(base) + offset, sizeof(v));
    return v;
}

void storeDouble(void* base, std::size_t offset, double v) {
    std::memcpy(static_cast<unsigned char*>(base) + offset, &v, sizeof(v));
}

}  // namespace

void boxAccumulate(unsigned char* box, const double* pair) {
    // 0x5C8A10: `cmp byte [rcx], 0 ; jne 0x5C8A60` -- a NON-ZERO flag means "nothing seen yet", so this call is the one
    // that establishes the box and clears the flag.
    if (box[kBoxFlag] != 0) {
        // 0x5C8A60..0x5C8A81: store the pair into all four slots (the four quadword moves, two per coordinate).
        box[kBoxFlag] = 0;
        storeDouble(box, kBoxMinX, pair[0]);
        storeDouble(box, kBoxMinY, pair[1]);
        storeDouble(box, kBoxMaxX, pair[0]);
        storeDouble(box, kBoxMaxY, pair[1]);
        return;
    }
    // 0x5C8A15..0x5C8A2D: minX, then 0x5C8A2D..0x5C8A39: maxX.
    if (!(loadDouble(box, kBoxMinX) <= pair[0])) {
        storeDouble(box, kBoxMinX, pair[0]);
    }
    if (pair[0] > loadDouble(box, kBoxMaxX)) {
        storeDouble(box, kBoxMaxX, pair[0]);
    }
    // 0x5C8A39..0x5C8A53: minY, then 0x5C8A53..0x5C8A5F: maxY.
    if (!(loadDouble(box, kBoxMinY) <= pair[1])) {
        storeDouble(box, kBoxMinY, pair[1]);
    }
    if (pair[1] > loadDouble(box, kBoxMaxY)) {
        storeDouble(box, kBoxMaxY, pair[1]);
    }
}

void* boxAccumulateRange(unsigned char* box, const void* range) {
    // 0x50FD62/0x50FD68..0x50FD7A: mark the box uninitialised and clear it.
    box[kBoxFlag] = 1;
    storeDouble(box, kBoxMinX, 0.0);
    storeDouble(box, kBoxMinY, 0.0);
    storeDouble(box, kBoxMaxX, 0.0);
    storeDouble(box, kBoxMaxY, 0.0);

    // 0x50FD56/0x50FD7F: the stack pair starts at (0, 0), and 0x50FD84 seeds the box with it. Two consequences: the
    // origin is always part of the answer, and the seeding call clears the flag, so the "uninitialised" test at 0x50FDDC
    // is unreachable from this entry (an empty range returns an all-zero box).
    double pair[2] = {0.0, 0.0};
    boxAccumulate(box, pair);

    const unsigned char* begin = nullptr;
    const unsigned char* end = nullptr;
    std::memcpy(&begin, static_cast<const unsigned char*>(range), sizeof(begin));
    std::memcpy(&end, static_cast<const unsigned char*>(range) + 8, sizeof(end));

    for (const unsigned char* element = begin; element != end; element += kBoxElementStride) {
        // 0x50FD98/0x50FDA0 and 0x50FDB3/0x50FDBB: the getter then the accessor, twice.
        const unsigned char* sub = nullptr;
        std::memcpy(&sub, element + kBoxElementSubObject, sizeof(sub));
        const double a = loadDouble(sub, kBoxValueA);
        const double b = loadDouble(sub, kBoxValueB);
        pair[0] = a;   // 0x50FDC6
        pair[1] = b;   // 0x50FDCC
        boxAccumulate(box, pair);
    }

    // 0x50FDDC: an uninitialised box means nothing was seen, so the routine returns it as it stands.
    if (box[kBoxFlag] != 0) {
        return box;
    }

    // 0x50FDE5..0x50FDF9: height = maxY - minY (xmm1), width = maxX - minX (xmm0).
    const double height = loadDouble(box, kBoxMaxY) - loadDouble(box, kBoxMinY);
    const double width = loadDouble(box, kBoxMaxX) - loadDouble(box, kBoxMinX);

    // 0x50FDFD `ucomisd xmm0, xmm1 ; jbe 0x50FE40`: the two branches differ only in which extent the zero is multiplied
    // by, which matters only for infinities (0 * inf = NaN), so both are kept.
    double w = width;
    double h = height;
    if (width > height) {
        w = width + 0.0 * height;   // 0x50FDFF mulsd xmm7, xmm1 ; 0x50FE03 addsd xmm0, xmm7
        h = 0.0 + height;           // 0x50FE07 addsd xmm7, xmm1
    } else {
        w = width + 0.0 * width;    // 0x50FE40 mulsd xmm7, xmm0 ; 0x50FE44 addsd xmm0, xmm7
        h = 0.0 + height;           // 0x50FE48 addsd xmm7, xmm1
    }

    // 0x50FE0B..0x50FE1D: the pair is (width, height) and it is folded into the box as one more point.
    pair[0] = w;
    pair[1] = h;
    boxAccumulate(box, pair);

    return box;   // 0x50FE28 `mov rax, rsi`
}

}  // namespace lcns
