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
const char* getPartUserString(void* part);

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
