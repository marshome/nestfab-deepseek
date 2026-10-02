// lcns/src/exports.cpp -- the runtime half of the C ABI layer.
//
// The generated table and definitions live in src/api_exports.cpp; this file holds what a hand can write: the counter of
// calls that reached an unrecovered entry point, the lookup of a forwarded implementation, and the bridge to the
// embedded original bytes. The split is deliberate -- regenerating the table must never erase a recovered behaviour, and
// recovering a behaviour must never require editing generated code.

#include "lcns/exports.hpp"

#include "lcns/embedded.hpp"

#include <cstring>

namespace lcns {
namespace dll {
namespace exports {
namespace {

std::size_t g_notReversedCount = 0;
const Entry* g_lastNotReversed = nullptr;

}  // namespace

// Provided by the generated translation unit, so the table and the definitions stay in one place. Declared at this
// namespace's scope -- inside the anonymous namespace above they would name a different entity and would not link.
extern const Forwarding kForwarding[];
extern const std::size_t kForwardingCount;

void notReversed(std::size_t index) {
    ++g_notReversedCount;
    const Entry* e = entries();
    g_lastNotReversed = (index < count()) ? &e[index] : nullptr;
}

std::size_t notReversedCount() { return g_notReversedCount; }

const Entry* lastNotReversed() { return g_lastNotReversed; }

std::size_t forwardedCount() { return kForwardingCount; }

Status statusOf(std::size_t index) { return forwards(index) ? Status::Forwarded : Status::NotReversed; }

const Forwarding* forwarding(std::size_t index) {
    return index < kForwardingCount ? &kForwarding[index] : nullptr;
}

std::size_t forwardingCount() { return kForwardingCount; }

bool forwards(std::size_t index) {
    const Entry* e = entries();
    if (index >= count()) {
        return false;
    }
    for (std::size_t i = 0; i < kForwardingCount; ++i) {
        if (kForwarding[i].ordinal0 == e[index].ordinal0) {
            return true;
        }
    }
    return false;
}

OriginalBytes originalBytesOf(std::size_t index) {
    OriginalBytes out{nullptr, 0u, nullptr};
    const Entry* e = entries();
    if (index >= count()) {
        return out;
    }
    const embedded::Block* b = embedded::find(e[index].rva);
    if (b == nullptr) {
        return out;
    }
    out.bytes = b->bytes;
    out.size = b->size;
    out.sha256 = b->sha256;
    return out;
}

}  // namespace exports
}  // namespace dll
}  // namespace lcns
