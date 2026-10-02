// lcns/boxacc.hpp -- the bounding-box accumulator pair the DLL uses, recovered from 0x5C8A10 and 0x50FD40.
//
//   0x5C8A10 (114 B, 16 callers) -- extend-or-initialise a box with one pair of numbers.
//   0x50FD40 (270 B, 3 callers)  -- walk a range of 312-byte elements, take a pair of doubles from each through the
//                                   element's own sub-object, fold every pair into the box, then fold the box's own
//                                   size in as one more pair and return the box.
//
// BOX LAYOUT (read from 0x5C8A10's own offsets, and written by 0x50FD40 before the loop):
//     +0x00  one byte, the FLAG. Non-zero means UNINITIALISED: the first call stores the pair into all four slots and
//            clears it. 0x50FD40 sets the byte to 1, zeroes the four doubles, and then immediately seeds the box with the
//            pair (0, 0) -- so the flag is already cleared before the loop starts, and the "nothing was seen" guard at
//            0x50FDDC cannot be reached through this entry. An empty range yields an all-zero box, not an uninitialised
//            one; the guard is kept in the implementation because the original has it.
//     +0x08  minX
//     +0x10  minY
//     +0x18  maxX
//     +0x20  maxY
//
// ELEMENT LAYOUT (0x50FD40's stride and accessors): the element is 0x138 bytes; +0x60 holds a pointer to a sub-object;
// the pair is that sub-object's +0x28 and +0x30 doubles. The two accessors are embedded blocks 0x4F8370 and 0x4F8380 and
// the getter is 0x51D2F0, so the differential test can build elements the original also accepts.

#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

/** The strided element the accumulator walks. RE: 0x50FDA8 `add rbx, 0x138`. */
inline constexpr std::size_t kBoxElementStride = 0x138;
/** Where the element keeps its sub-object pointer. RE: 0x51D2F0 `mov rax, [rcx+0x60]`. */
inline constexpr std::size_t kBoxElementSubObject = 0x60;
/** The two doubles the accessors read out of that sub-object. RE: 0x4F8370 / 0x4F8380. */
inline constexpr std::size_t kBoxValueA = 0x28;
inline constexpr std::size_t kBoxValueB = 0x30;

/** Field offsets of the box itself. */
inline constexpr std::size_t kBoxFlag = 0x00;
inline constexpr std::size_t kBoxMinX = 0x08;
inline constexpr std::size_t kBoxMinY = 0x10;
inline constexpr std::size_t kBoxMaxX = 0x18;
inline constexpr std::size_t kBoxMaxY = 0x20;
/** Bytes a box occupies. */
inline constexpr std::size_t kBoxBytes = 0x28;

/**
 * Extend a box with one pair, or initialise it. RE 0x5C8A10.
 * @param box - the box, flag at +0x00 and the four doubles after it.
 * @param pair - two doubles.
 */
void boxAccumulate(unsigned char* box, const double* pair);

/**
 * The bounding box of a range's element pairs, with the box's own (width, height) folded in. RE 0x50FD40.
 *
 * The range argument is the original's: a pointer to two pointers, begin at +0x00 and end at +0x08, elements
 * kBoxElementStride apart. The box must already be zeroed by the caller if a fresh result is wanted; the routine itself
 * sets the flag to 1 and zeroes the four doubles before walking, as the original does.
 *
 * @param box - the box to write.
 * @param range - pointer to the begin/end pair.
 * @returns the box pointer, as the original returns it in rax.
 */
void* boxAccumulateRange(unsigned char* box, const void* range);

}  // namespace lcns
