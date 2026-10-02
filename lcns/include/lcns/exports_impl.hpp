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
