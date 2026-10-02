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

/**
 * A third element family. 0x8C4530 counts a container of these: it shifts the difference by four and multiplies by
 * 0xAAAAAAAAAAAAAAAB, which is inv(3) mod 2**64, so the element is 16 * 3 = 48 bytes. With this the module's three
 * counting constants are 39, 15 and 3, each derived from an element size rather than written down.
 */
struct Element48 {
    unsigned char opaque[48];
};
static_assert(sizeof(Element48) == 48, "RE 0x8C4530");
static_assert(modularInverse(3) == 0xAAAAAAAAAAAAAAABull, "the constant 0x8C4530 multiplies by");

struct Element216 {
    unsigned char opaque[216];
};
static_assert(sizeof(Element216) == 216, "RE 0x4F73E0");
static_assert(modularInverse(27) == 0x84BDA12F684BDA13ull, "the constant 0x4F73E0 multiplies by");

/**
 * The window object that GetLength and GetHeight read.
 *
 * Both implementers build it through 0x4F9200 and 0x5CD800, then subtract one of four pairs of these fields. The pairs are
 * 0x10 apart inside a pair and the four pairs sit at 0x08, 0x10, 0x18, 0x20 on the low side and 0x38, 0x40, 0x48, 0x50 on
 * the high side, so the window holds two dimension records. Each assertion below names the instruction that produces the
 * read it pins.
 */
struct WindowSlots {
    unsigned char opaque00[0x08];
    double slot08;   // 0x526230 and 0x526770 (status false in both implementers)
    double slot10;   // 0x526770 minus, the low side of the second record
    double slot18;   // 0x526227 (0x526160, status true) and rsi+0x18 of the first record
    double slot20;   // 0x526767 (0x5266A0, status true) and rsi+0x20
    unsigned char opaque28[0x10];
    double slot38;   // 0x52624D (0x526160, status true)
    double slot40;   // 0x526767 (0x5266A0, status true)
    double slot48;   // 0x526227 (0x526160, status false)
    double slot50;   // 0x526767 (0x5266A0, status false)
};
static_assert(offsetof(WindowSlots, slot08) == 0x08, "RE 0x526230");
static_assert(offsetof(WindowSlots, slot10) == 0x10, "RE 0x526770");
static_assert(offsetof(WindowSlots, slot18) == 0x18, "RE 0x526227");
static_assert(offsetof(WindowSlots, slot20) == 0x20, "RE 0x526767");
static_assert(offsetof(WindowSlots, slot38) == 0x38, "RE 0x52624D");
static_assert(offsetof(WindowSlots, slot40) == 0x40, "RE 0x526767");
static_assert(offsetof(WindowSlots, slot48) == 0x48, "RE 0x526227");
static_assert(offsetof(WindowSlots, slot50) == 0x50, "RE 0x526767");

/** Where the status test in the two implementers reads its operand, as read from the code but NOT yet traced to a writer. */
// The status the two implementers test is their SECOND ARGUMENT. RE 0x526170 saves edx at rsp+0x108 and RE 0x526216 passes that address to the status function, so it is not a window field, and both entry points call with zero.

/**
 * The cached box that 0x4F9200 returns. RE 0x4F920B tests the byte at +0x100 and RE 0x4F9217 returns rcx+0x108, so the
 * object carries an initialisation byte and then a box. The box bytes follow the same layout as this project's box model:
 * flag, minX, minY, maxX, maxY, each eight bytes apart after the flag.
 */
struct CachedBoxCarrier {
    unsigned char opaque00[0x100];
    unsigned char initialised;   // +0x100, RE 0x4F920B (the same field UnknownFlagCarrier calls value100)
    unsigned char opaque01[0x07];
    unsigned char box[0x28];     // +0x108, RE 0x4F9217: flag, minX, minY, maxX, maxY
};
static_assert(offsetof(CachedBoxCarrier, initialised) == 0x100, "RE 0x4F920B");
static_assert(offsetof(CachedBoxCarrier, box) == 0x108, "RE 0x4F9217");

