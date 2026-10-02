// lcns/include/lcns/nesting_nester_fields.hpp -- Multi::NestingNester's fields, one instruction per position.
//
// THE RULE THIS PROJECT USES, and the reason this file is short: **a field's POSITION needs an instruction, and the instruction must be a
// store through the object.** Not a shape, not a name that matches, not a plausible layout -- a store, at an offset, through a register the
// function has been shown to hold the object in.
//
// THE CONSTRUCTOR 0x342E0 IS THE BEST SOURCE, because it sets its base register once and never changes it:
//
//     0x342EC  mov rbx, rcx        ; the object
//     0x343F1  pop rbx             ; and nothing in between writes rbx
//
// so every store through rbx in that body is a store into the object, and there are EIGHT of them at SEVEN offsets.
//
// WHAT THE CLASS'S METHODS ADD, and what they do not. The other slots were scanned the same way: slot 2 at 0x33100 contributes three
// offsets, and the two destructors contribute only the vtable pointer at +0. **The main packing routine 0x378E0 -- 14374 bytes, 2841
// instructions -- contributes NOTHING**, because the only registers it stores through at eight or more distinct offsets are the STACK
// (`rsp` with 131 offsets) and registers below +0x28. **So the packer does not write this object's fields; it works through locals and
// through other objects.** That is a fact about the class and not a gap in the scan.
//
// WHAT THE ARCHIVE'S 132 OFFSETS ARE, THEREFORE. Its dossier for 0x378E0 records 132 field offsets, and this scan finds none of them in that
// function through a register plausibly holding the object -- so those offsets are into OTHER objects the packer touches, not into
// NestingNester itself. The distinction was invisible until a layout was required to name the object its offsets belong to.
#pragma once

#include <cstddef>
#include <cstdint>

#include "lcns/class_definitions.hpp"

namespace lcns {

/** RE 0x342EC: `mov rbx, rcx`, and RE 0x343F1 pops it -- so rbx is the object for the whole body. */
constexpr std::uintptr_t kNestingNesterCtorAddress = 0x342E0;
constexpr std::size_t kNestingNesterCtorBytes = 422;

/** The seven offsets the constructor stores to, each with its instruction. */
struct FieldStore {
    std::size_t offset;
    const char* width;
    std::uintptr_t address;
    const char* note;
};

inline const FieldStore* nestingNesterCtorFields(std::size_t& count) {
    static const FieldStore table[] = {
        {0x000, "qword", 0x34308, "the vtable pointer"},
        {0x018, "qword", 0x34312, "written from the same rax as the vtable"},
        {0x020, "qword", 0x3430E, "written from rdx, which is [rdi + 8] loaded at 0x34301"},
        {0x028, "dword", 0x34341, "written from eax"},
        {0x030, "qword", 0x34328, "zeroed here"},
        {0x030, "qword", 0x343E3, "and set from xmm6 at the end, so this offset holds a DOUBLE"},
        {0x038, "dword", 0x34335, "set to 1"},
        {0x9F8, "qword", 0x3436D, "set to 0x270, which is 624"},
    };
    count = sizeof(table) / sizeof(table[0]);
    return table;
}

/** RE 0x24FDA in the other class's constructor: the object is 0x30 bytes, so its fields live below that. */
// kNestingNesterVtableField lives in lcns/vtable_layout.hpp, which measured it from the same instruction; it is not repeated here.

/** The offsets the class's SLOT 2 at 0x33100 adds, and the instruction that shows each. RE 0x3311F `mov rbp, rcx` makes rbp the object
 *  until 0x3392B reassigns it from a return value -- which is why the scan does not count rbp's stores after that point. */
inline const FieldStore* nestingNesterSlot2Fields(std::size_t& count) {
    static const FieldStore table[] = {
        {0x000, "qword", 0x335F3, "the vtable pointer"},
        {0x010, "qword", 0x3360F, "written from rcx"},
        {0x018, "qword", 0x337F1, "written from r10"},
    };
    count = sizeof(table) / sizeof(table[0]);
    return table;
}

static_assert(kNestingNesterCtorBytes == 422, "the profile's size for 0x342E0");
static_assert(kNestingNesterVtableField == 0x00, "RE 0x34308: mov [rbx], rax");

}  // namespace lcns
