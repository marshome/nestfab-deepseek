// lcns/exports_impl.hpp -- implementations behind the exported entry points, recovered from the assembly.
//
// Objects are modelled in lcns/dll_layout.hpp where each offset carries the rva that establishes it. A handle stays
// opaque (void*) at the entry level, which is what it is; the bodies cast to the modelled type.

#pragma once

#include "lcns/dll_layout.hpp"

#include <cstddef>
#include <cstdint>

namespace lcns {
namespace dll {
namespace exports {
namespace impl {

std::size_t getNumberOfNestings(void* order);      // RE 0xB0C0 (25/26): the nesting container's size
std::size_t getNumberOfNestedParts(void* order);   // RE 0xB190 (23/24): the nested-part container's size
std::uint32_t getMultiplicity(void* part);         // RE 0xB100 (17/18): the sub-object's 32-bit multiplicity
const char* getPartUserString(void* part);         // RE 0xC5E0 (27/28): the user string; the logger call is not reproduced
const char* getUserStringAt1B8(void* part);        // RE 0x16CF0 (210/211): the same field, no label in the module
void setByteAtF8(void* object, int value);         // RE 0x0AFF0 (288/289): flag = (value != 0)
void setDoubleAndFlag(void* object, int flag, double value);   // RE 0x0B000 (286/287)
void* getSolutionIdentity(void* handle);           // RE 0x0B0A0 (33/34): returns its argument, no memory touched
/** RE 0xB510 (ordinals 29/30): returns object[+0xA0] when object[+0x4C] is 1, else null. */
void* getPartWithBadGeometry(void* object);

/** RE 0xDD90 (ordinal 144): byte at +0x40 becomes the truth value of the argument. */
void setFillLastNestingStrategy(void* object, int value);
/** RE 0xDE50 (ordinal 166): byte at +0x1C. */
void setPartCommonCutMode(void* object, int value);
/** RE 0xDD30 (ordinal 182): byte at +0x20. */
void setFloatingMode(void* object, int value);
/** RE 0xDD60 (ordinal 312): byte at +0x21. */
void setOriginPackingMode(void* object, int value);
/** RE 0xDDF0 (ordinal 330): the 32-bit value goes to BOTH +0x48 and +0x44. */
void setPartialShearMode(void* object, int value);

/** RE 0x10440 (ordinal 316): byte at +0x41 becomes the truth value of the argument. */
void setEvaluateIntermediateNestingsAsLast(void* object, int value);
/** RE 0x10470 (ordinal 336): byte at +0x22. */
void setReorganizeBiggestPartNearOrigin(void* object, int value);
/** RE 0x104A0 (ordinal 338): byte at +0x23. */
void setReorganizeLongestPartNearOrigin(void* object, int value);
/** RE 0xC610 (ordinal 334): sets +0x20A to 1 and +0x20B to 0. No argument beyond the object. */
void forcePartInsideHole(void* part);
/** RE 0xCEC0 (ordinal 78): the 32-bit argument goes to +0x08. */
void setObjective(void* options, int value);
/** RE 0xCEF0 (ordinal 212): the double argument goes to +0x50. */
void setShearGap(void* options, double gap);
/** RE 0x89D0 (ordinal 238): counts the 48-byte elements of the container at +0 and +8. */
std::size_t noFitGetNumberOfExternalPolygons(const void* owner);

/** RE 0xD370 (ordinal 73): +0x200 and +0x201 become the complements of bit zero and bit one. */
void setLocalEngine(void* object, int value);
/** RE 0x8AB0E0: the platform concurrency count, through the import stub 0x63F6B0, negatives clamped to zero. */
unsigned platformConcurrency();
/** RE 0xB5B70 with RE 0xB5B79, and RE 0xD3B0: floor at one, then the requested value or the minimum of the two. */
unsigned clampMaximumThreads(unsigned platformValue, int requested);
/** RE 0xD3B0 (ordinal 82): stores clampMaximumThreads(platformConcurrency(), value) at +0x1F8. */
void setLocalMaximumThreads(void* object, int value);

/** RE 0xAFE0 through 0x1B270: normalises the argument to zero or one. */
void setModuleSwitch(int value);
/** RE 0x60A610: reads back the byte the switch writes, so the behaviour can be checked. */
unsigned char moduleSwitch();

/** RE 0x16CB0 (ordinal 208): assigns the C string to the std::string at +0x1B8. */
void setUserStringAt1B8(void* object, const char* text);

void setShearMode(void* order, int value);         // RE 0x0DDC0 -> +0x44
void setNoMixPreference(void* order, int value);   // RE 0x0D310 -> +0x18
void setNoSheetMixPreference(void* order, int value);   // RE 0x0D340 -> +0x1C
void setShearRepulseFromBorders(void* order, int value);   // RE 0x0DE20 -> +0x58
void unlockLaunchingOrder(void* order, int value); // RE 0x0D430 -> +0x244
void setInt_1FC(void* order, int value);           // RE 0x0D400 -> +0x1FC


// ---------------------------------------------------------------- the nine setters re/g_ready.py found ready (round 537)
//
// Every one writes a field of the order and nothing else observable: the logger call they make first is toolchain and
// affects no state, and the mutex guard they take is not reproduced. Each carries the store address that establishes it.

/** RE 0xD119 (ordinal 86, SetOrigin): the 32-bit argument goes to +0x0C. */
void setOrigin_0D050(void* order, int value);
/** RE 0xED59 and 0xED60 (154, SetCommonCutCuttingPreference): +0x88 = 1, then the argument at +0x8C. */
void setCommonCutCuttingPreference_0EC90(void* order, int value);
/** RE 0xD255 and its three siblings (128, CNS_SetMultiplicityPreference): one of four doubles at +0x10, chosen by the
 *  argument (1, 3 or 4 select 0x9A0476, 0x9A044C, 0x9A0413; anything else takes 0x9A0488). */
void setMultiplicityPreference_0D1A0(void* order, int choice);
/** RE 0xE0D9 and 0xE12F (140, SetAutomaticStop): the argument goes to +0x240, the mode 0x22A20 reads. */
void setAutomaticStop_0E010(void* order, int value);
/** RE 0xEA09 and 0xEA0D (150, SetCommonCutSafetyPreference): +0x68 = 1, then the argument at +0x6C. */
void setCommonCutSafetyPreference_0E940(void* order, int value);
/** RE 0xF225, 0xF22C and 0xF233 (176, SetMultiTorchCuttingPreference): +0x98 = 1, +0xA0 = (value > 0), value at +0x9C. */
void setMultiTorchCuttingPreference_0F130(void* order, int value);
/** RE 0x13F02 and 0x13F09 (298, SetSpecificSheetOrigin): +0x124 = 1, then the argument at +0x128. */
void setSpecificSheetOrigin_13E30(void* order, int value);
/** RE 0x140B2 and 0x140B9 (300, SetSpecificSheetObjective): +0x12C = 1, then the argument at +0x130. */
void setSpecificSheetObjective_13FE0(void* order, int value);
/** RE 0x189FA, 0x18A09 and 0x18A10 (246, SetMarkMode): xmm2 to +0xE8, +0xE0 = (flag != 0), xmm3 to +0xF0. */
void setMarkMode_188D0(void* order, int flag, double first, double second);

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