/**
 * The option object the mode setters write. Offsets come from the exports themselves: RE 0xDE69 writes +0x1C,
 * RE 0xDD49 writes +0x20, RE 0xDD79 writes +0x21, RE 0xDDA9 writes +0x40, and RE 0xDE07 with RE 0xDE0A write +0x48 and
 * +0x44 as 32-bit values.
 */
struct OptionFlagCarrier {
    unsigned char opaque00[0x1C];
    unsigned char flag1C;      // +0x1C, RE 0xDE69, SetPartCommonCutMode (ordinal 166)
    unsigned char opaque1D[0x03];
    unsigned char flag20;      // +0x20, RE 0xDD49, CNS_SetFloatingMode (ordinal 182)
    unsigned char flag21;      // +0x21, RE 0xDD79, CNS_SetOriginPackingMode (ordinal 312)
    unsigned char flag22;      // +0x22, RE 0x1048F, SetReorganizeBiggestPartNearOrigin (ordinal 336)
    unsigned char flag23;      // +0x23, RE 0x104BF, SetReorganizeLongestPartNearOrigin (ordinal 338)
    unsigned char opaque24[0x1C];
    unsigned char flag40;      // +0x40, RE 0xDDA9, SetFillLastNestingStrategy (ordinal 144)
    unsigned char flag41;      // +0x41, RE 0x1045F, CNS_SetEvaluateIntermediateNestingsAsLast (ordinal 316)
    unsigned char opaque42[0x02];
    std::uint32_t field44;     // +0x44, RE 0xDE0A, SetPartialShearMode (ordinal 330) and the existing setShearMode
    std::uint32_t field48;     // +0x48, RE 0xDE07, SetPartialShearMode (ordinal 330)
};
static_assert(offsetof(OptionFlagCarrier, flag1C) == 0x1C, "RE 0xDE69");
static_assert(offsetof(OptionFlagCarrier, flag20) == 0x20, "RE 0xDD49");
static_assert(offsetof(OptionFlagCarrier, flag21) == 0x21, "RE 0xDD79");
static_assert(offsetof(OptionFlagCarrier, flag40) == 0x40, "RE 0xDDA9");
static_assert(offsetof(OptionFlagCarrier, field44) == 0x44, "RE 0xDE0A");
static_assert(offsetof(OptionFlagCarrier, field48) == 0x48, "RE 0xDE07");
static_assert(offsetof(OptionFlagCarrier, flag22) == 0x22, "RE 0x1048F");
static_assert(offsetof(OptionFlagCarrier, flag23) == 0x23, "RE 0x104BF");
static_assert(offsetof(OptionFlagCarrier, flag41) == 0x41, "RE 0x1045F");

/**
 * The object SetObjective and SetShearGap write: a 32-bit objective at +0x08 (RE 0xCEE3) and a double gap at +0x50
 * (RE 0xCF0D). Separate from the option flag carrier because the two exports write different offsets of a different
 * shape, and nothing read so far connects them.
 */
struct SolverOptionCarrier {
    unsigned char opaque00[0x08];
    std::int32_t objective;    // +0x08, RE 0xCEE3
    unsigned char opaque0C[0x44];
    double shearGap;           // +0x50, RE 0xCF0D
};
static_assert(offsetof(SolverOptionCarrier, objective) == 0x08, "RE 0xCEE3");
static_assert(offsetof(SolverOptionCarrier, shearGap) == 0x50, "RE 0xCF0D");

/** The two bytes ForcePartInsideHole sets: RE 0xC627 writes +0x20A and RE 0xC62E writes +0x20B. */
struct HoleForceCarrier {
    unsigned char opaque00[0x20A];
    unsigned char insideHole;   // +0x20A, RE 0xC627, set to 1
    unsigned char something;    // +0x20B, RE 0xC62E, set to 0
};
static_assert(offsetof(HoleForceCarrier, insideHole) == 0x20A, "RE 0xC627");
static_assert(offsetof(HoleForceCarrier, something) == 0x20B, "RE 0xC62E");

}  // namespace dll
}  // namespace lcns
