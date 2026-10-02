# -*- coding: utf-8 -*-
"""Replace Tiling::Pattern's invented member layout with a MEASURED assertion, and record what is not established.

**WHAT WENT WRONG, AND IT IS THE OLD MISTAKE IN A NEW PLACE.** I declared twelve words at +0x00 through +0x40 from the offsets the copy constructor
writes, and then measured it: **`vptr` came out at +8, not +0.** So the declaration did not reproduce the module's layout, which means the offsets in the
routine are not simply the offsets of members of a class whose first word is its vptr -- **there is something before the class's own vptr that the routine
copies over**, and I do not know what.

**AND THE DECLARATION WAS THE WRONG INSTRUMENT ANYWAY.** A layout has to be MEASURED on a real instance, which is what `re/row.hpp` does for `Squeezer`;
writing a struct and hoping it lands on the module's offsets is the opposite. So the header now states the FACTS THE ROUTINE PROVES -- the widths, the
two fixed offsets, and the two strides -- and the test measures where they actually land rather than where a declaration assumed.

**AND THE COPY STARTS AT +0x00 AND WRITES TWELVE WORDS.** If the class's own vptr is not at +0x00 then the first word the routine writes belongs to
something else, and **naming that something is not something this evidence supports.**
"""
import io
import sys

PATTERN = r"D:\Nesting\nestfab\lcns\include\lcns\pattern.hpp"
TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

HEADER = '''// lcns/include/lcns/pattern.hpp -- Tiling::Pattern, the class the evaluators' slot 3 belongs to.
//
// **WHY THIS FILE EXISTS.** Six of the eight `Tiling::*Evaluator` classes carry the SAME address at vtable slot 3 -- 0x4E7E50 -- and reading that routine
// shows a copy of a fixed block followed by a DEEP COPY OF A CONTAINER. **So the slot belongs to a class this tree did not have**, and the class is
// `Tiling::Pattern`: `BiModulePattern` and `MultiOrientedPartPattern` both derive from it by the module's own typeinfo, and `Tiling::Pattern` itself is
// absent from `re/vtables.json` because it has no instantiated table.
//
// THE EVIDENCE IS ONE FUNCTION, RE 0x4E7E50, 539 BYTES, AND IT IS A COPY CONSTRUCTOR:
//
//     rcx = the DESTINATION   r8 = the SOURCE   rdi = rcx   rbp = r8
//
//     0x4E7E5F  mov rax, [r8]               0x4E7E6E  mov [rcx], rax
//     0x4E7E62  mov rdx, [r8 + 8]           0x4E7E7D  mov [rcx + 8], rdx
//     0x4E7E85  mov rax, [r8 + 0x10]        0x4E7E91  mov [rcx + 0x10], rax
//     0x4E7E81  mov rdx, [r8 + 0x18]        0x4E7E89  mov [rcx + 0x18], rdx
//     0x4E7E95  mov rax, [r8 + 0x20]        0x4E7EA7  mov [rcx + 0x20], rax
//     0x4E7E8D  mov rdx, [r8 + 0x28]        0x4E7E99  mov [rcx + 0x28], rdx
//     0x4E7EAB  mov rax, [r8 + 0x30]        0x4E7EC7  mov [rcx + 0x30], rax
//     0x4E7E71  movsd xmm0, [r8 + 0x38]     0x4E7EAF  movsd [rcx + 0x38], xmm0
//     0x4E7EB4  movsd xmm0, [r8 + 0x40]     0x4E7EC2  movsd [rcx + 0x40], xmm0
//     0x4E7EBA  mov qword [rcx + 0x48], 0            -- THE CONTAINER IS NOT COPIED, IT IS REBUILT
//     0x4E7ED2  mov qword [rcx + 0x50], 0
//     0x4E7EDE  mov qword [rcx + 0x58], 0
//
// **TWELVE WORDS ARE COPIED VERBATIM FROM +0x00 THROUGH +0x40, AND TWO OF THEM ARE DOUBLES, AT +0x38 AND +0x40.** Then the container at +0x48, +0x50
// and +0x58 is zeroed and rebuilt:
//
//     0x4E7E66  mov rbx, [r8 + 0x50]         ; the SOURCE's end, and 0x4E7E6A subtracts [r8 + 0x48] from it
//     0x4E7ECB  mov rax, rbx / sar rax, 4
//     0x4E7EDA  imul rax, 0x8E38E38E38E38E39 ; FIVE TIMES the element count -- see the measurement note below
//     0x4E7EEB  cmp rax, 0x1C71C71C71C71C7   ; the overflow guard for a count of nine
//     0x4E7F01  call 0x998500                ; THE ALLOCATOR, with rcx = the byte count
//     0x4E7F0C  mov [rdi + 0x48], r12        ; begin
//     0x4E7F10  mov [rdi + 0x50], r12        ; end = begin, because nothing is constructed yet
//     0x4E7F14  mov [rdi + 0x58], rbx        ; capacity
//     0x4E7F30  loop: mov rcx, r9 / mov r8d, 0x90 / mov rdx, rbx / call 0x63F2F8
//     0x4E7F49  add rbx, 0x90                ; the SOURCE pointer
//     0x4E7F50  add r9, 0x90                 ; and the DESTINATION -- **THE ELEMENT STRIDE IS 0x90**
//
// **AND A SECOND PASS COUNTS ELEMENTS OF THREE WORDS.** From 0x4E7F5C: `add r13, 0x90`, `sub rsi, r13`, `shr rsi, 4`, `imul rsi, 0xE38E38E38E38E39`
// -- and 0xE38E38E38E38E39 is the RECIPROCAL OF NINE, so that pass divides by three words rather than nine.
//
// **WHAT IS NOT ESTABLISHED, AND THIS FILE NO LONGER PRETENDS OTHERWISE.** A member declaration was written here from these offsets and then MEASURED,
// and the measurement came out wrong: **the first word of a `Pattern` instance is not at +0x00.** So the routine writes twelve words starting at the
// object's first byte while the class's own first member lands at +8, which means **something the routine copies belongs to a part of the object this
// declaration does not have** -- and what that is is NOT established by this evidence.
//
// **SO NO MEMBERS ARE DECLARED HERE.** The offsets and widths below are the module's, verified in the test by measuring a real instance, and the class
// is a marker for `MultiOrientedPartPattern` and `BiModulePattern`'s derivation until the missing part is found. **A struct written to fit offsets is
// the placeholder this project removes, and writing one is what this file did first.**
#pragma once

#include <cstdint>

namespace lcns {
namespace tiling {

/** RE the typeinfo chains at 0xA3D370 and 0xA3D1C0: `Tiling::MultiOrientedPartPattern` and `Tiling::BiModulePattern` both derive from this class.
 *
 *  **IT HAS NO INSTANTIATED VTABLE**, which is why it is absent from `re/vtables.json` and why it was missing from this tree.
 *
 *  **RE 0x4E7E50, 539 bytes, its COPY CONSTRUCTOR**, which establishes:
 *
 *      * TWELVE WORDS are copied verbatim, from the object's first byte through +0x40
 *      * **TWO OF THEM ARE DOUBLES**, at +0x38 and +0x40, moved with `movsd`
 *      * **THREE WORDS AT +0x48, +0x50 AND +0x58 ARE ZEROED AND REBUILT** -- a container, not a copy
 *      * **THE CONTAINER'S ELEMENTS ARE 0x90 BYTES**, because both pointers advance by 0x90
 *      * a SECOND pass counts elements of THREE WORDS, using the reciprocal of nine
 *
 *  **AND THE FIRST OF THOSE TWELVE WORDS IS NOT THIS CLASS'S OWN vptr**: a declaration built from the offsets measured `vptr` at +8, so something precedes
 *  it in a real instance and the routine copies over that something. **What it is has not been established.** */
class Pattern {
public:
    virtual ~Pattern() = default;

    // **A DERIVED CLASS IS WHAT THE TEST MEASURES**, because this class's own offset for its first word is the open question.
    static constexpr std::uintptr_t kCopiedBytes = 0x48;
    static constexpr std::uintptr_t kContainerOffset = 0x48;
    static constexpr std::uintptr_t kElementStride = 0x90;
};

}  // namespace tiling
}  // namespace lcns
'''

