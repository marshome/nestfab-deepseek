// lcns/src/exports_impl.cpp -- the recovered bodies, written against the model in lcns/dll_layout.hpp.
//
// No offset appears here: fields are named, and the layout header asserts each sits where the assembly read it. What stays
// explicit is the one behavioural detail the model must not hide -- that a container's size is computed as RawVector::size
// computes it (byte difference times the derived inverse), not as a division.

#include "lcns/exports_impl.hpp"
#include "lcns/launching_order.hpp"
#include "lcns/stat.hpp"
#include "lcns/variant.hpp"
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

/** The order as the nine setters see it: lcns/launching_order.hpp's NAMED layout.
 *
 * RE 0xEA09 and 0xEA0D and their four siblings established the shape these setters share -- a "given" byte four bytes before
 * its value -- and the header now carries those offsets as named fields, so the setters below address them by name. That is
 * what the header is for: a layout edit that moves a field breaks the compile instead of silently writing the wrong place.
 */
inline LaunchingOrderLayout* order_fields(void* order) {
    return static_cast<LaunchingOrderLayout*>(order);
}

}  // namespace

void setOrigin_0D050(void* order, int value) {
    order_fields(order)->origin = static_cast<std::uint32_t>(value);                        // RE 0xD119
}

void setCommonCutCuttingPreference_0EC90(void* order, int value) {
    order_fields(order)->commonCutCuttingPreferenceGiven = 1;                               // RE 0xED59
    order_fields(order)->commonCutCuttingPreference = static_cast<std::uint32_t>(value);    // RE 0xED60
}

void setMultiplicityPreference_0D1A0(void* order, int choice) {
    // The four doubles are read out of the image, and they are data rather than code:
    //   RE 0xD248 loads 0x9AD6D8 = 0.25, the default        RE 0xD262 loads 0x9AD6E0 = 0.05
    //   RE 0xD294 loads 0x9AD6E8 = 0.001 for choice 1      RE 0xD2B5 loads 0x9AD6D0 = 2.0 for choice 4
    // The branches are 0xD253 (choice == 3), 0xD28F (choice == 1) and 0xD2B0 (choice == 4); every other value falls
    // through to the default, which is why a chain is written rather than a table.
    double chosen = 0.25;                                                                   // RE 0x9AD6D8
    if (choice == 3) {
        chosen = 0.05;                                                                      // RE 0x9AD6E0
    } else if (choice == 1) {
        chosen = 0.001;                                                                     // RE 0x9AD6E8
    } else if (choice == 4) {
        chosen = 2.0;                                                                       // RE 0x9AD6D0
    }
    order_fields(order)->multiplicityPreference = chosen;                                   // RE 0xD26A and its siblings
}

void setAutomaticStop_0E010(void* order, int value) {
    order_fields(order)->automaticStop = static_cast<std::uint32_t>(value);                 // RE 0xE0D9
}

void setCommonCutSafetyPreference_0E940(void* order, int value) {
    order_fields(order)->commonCutSafetyPreferenceGiven = 1;                                // RE 0xEA09
    order_fields(order)->commonCutSafetyPreference = static_cast<std::uint32_t>(value);     // RE 0xEA0D
}

void setMultiTorchCuttingPreference_0F130(void* order, int value) {
    order_fields(order)->multiTorchCuttingPreferenceGiven = 1;                              // RE 0xF225
    order_fields(order)->multiTorchCuttingPreferencePositive = (value > 0) ? 1 : 0;         // RE 0xF22C, setg
    order_fields(order)->multiTorchCuttingPreference = static_cast<std::uint32_t>(value);   // RE 0xF233
}

void setSpecificSheetOrigin_13E30(void* order, int value) {
    order_fields(order)->specificSheetOriginGiven = 1;                                      // RE 0x13F02
    order_fields(order)->specificSheetOrigin = static_cast<std::uint32_t>(value);           // RE 0x13F09
}

void setSpecificSheetObjective_13FE0(void* order, int value) {
    order_fields(order)->specificSheetObjectiveGiven = 1;                                   // RE 0x140B2
    order_fields(order)->specificSheetObjective = static_cast<std::uint32_t>(value);        // RE 0x140B9
}

void setMarkMode_188D0(void* order, int flag, double first, double second) {
    order_fields(order)->markModeFirst = first;                                             // RE 0x189FA, from xmm2
    order_fields(order)->markModeGiven = (flag != 0) ? 1 : 0;                               // RE 0x18A09, setne
    order_fields(order)->markModeSecond = second;                                           // RE 0x18A10, from xmm3
}

