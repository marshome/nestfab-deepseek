// lcns/exports_impl.hpp -- implementations behind the exported entry points, recovered from the assembly.
//
// One function per recovered export. Each declares the rva it comes from and what the recovery rests on, because a
// signature and a body are not evidence: the evidence is the test that holds it to the original, and the note says which
// kind of test that is.
//
// The handles are the original's own opaque objects. These functions read the ORIGINAL's field offsets, so they are the
// behaviour of the module's objects, not of this project's models -- which is exactly what an entry point has to be.

#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {
namespace dll {
namespace exports {
namespace impl {

/**
 * RE 0xB0C0 (ordinals 25/26), 52 bytes.
 * count = ([order+0x58] - [order+0x50]) >> 3, multiplied by 0x6F96F96F96F96F97 -- the modular inverse of 39, i.e. the
 * container's element count with a stride of 312 bytes (39 * 8). Exact for any container whose byte length is a multiple
 * of 312, which is what a container of 312-byte elements always is; reproduced literally so a malformed one behaves the
 * same here as in the original. The original also logs "GetNumberOfNestings" before reading; this implementation does
 * not log, and that difference is recorded in re/EXPORT_IMPLS.md.
 * Established by: behavioural test (the original reads a RIP-relative label string and calls the logger, so it cannot be
 * executed from the embedded copy).
 */
std::size_t getNumberOfNestings(void* order);

/**
 * RE 0xB190 (ordinals 23/24), 63 bytes.
 * sub = [order+0x08]; the container is at sub+0x28 (0x51D0C0 is `lea rax, [rcx+0x28]`), so
 * count = ([sub+0x30] - [sub+0x28]) >> 3, multiplied by 0xEEEEEEEEEEEEEEEF -- the modular inverse of 15, a stride of
 * 120 bytes.
 * Established by: behavioural test.
 */
std::size_t getNumberOfNestedParts(void* order);

/**
 * RE 0xB100 (ordinals 17/18), 34 bytes: a tail call to 0x51D090, which is `mov eax, [rcx+0x20]; ret`.
 * So it returns the 32-bit field at +0x20 of the sub-object at [part+0x08].
 * Established by: behavioural test.
 */
std::uint32_t getMultiplicity(void* part);

/**
 * RE 0xC5E0 (ordinals 27/28), 36 bytes: returns the pointer stored at +0x1B8. The original logs before returning; that
 * side effect is not reproduced and is recorded in re/EXPORT_IMPLS.md.
 * Established by: behavioural test.
 */
const char* getUserStringAt1B8(void* part);   // RE 0x16CF0 (210/211): pointer at +0x1B8, no logging
void setByteAtF8(void* object, int value);    // RE 0x0AFF0 (288/289): byte +0xF8 = (value != 0)
void setDoubleAndFlag(void* object, int flag, double value);   // RE 0x0B000 (286/287): double +0x100, byte +0xF9
void* getSolutionIdentity(void* handle);      // RE 0x0B0A0 (33/34): returns its argument, touches no memory

/** The int-setter family (RE 0x0DDC0, 0x0D310, 0x0D340, 0x0DE20, 0x0D430): `mov dword ptr [rsi+OFF], ebx`.
 *  Each stores the second argument, unchanged, as a 32-bit value at its own offset; the harness in which that
 *  store sits is identical for all five (push rsi/rbx, the argument pair, a logger call, the store, ret).
 *  Established by: behavioural test. */
void setIntField(void* object, int value, std::size_t offset);
void setShearMode(void* object, int value);   // RE SetShearMode: offset 0x44
void setNoMixPreference(void* object, int value);   // RE CNS_SetNoMixPreference: offset 0x18
void setNoSheetMixPreference(void* object, int value);   // RE CNS_SetNoSheetMixPreference: offset 0x1C
void setShearRepulseFromBorders(void* object, int value);   // RE SetShearRepulseFromBorders: offset 0x58
void unlockLaunchingOrder(void* object, int value);   // RE UnLockLaunchingOrder: offset 0x244

const char* getPartUserString(void* part);

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
