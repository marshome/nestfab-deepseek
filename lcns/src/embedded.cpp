// lcns/src/embedded.cpp -- lookups over the embedded original blocks. See include/lcns/embedded.hpp for the policy.
//
// Nothing here executes the originals; it only answers questions about the registry, so a caller can tell a block that
// has an executable copy from one that is carried as bytes with a reason. The differential tests in tests/test_embedded
// are the only place that calls kOrigTable.

#include "lcns/embedded.hpp"

namespace lcns {
namespace embedded {

const Block* find(std::uintptr_t rva) {
    for (std::size_t i = 0; i < kBlockCount; ++i) {
        if (kBlocks[i].rva == rva) {
            return &kBlocks[i];
        }
    }
    return nullptr;
}

Status statusOf(std::uintptr_t rva) {
    const Block* b = find(rva);
    return b ? b->status : Status::CommentOnly;  // an unknown block is certainly not known to be callable
}

std::size_t callableCount() {
    std::size_t n = 0;
    for (std::size_t i = 0; i < kBlockCount; ++i) {
        if (kBlocks[i].status == Status::Callable) {
            ++n;
        }
    }
    return n;
}

std::size_t commentOnlyCount() {
    return kBlockCount - callableCount();
}

std::size_t embeddedBytes() {
    std::size_t n = 0;
    for (std::size_t i = 0; i < kBlockCount; ++i) {
        n += kBlocks[i].size;
    }
    return n;
}

RawFn originalOf(std::uintptr_t rva) {
    std::size_t index = 0;
    for (std::size_t i = 0; i < kBlockCount; ++i) {
        if (kBlocks[i].status != Status::Callable) {
            continue;
        }
        if (kBlocks[i].rva == rva) {
            return index < kOrigTableCount ? kOrigTable[index] : nullptr;
        }
        ++index;
    }
    return nullptr;
}

}  // namespace embedded
}  // namespace lcns
