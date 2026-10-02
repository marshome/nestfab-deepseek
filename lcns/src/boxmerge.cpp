// lcns/src/boxmerge.cpp -- RE 0x5C8C50: merging two min/max boxes.
//
// The worker and its field helpers are the model verified against the original: 5000 of 5000 random boxes agree,
// invalid ones included, after the INIT path was corrected. See re/MERGE_MAX_X.md: on that path the original
// jumps to 0x5C8CDB, the maxX check inside the second pass, before the tail at 0x5C8CE7. They are copied here
// UNCHANGED and only wrapped, so the verified logic cannot drift while being moved.

#include "lcns/boxmerge.hpp"
#include "lcns/boxacc.hpp"   // kBoxMinX and friends live here; without this the worker cannot compile

#include <cstring>

static double loadD(const void* b, std::size_t o) {
    double v = 0.0;
    std::memcpy(&v, static_cast<const unsigned char*>(b) + o, sizeof(v));
    return v;
}
static void storeD(void* b, std::size_t o, double v) {
    std::memcpy(static_cast<unsigned char*>(b) + o, &v, sizeof(v));
}

static void boxMergeWorker(unsigned char* dst, const unsigned char* src) {
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

namespace lcns {
namespace dll {
namespace exports {
namespace impl {

void mergeBoxInto(void* dstBase, const void* srcBase) {
    boxMergeWorker(static_cast<unsigned char*>(dstBase), static_cast<const unsigned char*>(srcBase));
}


double windowSpanLength(const lcns::dll::WindowSlots& window, const void* boxBase, bool hasGeometry) {
    if (!hasGeometry) {
        return 0.0;   // RE 0x526264
    }
    // RE 0x526244 with RE 0x52624D: the merged box maxX minus the window low value.
    double maxX = 0.0;
    std::memcpy(&maxX, static_cast<const unsigned char*>(boxBase) + 0x18, sizeof(maxX));
    return maxX - window.slot08;
}

double windowSpanHeight(const lcns::dll::WindowSlots& window, const void* boxBase, bool hasGeometry) {
    if (!hasGeometry) {
        return 0.0;   // RE 0x5267B0
    }
    // RE 0x526790 with RE 0x5267A2: the merged box maxY minus the window low value.
    double maxY = 0.0;
    std::memcpy(&maxY, static_cast<const unsigned char*>(boxBase) + 0x20, sizeof(maxY));
    return maxY - window.slot10;
}

void copyPair38(void* destination, const void* element) {
    const unsigned char* src = static_cast<const unsigned char*>(element);
    unsigned char* dst = static_cast<unsigned char*>(destination);
    double first = 0.0;    // RE 0x5203D0: r9 = [rdx + 0x38]
    double second = 0.0;   // RE 0x5203D4: r10 = [rdx + 0x40]
    std::memcpy(&first, src + 0x38, sizeof(first));
    std::memcpy(&second, src + 0x40, sizeof(second));
    std::memcpy(dst, &first, sizeof(first));        // RE 0x5203DB: [rcx] = r9
    std::memcpy(dst + 8, &second, sizeof(second));  // RE 0x5203DE: [rcx + 8] = r10
}

void copyPair28(void* destination, const void* element) {
    const unsigned char* src = static_cast<const unsigned char*>(element);
    unsigned char* dst = static_cast<unsigned char*>(destination);
    double first = 0.0;    // RE 0x5203F0: r9 = [rdx + 0x28]
    double second = 0.0;   // RE 0x5203F4: r10 = [rdx + 0x30]
    std::memcpy(&first, src + 0x28, sizeof(first));
    std::memcpy(&second, src + 0x30, sizeof(second));
    std::memcpy(dst, &first, sizeof(first));        // RE 0x5203FB: [rcx] = r9
    std::memcpy(dst + 8, &second, sizeof(second));  // RE 0x5203FE: [rcx + 8] = r10
}

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
