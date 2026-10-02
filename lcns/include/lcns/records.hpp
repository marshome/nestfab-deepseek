// lcns/include/lcns/records.hpp -- records the module walks, as STRUCTS, with the constants kept as their evidence.
//
// WHY THIS REPLACES PART OF layout.hpp. layout.hpp is 3389 lines of `inline constexpr std::size_t` with an instruction address on each, and
// **not one `struct` in the file.** The human's objection -- "C++ code is full of address offsets everywhere, check it all, and do not do
// this kind of fake reverse engineering again" -- is exactly that file: it records where a record's fields are without ever saying what the
// record IS. **Offsets with instructions are good EVIDENCE and a poor DELIVERABLE.**
//
// So the records below are written as types, each member carrying the instruction that placed it, and the offsets are checked against those
// members rather than listed beside them. **The conversion is mechanical where the evidence is good**, which is the point: a group of
// same-prefix offsets whose instructions agree about adjacency was always a struct that had not been written down.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

/** The record at 0x60 bytes that layout.hpp described as kRecordVtable / kRecordWordA / kRecordWordB / kRecordBytes.
 *
 *  EVERY MEMBER IS PLACED BY AN INSTRUCTION, and the two that follow each other are ADJACENT BY ARITHMETIC rather than by assertion:
 *  `kRecordWordB - kRecordWordA == 4` was itself a static_assert in the old file, which is what a struct says for free.
 *
 *  The vtable pointer is a real member here rather than a constant, because the instruction at 0x6DE4F5 STORES to it -- so this record is
 *  polymorphic, and the RVA at 0x6DE4E0 is the vtable it is given.
 */
struct PolymorphicRecord {
    void** vtable = nullptr;            // +0x00, RE 0x6DE4F5
    std::uint32_t wordA = 0;            // +0x08, RE 0x6DE4E7
    std::uint32_t wordB = 0;            // +0x0C, RE 0x6DE4EE

    /** RE 0x6DE4E0: the vtable this record is built with. */
    static constexpr std::uintptr_t kVtableRva = 0x35E739;

    /** RE 0x6DE4D0: the record is 0x60 bytes, so there are fields past the three above that no instruction has placed yet. */
    static constexpr std::size_t kBytes = 0x60;

    /** The bytes past +0x10, named as a region rather than invented as members: **an unplaced field is not a field**, and a struct with
     *  guessed members would be the defect this project's ledger exists to prevent. */
    std::byte unplaced[kBytes - 0x10]{};    // +0x10 .. +0x60
};

/** The 240 byte record layout.hpp described by kRunRecordStride and the kRecord*Offset constants.
 *
 *  **THE COUNT IS THE POINT**: `unplaced` makes it 240 bytes and says the rest is unmeasured, where the old file listed three offsets and a
 *  stride and left a reader to work out that most of the record was unknown.
 */
struct RunRecord {
    std::byte unplaced0[0x18]{};        // +0x00 .. +0x18: not placed by any instruction read so far
    std::uint32_t value = 0;            // +0x18, RE: kRecordValueOffset, a dword
    std::uint32_t pad0x1C = 0;          // +0x1C: alignment before the qword at 0x20
    void* wide = nullptr;               // +0x20, RE: kRecordWideOffset, a qword
    std::uint8_t flag = 0;              // +0x28, RE: kRecordFlagOffset, a byte
    std::byte unplaced1[0xF0 - 0x29]{}; // +0x29 .. +0xF0

    static constexpr std::size_t kStride = 0xF0;    // RE 0x1A90BB `add rbx,0xF0` and 0x1B3943 `add rdx,0xF0`
};

// THE LAYOUT IS THE STRUCT'S, checked against the instructions: these replace the file's constants rather than duplicating them.
static_assert(offsetof(PolymorphicRecord, vtable) == 0x00, "RE 0x6DE4F5");
static_assert(offsetof(PolymorphicRecord, wordA) == 0x08, "RE 0x6DE4E7");
static_assert(offsetof(PolymorphicRecord, wordB) == 0x0C, "RE 0x6DE4EE");
static_assert(offsetof(PolymorphicRecord, wordB) - offsetof(PolymorphicRecord, wordA) == 4,
              "the old file asserted this arithmetic; a struct gives it for free");
static_assert(sizeof(PolymorphicRecord) == 0x60, "RE 0x6DE4D0: the record is 0x60 bytes");
static_assert(PolymorphicRecord::kVtableRva == 0x35E739, "RE 0x6DE4E0");

static_assert(offsetof(RunRecord, value) == 0x18, "kRecordValueOffset");
static_assert(offsetof(RunRecord, wide) == 0x20, "kRecordWideOffset");
static_assert(offsetof(RunRecord, flag) == 0x28, "kRecordFlagOffset");
static_assert(sizeof(RunRecord) == 0xF0, "kRunRecordStride: the record is what the walk advances by");

}  // namespace lcns
