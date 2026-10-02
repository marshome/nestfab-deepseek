// lcns/dll_layout.hpp -- the original module's objects as DATA STRUCTURES.
//
// Each field names the rva that establishes its offset and every offset is asserted by the compiler, so a wrong model
// stops the build instead of reading the wrong bytes.
//
// The types are SPLIT because the evidence requires it: [+0x58] is the nesting container's end POINTER in 0xB0C0 and a
// 32-bit setter field in 0x0DE20, so those functions do not share an object type. The inferred signatures in
// lcns/detail/api_typed.inc suggest they do; that file says its signatures are inferred, and this contradiction is why
// they are not relied on. See re/EXPORT_IMPLS.md.

#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {
namespace dll {

/** Modular inverse modulo 2**64 by Newton iteration; valid for the odd strides used here. */
constexpr std::uint64_t modularInverse(std::uint64_t a) {
    std::uint64_t x = a;
    for (int i = 0; i < 6; ++i) {
        x *= 2u - a * x;
    }
    return x;
}

// The constants the assembly multiplies by are DERIVED from the element sizes (312/8 = 39, 120/8 = 15), not transcribed.
static_assert(modularInverse(39) == 0x6F96F96F96F96F97ull, "0xB0C0's constant must follow from 39");
static_assert(modularInverse(15) == 0xEEEEEEEEEEEEEEEFull, "0xB190's constant must follow from 15");

/** The 312-byte element 0xB0C0 counts -- the same stride 0x50FD40's accumulator walks. Interior not recovered. */
struct NestingElement {
    unsigned char opaque[312];
};
static_assert(sizeof(NestingElement) == 312, "RE 0xB0C0");

/** The 120-byte element 0xB190 counts. */
struct NestedPartElement {
    unsigned char opaque[120];
};
static_assert(sizeof(NestedPartElement) == 120, "RE 0xB190");

/**
 * A contiguous container of the module's own making: begin, end, capacity.
 *
 * size() is not a division, because the original does not divide: it takes the byte difference, shifts by three and
 * multiplies by the modular inverse of the element size in eight-byte units. That is exact for a well-formed container
 * and differs from a division for a malformed one; reproducing it keeps both cases equal to the original. The element
 * size is the only input, so no magic constant appears in the code.
 */
template <class T>
struct RawVector {
    T* begin;
    T* end;
    T* capacity;

    std::size_t size() const {
        static_assert(sizeof(T) % 8 == 0, "the original works in eight-byte units");
        const std::uint64_t bytes = reinterpret_cast<std::uint64_t>(end) - reinterpret_cast<std::uint64_t>(begin);
        return static_cast<std::size_t>((bytes >> 3u) * modularInverse(sizeof(T) / 8));
    }
};

/** [order+0x08]: 0x51D090 reads its +0x20; 0x51D0C0 hands out its +0x28. */
struct SubObject {
    unsigned char opaque00[0x20];
    std::uint32_t multiplicity;          // +0x20  RE 0x51D090
    unsigned char opaque24[0x04];
    RawVector<NestedPartElement> parts;  // +0x28  RE 0x51D0C0
};
static_assert(offsetof(SubObject, multiplicity) == 0x20, "RE 0x51D090");
static_assert(offsetof(SubObject, parts) == 0x28, "RE 0x51D0C0");

/** The object that owns the nesting container; nothing past the container is claimed. */
struct NestingOwner {
    unsigned char opaque00[0x08];
    SubObject* sub;                      // +0x08  RE 0xB190, 0xB100
    unsigned char opaque10[0x40];
    RawVector<NestingElement> nestings;  // +0x50  RE 0xB0C0
};
static_assert(offsetof(NestingOwner, sub) == 0x08, "RE 0xB190");
static_assert(offsetof(NestingOwner, nestings) == 0x50, "RE 0xB0C0");

/** The part handle. */
struct PartObject {
    unsigned char opaque00[0x08];
    SubObject* sub;                    // +0x08  RE 0xB100
    unsigned char opaque10[0x1A8];
    const char* userString;            // +0x1B8 RE 0xC5E0, 0x16CF0
};
static_assert(offsetof(PartObject, sub) == 0x08, "RE 0xB100");
static_assert(offsetof(PartObject, userString) == 0x1B8, "RE 0xC5E0");

/** ONLY the offsets the int setters write -- a carrier, not "the order object", which is what the contradiction leaves open. */
struct IntFieldCarrier {
    unsigned char opaque00[0x18];
    std::int32_t field18;      // RE 0x0D310
    std::int32_t field1C;      // RE 0x0D340
    unsigned char opaque20[0x24];
    std::int32_t field44;      // RE 0x0DDC0
    unsigned char opaque48[0x10];
    std::int32_t field58;      // RE 0x0DE20
    unsigned char opaque5C[0x1A0];
    std::int32_t field1FC;     // RE 0x0D400
    unsigned char opaque200[0x44];
    std::int32_t field244;     // RE 0x0D430
};
static_assert(offsetof(IntFieldCarrier, field18) == 0x18, "RE 0x0D310");
static_assert(offsetof(IntFieldCarrier, field1C) == 0x1C, "RE 0x0D340");
static_assert(offsetof(IntFieldCarrier, field44) == 0x44, "RE 0x0DDC0");
static_assert(offsetof(IntFieldCarrier, field58) == 0x58, "RE 0x0DE20");
static_assert(offsetof(IntFieldCarrier, field1FC) == 0x1FC, "RE 0x0D400");
static_assert(offsetof(IntFieldCarrier, field244) == 0x244, "RE 0x0D430");

/** The two unlabelled setters take a type that is NOT recoverable (no label, no typed signature). */
struct UnknownFlagCarrier {
    unsigned char opaque00[0xF8];
    unsigned char flagF8;      // RE 0x0AFF0
    unsigned char flagF9;      // RE 0x0B000
    unsigned char opaqueFA[0x06];
    double value100;           // RE 0x0B000
};
static_assert(offsetof(UnknownFlagCarrier, flagF8) == 0xF8, "RE 0x0AFF0");
static_assert(offsetof(UnknownFlagCarrier, flagF9) == 0xF9, "RE 0x0B000");
static_assert(offsetof(UnknownFlagCarrier, value100) == 0x100, "RE 0x0B000");

/**
 * The object behind GetPartWithBadGeometry (ordinal 29, rva 0xB510).
 *
 * Kept separate on purpose: the export has a log label but no typed signature a reader can trust, so only the two offsets
 * its code touches are known. Claiming they are fields of PartObject would be a guess.
 */
struct BadGeometryCarrier {
    unsigned char opaque00[0x4C];
    std::uint32_t status;      // +0x4C, RE 0xB524: only the value 1 continues
    unsigned char opaque50[0x50];
    void* geometry;            // +0xA0, RE 0xB52E: returned when the status is 1
};
static_assert(offsetof(BadGeometryCarrier, status) == 0x4C, "RE 0xB524");
static_assert(offsetof(BadGeometryCarrier, geometry) == 0xA0, "RE 0xB52E");

}  // namespace dll
}  // namespace lcns