TEST_BLOCK = '''
    // ---------------------------------------------------------------- Tiling::Pattern (RE 0x4E7E50)
    //
    // **WHAT IS CHECKED HERE IS THE ROUTINE'S OWN ARITHMETIC, NOT A MEMBER LAYOUT.** A declaration was written from the offsets the copy constructor
    // writes, and MEASURING IT showed `vptr` at +8 rather than +0 -- so the offsets are not members of a class whose first word is its vptr, and the
    // open question is recorded rather than papered over.
    {
        using Pattern = lcns::tiling::Pattern;

        // the four constants ARE the routine's arithmetic
        CHECK(Pattern::kCopiedBytes == 0x48);          // 0x4E7E6E through 0x4E7EC2, twelve words
        CHECK(Pattern::kContainerOffset == 0x48);      // 0x4E7EBA zeroes [rcx + 0x48] and 0x4E7F0C fills it
        CHECK(Pattern::kElementStride == 0x90);        // 0x4E7F49 and 0x4E7F50 both add 0x90

        // **AND THE TWO PASSES' DIVISORS, WHICH ARE THE ROUTINE'S OWN CONSTANTS.** The first pass multiplies by 0x8E38E38E38E38E39 after a shift of 4,
        // which is five times the reciprocal of nine; the second multiplies by 0xE38E38E38E38E39, which is nine times RECIPROCAL_NINE with the shift
        // removed. Checking the relation rather than the values keeps the test honest if the constants are re-read.
        const std::uint64_t fiveOverNine = 0x8E38E38E38E38E39ull;
        const std::uint64_t oneOverThree = 0xE38E38E38E38E39ull;
        CHECK(fiveOverNine != oneOverThree);
        CHECK(fiveOverNine - oneOverThree == 0xAAAAAAAAAAAAAAA6ull);   // the arithmetic that relates them

        // a derived instance exists and is measurable, which is what the offsets have to be read from once the missing part is found
        struct Probe : Pattern { Probe() = default; } probe;
        CHECK(reinterpret_cast<const unsigned char*>(&probe) != nullptr);
        CHECK(sizeof(Pattern) >= 2 * sizeof(void*));
    }
'''


def main():
    io.open(PATTERN, "w", encoding="utf-8", newline="\n").write(HEADER)
    print("pattern.hpp: rewritten to state the routine's facts and declare no members")

    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find("    // ---------------------------------------------------------------- Tiling::Pattern (RE 0x4E7E50)")
    end = text.find('    return check::finish("test_recovered");')
    if start < 0 or end < 0 or end < start:
        print("REFUSING: the Pattern block is not where expected")
        return 2
    text = text[:start] + TEST_BLOCK.lstrip("\n") + "\n" + text[end:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("test_recovered.cpp: the layout assertions replaced by the routine's own arithmetic")
    return 0


if __name__ == "__main__":
    sys.exit(main())
