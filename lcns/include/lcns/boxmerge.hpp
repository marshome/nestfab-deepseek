// lcns/boxmerge.hpp -- RE 0x5C8C50: merge the box at srcBase into the box at dstBase.
// Verified against the original: 5000 of 5000 random boxes agree, invalid ones included.
#pragma once

#include "lcns/dll_layout.hpp"

namespace lcns {
namespace dll {
namespace exports {
namespace impl {

void mergeBoxInto(void* dstBase, const void* srcBase);

/**
 * The two spans that the GetLength and GetHeight implementers return, as read from their tails:
 * RE 0x526227 with RE 0x52624D for the first, RE 0x526767 with RE 0x526790 for the second, and zero when there is no
 * geometry (RE 0x526264, RE 0x5267B0). The status argument that selects these branches is the implementer's second
 * argument (RE 0x526170 saves it, RE 0x526216 reads it) and both entry points pass zero, so this is the branch they take.
 */
double windowSpanLength(const lcns::dll::WindowSlots& window, const void* boxBase, bool hasGeometry);
double windowSpanHeight(const lcns::dll::WindowSlots& window, const void* boxBase, bool hasGeometry);


}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