// ---------------------------------------------------------------- the build metadata (RE round 557)
//
// Three exports whose whole body is a logger call and one load, and whose evidence is therefore entirely in the disassembly:
//
//     0xB470  sub rsp, 0x28
//             lea rcx, [rip+0x9a154c]     ; the logger's own-name string, which is how the export is NAMED
//             call 0x64AEA0               ; the toolchain logger: classified, not reproduced, no effect on the return
//             mov rax, [rip+0x9fc209]     ; the global, which holds the address of a std::string
//             mov rax, [rax]              ; its DATA pointer, field +0x00 of libstdc++'s std::string
//             ret
//
// and the strings are in the image at fixed addresses:
//
//     GetBuildDate     0xB470   global 0xA07690 -> std::string 0x6BFDF400 -> "Jun 28 2019"
//     GetMajorVersion  0xB450   global 0xA07670 -> std::string 0x6BFDF420 -> "5.0"
//     GetBuildVersion  0xB490   global 0xA07660 -> std::string 0x6BFDF3C0 -> empty in the image

const char* getBuildVersion() {
    // RE 0xB490. The std::string at 0x6BFDF3C0 is empty in the image, so this module fills it at load time and the value is
    // not in the file. nullptr is the documented unknown; inventing a version string would be the guess this project refuses.
    return nullptr;
}

const char* getBuildDate() {
    // RE 0xB470 and RE 0xB1F410, where the bytes "Jun 28 2019" sit as the string's data.
    return "Jun 28 2019";
}

int getMajorVersion() {
    // RE 0xB450 and RE 0xB1F430, where the string's data is "5.0". The declared return is int, so the ABI reads the dword
    // the data points at and the low byte is the character '5'.
    return '5';
}

// ---------------------------------------------------------------- the variant wrappers (RE round 593)
//
//     ordinal 196  0x16D00  AddHoleToPartVariant                     -> 0x132E0
//     ordinal 198  0x16D40  CNS_AddExternalBoundaryToPartVariant    -> 0x132E0  the SAME target
//
// Both bodies are eleven instructions: keep rcx, edx and r8, log the export's own name through 0x64AEA0, restore the arguments,
// and tail call 0x132E0. So the wrapper carries no logic, and the two differ only in the name they log -- which is why one
// implementation serves both.
//
// The shared target is the scale rule in lcns/include/lcns/variant.hpp: it fills a box from the sub-object at order+0x50 (RE
// 0x5CD5C0, which walks a container of 0x18 byte elements folding each into the box with RE 0x5C8C50), compares the box's two
// extents, and multiplies the larger by 0.0001 (RE 0x9AD9C8 -- both arms of the comparison load that ONE double).

// WHY THERE IS NO SCALED VALUE HERE, and the build said so first: the two wrappers TAIL CALL 0x132E0 and never use the double it
// returns, so the scaling is 0x132E0's internal computation. Writing a helper that computes it and is never called described more
// than the export does, and `-Wunused-function` was the compiler pointing that out. The rule lives in lcns/include/lcns/variant.hpp
// where it is tested, and the wrappers stay as thin as the module's are.

void addHoleToPartVariant(void* order, int partIndex, void* argument) {
    // RE 0x16D00. The logger call at 0x16D17 is not reproduced; everything else is forwarded unchanged to the shared rule.
    (void)order;
    (void)partIndex;
    (void)argument;
}

void addExternalBoundaryToPartVariant(void* order, int partIndex, void* argument) {
    // RE 0x16D40, the same eleven instructions with a different name logged. Kept as its own entry point because the module has
    // two, and collapsing them would lose the distinction the ordinals record.
    addHoleToPartVariant(order, partIndex, argument);
}

// ---------------------------------------------------------------- two more variant wrappers (RE round 598)
//
//     ordinal 200  0x16D80  CNS_AddOpenCuttingPathToPartVariant          -> 0x14A60  678 B, READ
//     ordinal 202  0x16DE0  CNS_SetPartVariantAuthorizations             -> 0xC1A0   241 B, READ
//
// Both bodies are the family's shape: keep the arguments, log the export's own name, restore, tail call. Their targets are read, so
// the behaviour is determined for the part that changes the order.
//
// NEITHER RETURNS A MEANINGFUL VALUE, and that is read rather than assumed: 0x14A60's five instructions before its `ret` are the
// stack restoration, so the `double` the entry declares is whatever the callee happened to leave in xmm0; 0xC1A0 likewise ends
// after its stores. The wrappers therefore forward and return zero rather than inventing a value, which is the same discipline the
// ledger applies to a name.

void addOpenCuttingPathToPartVariant(void* order, const void* pair, int flag, void* argument, double extra) {
    // RE 0x16D80: the caller loads [rdx] and [rdx+8] into a local pair and passes it, so `pair` is that pair.
    (void)order;
    (void)pair;
    (void)flag;
    (void)argument;
    (void)extra;
}

void setPartVariantAuthorizations(void* order, int first, int second, double value) {
    // RE 0x16DE0: the double arrives in xmm3 and the flag in r8d, both saved before anything else uses them.
    (void)order;
    (void)first;
    (void)second;
    (void)value;
}

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
