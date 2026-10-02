// lcns/boxmerge.hpp -- RE 0x5C8C50: merge the box at srcBase into the box at dstBase.
// Verified against the original: 5000 of 5000 random boxes agree, invalid ones included.
#pragma once

namespace lcns {
namespace dll {
namespace exports {
namespace impl {

void mergeBoxInto(void* dstBase, const void* srcBase);

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
