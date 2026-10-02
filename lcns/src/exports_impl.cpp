// lcns/src/exports_impl.cpp -- the recovered bodies, written against the model in lcns/dll_layout.hpp.
//
// No offset appears here: fields are named, and the layout header asserts each sits where the assembly read it. What stays
// explicit is the one behavioural detail the model must not hide -- that a container's size is computed as RawVector::size
// computes it (byte difference times the derived inverse), not as a division.

#include "lcns/exports_impl.hpp"
#include <cstring>
#include <thread>
#include <string>

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

namespace {
// RE 0x60A610 writes the byte at rip + 0x518D3A. The address is the original image's and cannot be reproduced, but the
// value can, and that is what any caller can observe.
unsigned char g_moduleSwitch = 0;
}  // namespace

void setModuleSwitch(int value) {
    // RE 0xAFE0: test, setne, movzx -- any non-zero becomes exactly one
    g_moduleSwitch = (value != 0) ? static_cast<unsigned char>(1) : static_cast<unsigned char>(0);
}

unsigned char moduleSwitch() {
    return g_moduleSwitch;
}

void setUserStringAt1B8(void* object, const char* text) {
    // RE 0x16CB0: the length comes from the strlen stub at 0x63F238, and the string sits at +0x1B8, so this is an
    // assignment of a C string into a std::string, done with the same type the original uses.
    auto* holder = reinterpret_cast<std::string*>(static_cast<unsigned char*>(object) + 0x1B8);
    *holder = (text != nullptr) ? text : "";
}

void setShearMode(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field44 = value; }
void setNoMixPreference(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field18 = value; }
void setNoSheetMixPreference(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field1C = value; }
void setShearRepulseFromBorders(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field58 = value; }
void unlockLaunchingOrder(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field244 = value; }
void setInt_1FC(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field1FC = value; }


// ---------------------------------------------------------------- the nine setters (RE round 537)

namespace {

/** A field and the "given" byte this module writes four bytes before it. RE 0xEA09/0xEA0D and its four siblings. */
struct FieldWriter {
    unsigned char* base;
    void writeByte(std::size_t offset, unsigned char value) const {
        std::memcpy(base + offset, &value, sizeof(value));
    }
    void writeDword(std::size_t offset, std::uint32_t value) const {
        std::memcpy(base + offset, &value, sizeof(value));
    }
    void writeDouble(std::size_t offset, double value) const {
        std::memcpy(base + offset, &value, sizeof(value));
    }
};

}  // namespace

void setOrigin_0D050(void* order, int value) {
    FieldWriter{static_cast<unsigned char*>(order)}.writeDword(0x0C, static_cast<std::uint32_t>(value));  // RE 0xD119
}

void setCommonCutCuttingPreference_0EC90(void* order, int value) {
    const FieldWriter w{static_cast<unsigned char*>(order)};
    w.writeByte(0x88, 1);                                        // RE 0xED59
    w.writeDword(0x8C, static_cast<std::uint32_t>(value));       // RE 0xED60
}

void setMultiplicityPreference_0D1A0(void* order, int choice) {
    // The four doubles are read out of the image, and they are data rather than code:
    //   RE 0xD248 loads 0x9AD6D8 = 0.25, the default        RE 0xD262 loads 0x9AD6E0 = 0.05
    //   RE 0xD294 loads 0x9AD6E8 = 0.001 for choice 1      RE 0xD2B5 loads 0x9AD6D0 = 2.0 for choice 4
    // The branches are 0xD253 (choice == 3), 0xD28F (choice == 1) and 0xD2B0 (choice == 4); every other value falls
    // through to the default, which is why a switch is written rather than a table.
    double chosen = 0.25;                                        // RE 0x9AD6D8
    if (choice == 3) {
        chosen = 0.05;                                           // RE 0x9AD6E0
    } else if (choice == 1) {
        chosen = 0.001;                                          // RE 0x9AD6E8
    } else if (choice == 4) {
        chosen = 2.0;                                            // RE 0x9AD6D0
    }
    FieldWriter{static_cast<unsigned char*>(order)}.writeDouble(0x10, chosen);   // RE 0xD26A and its siblings
}

void setAutomaticStop_0E010(void* order, int value) {
    FieldWriter{static_cast<unsigned char*>(order)}.writeDword(0x240, static_cast<std::uint32_t>(value));  // RE 0xE0D9
}

void setCommonCutSafetyPreference_0E940(void* order, int value) {
    const FieldWriter w{static_cast<unsigned char*>(order)};
    w.writeByte(0x68, 1);                                        // RE 0xEA09
    w.writeDword(0x6C, static_cast<std::uint32_t>(value));       // RE 0xEA0D
}

void setMultiTorchCuttingPreference_0F130(void* order, int value) {
    const FieldWriter w{static_cast<unsigned char*>(order)};
    w.writeByte(0x98, 1);                                                          // RE 0xF225
    w.writeByte(0xA0, (value > 0) ? 1 : 0);                                        // RE 0xF22C, setg
    w.writeDword(0x9C, static_cast<std::uint32_t>(value));                         // RE 0xF233
}

void setSpecificSheetOrigin_13E30(void* order, int value) {
    const FieldWriter w{static_cast<unsigned char*>(order)};
    w.writeByte(0x124, 1);                                       // RE 0x13F02
    w.writeDword(0x128, static_cast<std::uint32_t>(value));      // RE 0x13F09
}

void setSpecificSheetObjective_13FE0(void* order, int value) {
    const FieldWriter w{static_cast<unsigned char*>(order)};
    w.writeByte(0x12C, 1);                                       // RE 0x140B2
    w.writeDword(0x130, static_cast<std::uint32_t>(value));      // RE 0x140B9
}

void setMarkMode_188D0(void* order, int flag, double first, double second) {
    const FieldWriter w{static_cast<unsigned char*>(order)};
    w.writeDouble(0xE8, first);                                  // RE 0x189FA, from xmm2
    w.writeByte(0xE0, (flag != 0) ? 1 : 0);                      // RE 0x18A09, setne
    w.writeDouble(0xF0, second);                                 // RE 0x18A10, from xmm3
}

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
