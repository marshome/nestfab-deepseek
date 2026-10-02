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

void setShearMode(void* order, int value);         // RE 0x0DDC0 -> +0x44
void setNoMixPreference(void* order, int value);   // RE 0x0D310 -> +0x18
void setNoSheetMixPreference(void* order, int value);   // RE 0x0D340 -> +0x1C
void setShearRepulseFromBorders(void* order, int value);   // RE 0x0DE20 -> +0x58
void unlockLaunchingOrder(void* order, int value); // RE 0x0D430 -> +0x244
void setInt_1FC(void* order, int value);           // RE 0x0D400 -> +0x1FC

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
