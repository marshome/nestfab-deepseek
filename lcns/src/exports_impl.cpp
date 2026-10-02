// lcns/src/exports_impl.cpp -- the recovered bodies, written against the model in lcns/dll_layout.hpp.
//
// No offset appears here: fields are named, and the layout header asserts each sits where the assembly read it. What stays
// explicit is the one behavioural detail the model must not hide -- that a container's size is computed as RawVector::size
// computes it (byte difference times the derived inverse), not as a division.

#include "lcns/exports_impl.hpp"
#include <cstring>
#include <thread>

namespace lcns {
namespace dll {
namespace exports {
namespace impl {

std::size_t getNumberOfNestings(void* order) {
    return static_cast<NestingOwner*>(order)->nestings.size();
}

std::size_t getNumberOfNestedParts(void* order) {
    return static_cast<NestingOwner*>(order)->sub->parts.size();
}

std::uint32_t getMultiplicity(void* part) {
    return static_cast<PartObject*>(part)->sub->multiplicity;
}

const char* getPartUserString(void* part) {
    return static_cast<PartObject*>(part)->userString;
}

const char* getUserStringAt1B8(void* part) {
    return static_cast<PartObject*>(part)->userString;
}

void setByteAtF8(void* object, int value) {
    static_cast<UnknownFlagCarrier*>(object)->flagF8 = (value != 0) ? 1u : 0u;
}

void setDoubleAndFlag(void* object, int flag, double value) {
    auto* carrier = static_cast<UnknownFlagCarrier*>(object);
    carrier->value100 = value;
    carrier->flagF9 = (flag != 0) ? 1u : 0u;
}

void* getSolutionIdentity(void* handle) {
    return handle;
}

void* getPartWithBadGeometry(void* object) {
    auto* carrier = static_cast<BadGeometryCarrier*>(object);
    if (carrier->status != 1u) {
        return nullptr;
    }
    return carrier->geometry;
}

void setFillLastNestingStrategy(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag40 = (value != 0) ? 1 : 0;   // RE 0xDDA9: setne
}

void setPartCommonCutMode(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag1C = (value != 0) ? 1 : 0;   // RE 0xDE69: setne
}

void setFloatingMode(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag20 = (value != 0) ? 1 : 0;   // RE 0xDD49: setne
}

void setOriginPackingMode(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag21 = (value != 0) ? 1 : 0;   // RE 0xDD79: setne
}

void setPartialShearMode(void* object, int value) {
    OptionFlagCarrier* carrier = static_cast<OptionFlagCarrier*>(object);
    carrier->field48 = static_cast<std::uint32_t>(value);   // RE 0xDE07
    carrier->field44 = static_cast<std::uint32_t>(value);   // RE 0xDE0A, the same field setShearMode writes
}

void setEvaluateIntermediateNestingsAsLast(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag41 = (value != 0) ? 1 : 0;   // RE 0x1045F: setne
}

void setReorganizeBiggestPartNearOrigin(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag22 = (value != 0) ? 1 : 0;   // RE 0x1048F: setne
}

void setReorganizeLongestPartNearOrigin(void* object, int value) {
    static_cast<OptionFlagCarrier*>(object)->flag23 = (value != 0) ? 1 : 0;   // RE 0x104BF: setne
}

void forcePartInsideHole(void* part) {
    HoleForceCarrier* carrier = static_cast<HoleForceCarrier*>(part);
    carrier->insideHole = 1;   // RE 0xC627
    carrier->something = 0;    // RE 0xC62E
}

void setObjective(void* options, int value) {
    static_cast<SolverOptionCarrier*>(options)->objective = value;   // RE 0xCEE3 stores the integer itself
}

void setShearGap(void* options, double gap) {
    static_cast<SolverOptionCarrier*>(options)->shearGap = gap;      // RE 0xCF0D
}

std::size_t noFitGetNumberOfExternalPolygons(const void* owner) {
    const unsigned char* o = static_cast<const unsigned char*>(owner);
    std::uintptr_t begin = 0;   // RE 0x89E7: [rbx]
    std::uintptr_t end = 0;     // RE 0x89F5 reads [rbx + 8]
    std::memcpy(&begin, o, sizeof(begin));
    std::memcpy(&end, o + 8, sizeof(end));
    const std::uint64_t units = static_cast<std::uint64_t>(end - begin) >> 4;   // RE 0x89F8: sar 4
    // RE 0x89EB multiplies by 0xAAAAAAAAAAAAAAAB, which is the modular inverse of three: 48-byte elements.
    return static_cast<std::size_t>(units * lcns::dll::modularInverse(3));
}

void setLocalEngine(void* object, int value) {
    LocalEngineCarrier* carrier = static_cast<LocalEngineCarrier*>(object);
    const unsigned int bits = static_cast<unsigned int>(value);
    // RE 0xD38B: not, then RE 0xD399: and 1 -- the complement of the low bit, stored as a byte
    carrier->engineLo = static_cast<unsigned char>((~bits) & 1u);
    // RE 0xD389: shr 1, RE 0xD38D: xor 1, RE 0xD396: and 1 -- the complement of bit one
    carrier->engineHi = static_cast<unsigned char>(((bits >> 1) ^ 1u) & 1u);
}

unsigned platformConcurrency() {
    // RE 0x8AB0E0 calls the import stub 0x63F6B0 and clamps a negative result to zero. The stub is the platform, so this
    // is where the platform is asked, and it is the only platform number in these two exports.
    const unsigned int value = std::thread::hardware_concurrency();
    return value;   // hardware_concurrency returns zero when the value is unknown, which matches the stub contract
}

unsigned clampMaximumThreads(unsigned platformValue, int requested) {
    // RE 0xB5B79: if the count is zero use one. Both helpers do this, so it applies to either branch.
    const unsigned int floored = (platformValue == 0u) ? 1u : platformValue;
    if (requested == 0) {
        return floored;                                    // RE 0xD3E2: the branch that ignores the argument
    }
    const unsigned int want = static_cast<unsigned int>(requested);
    return (floored > want) ? want : floored;               // RE 0xD3D2: cmova takes the smaller of the two
}

void setLocalMaximumThreads(void* object, int value) {
    static_cast<LocalEngineCarrier*>(object)->maxThreads = clampMaximumThreads(platformConcurrency(), value);
}

void setShearMode(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field44 = value; }
void setNoMixPreference(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field18 = value; }
void setNoSheetMixPreference(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field1C = value; }
void setShearRepulseFromBorders(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field58 = value; }
void unlockLaunchingOrder(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field244 = value; }
void setInt_1FC(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field1FC = value; }

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
