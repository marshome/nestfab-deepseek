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

const char* getUserStringAt1B8(void* part) {
    return static_cast<const char*>(loadPointer(part, 0x1B8));   // the same load as 0xC5E0, without the logger call
}

void setByteAtF8(void* object, int value) {
    // `setne` writes 1 or 0, never the argument: a 32-bit test, so 256 stores 1.
    static_cast<unsigned char*>(object)[0xF8] = (value != 0) ? 1u : 0u;
}

void setDoubleAndFlag(void* object, int flag, double value) {
    std::memcpy(static_cast<unsigned char*>(object) + 0x100, &value, sizeof(value));
    static_cast<unsigned char*>(object)[0xF9] = (flag != 0) ? 1u : 0u;
}

void* getSolutionIdentity(void* handle) {
    return handle;   // the body is `mov rax, rbx; ret` after the logger call: no memory is touched
}

void setIntField(void* object, int value, std::size_t offset) {
    // The store is a 32-bit one: `mov dword ptr [rsi + OFF], ebx`. Nothing else in these functions touches memory.
    std::memcpy(static_cast<unsigned char*>(object) + offset, &value, sizeof(value));
}

void setShearMode(void* object, int value) { setIntField(object, value, 0x44); }   // SetShearMode

void setNoMixPreference(void* object, int value) { setIntField(object, value, 0x18); }   // CNS_SetNoMixPreference

void setNoSheetMixPreference(void* object, int value) { setIntField(object, value, 0x1C); }   // CNS_SetNoSheetMixPreference

void setShearRepulseFromBorders(void* object, int value) { setIntField(object, value, 0x58); }   // SetShearRepulseFromBorders

void unlockLaunchingOrder(void* object, int value) { setIntField(object, value, 0x244); }   // UnLockLaunchingOrder

void setInt_1FC(void* object, int value) { setIntField(object, value, 0x1FC); }   // SetLocalMaximumIterations

const char* getPartUserString(void* part) {
    return static_cast<const char*>(loadPointer(part, 0x1B8));
}

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
