// lcns/src/exports_impl.cpp -- the recovered bodies. See lcns/exports_impl.hpp for what each rests on.

#include "lcns/exports_impl.hpp"

#include <cstring>

namespace lcns {
namespace dll {
namespace exports {
namespace impl {
namespace {

std::uint64_t loadQword(const void* base, std::size_t offset) {
    std::uint64_t v = 0;
    std::memcpy(&v, static_cast<const unsigned char*>(base) + offset, sizeof(v));
    return v;
}

void* loadPointer(const void* base, std::size_t offset) {
    void* v = nullptr;
    std::memcpy(&v, static_cast<const unsigned char*>(base) + offset, sizeof(v));
    return v;
}

/** The two counts share a shape: (end - begin) >> 3, then the modular-inverse multiply that divides by the stride/8. */
std::size_t countWithInverse(std::uint64_t begin, std::uint64_t end, std::uint64_t inverse) {
    const std::uint64_t units = (end - begin) >> 3u;
    return static_cast<std::size_t>(units * inverse);
}

}  // namespace

std::size_t getNumberOfNestings(void* order) {
    // 0x50 / 0x58 are the container's begin and end; the stride is 312 bytes, so the inverse is that of 39.
    return countWithInverse(loadQword(order, 0x50), loadQword(order, 0x58), 0x6F96F96F96F96F97ull);
}

std::size_t getNumberOfNestedParts(void* order) {
    // 0x51D0C0 gives the container's address as sub+0x28; the stride is 120 bytes, so the inverse is that of 15.
    void* sub = loadPointer(order, 0x08);
    return countWithInverse(loadQword(sub, 0x28), loadQword(sub, 0x30), 0xEEEEEEEEEEEEEEEFull);
}

std::uint32_t getMultiplicity(void* part) {
    // 0x51D090 is `mov eax, dword ptr [rcx + 0x20]` -- a 32-bit load, not a 64-bit one.
    void* sub = loadPointer(part, 0x08);
    std::uint32_t v = 0;
    std::memcpy(&v, static_cast<const unsigned char*>(sub) + 0x20, sizeof(v));
    return v;
}

const char* getPartUserString(void* part) {
    return static_cast<const char*>(loadPointer(part, 0x1B8));
}

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
