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

/** RE 0x16D00 (ordinals 196/197, AddHoleToPartVariant).
 *
 * The body is eleven instructions: keep rcx, edx and r8, log its own name through 0x64AEA0, restore them and tail call 0x132E0.
 * So the wrapper carries no logic and the work is the shared variant scale rule -- RE 0x132E0 measures the sub-object at
 * order+0x50, compares its two extents, and multiplies the larger by 0.0001 (RE 0x9AD9C8). The logger call is not reproduced,
 * which the project classifies rather than reimplements.
 *
 * The arguments are the export's own: the order, a part index, and a pointer. They are forwarded unchanged, which is what the
 * body does with them.
 */
void addHoleToPartVariant(void* order, int partIndex, void* argument);
/** RE 0x16D40 (ordinals 198/199, CNS_AddExternalBoundaryToPartVariant): the SAME eleven instructions and the SAME tail target as
 *  AddHoleToPartVariant, so the two differ only in the name they log. That is why one implementation serves both. */
void addExternalBoundaryToPartVariant(void* order, int partIndex, void* argument);

/** RE 0x16D80 (ordinals 200/201, CNS_AddOpenCuttingPathToPartVariant): 96 bytes. It reads [rdx] and [rdx+8] into a local pair,
 *  logs its name, and calls 0x14A60 with that pair and two more arguments. */
void addOpenCuttingPathToPartVariant(void* object, const void* pair, int flag, void* argument, double extra);

/** RE 0xC1A0 (ordinals 202/203, CNS_SetPartVariantAuthorizations): 241 bytes, a 24-byte move assignment into order+0x188 that
 *  keeps the old first word and tests it for null. The signature is (order, int, int, double): the flag is in r8d and the double in
 *  xmm3, both saved before anything else touches them. */
void setPartVariantAuthorizations(void* order, int first, int second, double value);

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

/** RE 0x0D400 (ordinal 84), 36 bytes, and the body is ONE store: `mov dword [rsi + 0x1fc], ebx` at 0x0D417. **The export's own name is the oracle for the
 *  field** -- the module calls it `SetLocalMaximumIterations` and it writes exactly one offset, which is `Order`'s `maxIterations`. **It was called `setInt_1FC`
 *  here, a name built from its position**, and `kForwarding` named it at ordinal 84; the module's name replaces it. **No clamp**: 0xD3C7's `test ebx, ebx` and
 *  0xD3D2's `cmova` are in the function next door. */
void setLocalMaximumIterations(void* object, int value);

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
/** RE 0xF130, 388 bytes. **THE POSITIVE FLAG COMES FROM A THIRD PARAMETER, NOT FROM THE VALUE.** 0xF140 is `mov ebp, r8d` and 0xF22C is
 *  `setg byte [rsi + 0xa0]` -- so `flag > 0` is stored and `value > 0` is not. 0xF225 writes the "given" byte unconditionally and 0xF233 stores
 *  `edx` (argument 2) at +0x9C. **`ebp` is never stored**, so the third argument is read, tested and discarded. */
void setMultiTorchCuttingPreference_0F130(void* order, int value, int flag);
/** RE 0x13F02 and 0x13F09 (298, SetSpecificSheetOrigin): +0x124 = 1, then the argument at +0x128. */
void setSpecificSheetOrigin_13E30(void* order, int value);
/** RE 0x140B2 and 0x140B9 (300, SetSpecificSheetObjective): +0x12C = 1, then the argument at +0x130. */
void setSpecificSheetObjective_13FE0(void* order, int value);
/** RE 0x189FA, 0x18A09 and 0x18A10 (246, SetMarkMode): xmm2 to +0xE8, +0xE0 = (flag != 0), xmm3 to +0xF0. */
void setMarkMode_188D0(void* order, int flag, double first, double second);

/** RE 0xB490 (88, GetBuildVersion): a logger call, then the data pointer of the std::string the global at 0xA07660 holds.
 *  That string is EMPTY in the image, so its value is produced at load time and is not recoverable. */
const char* getBuildVersion();
/** RE 0xB470 (90, GetBuildDate): the same shape; the global at 0xA07690 holds a std::string whose data is "Jun 28 2019". */
const char* getBuildDate();
/** RE 0xB450 (92, GetMajorVersion): the same shape; the global at 0xA07670 holds a std::string whose data is "5.0". */
int getMajorVersion();

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
