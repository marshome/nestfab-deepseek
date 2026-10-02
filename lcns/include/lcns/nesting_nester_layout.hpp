// lcns/include/lcns/nesting_nester_layout.hpp -- Multi::NestingNester's OBJECT LAYOUT as real C++ types.
//
// WHY THIS EXISTS. lcns/nesting_nester_fields.hpp holds a `FieldStore` table -- offsets, widths, addresses and notes -- and the human was
// right that **a table of offsets is metadata ABOUT a class, not a class.** A C++ class has members with types and a constructor; the offsets
// are the EVIDENCE for where the members go.
//
// AND READING THE CONSTRUCTOR'S TAIL PROVED THE TABLE WRONG. RE 0x342E0's last third is a loop:
//
//     0x34344  mov eax, ecx / shr eax, 0x1e / xor eax, ecx
//     0x3434B  imul eax, eax, 0x6c078965          ; the MT19937 seed multiplier, 1812433253
//     0x34351  lea ecx, [rax + rdx]
//     0x34354  mov [rbx + rdx*4 + 0x38], ecx      ; a 32 bit word into an array based at +0x38
//     0x34358  add rdx, 1
//     0x3435C  cmp rdx, 0x270                     ; 624 -- the MT19937 state size
//     0x34363  jne 0x34344
//     0x3436D  mov qword [rbx + 0x9f8], 0x270     ; and the index set to 624, which means untwisted
//
// **SO +0x9F8 IS NOT "A FIELD" AMONG SEVEN: it is the twist index of a 624 word Mersenne Twister whose state begins at +0x38.** A table of
// distinct offsets cannot tell a member from an element count, which is why the class had to be written out.
//
// THE POLYMORPHIC PART IS SEPARATE, AND THE COMPILER SAID SO. A first version made one polymorphic class and asserted offsetof on it, which
// GCC answers with `-Winvalid-offsetof`: **offsetof on a non-standard-layout type is conditionally supported**, and the condition is exactly
// the thing being measured. So the layout is a STANDARD-LAYOUT struct whose offsets are guaranteed, and the vtable pointer that precedes it
// in the module's object is named as the offset it is.
#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace lcns {
namespace Multi {

/** The two halves of the constructor's third argument. RE 0x342EF `mov rdi, r8`, then 0x3430B reads [rdi] and 0x34301 reads [rdi + 8]. */
struct SeedPair {
    void* first = nullptr;                  // RE 0x3430B: mov rax, [rdi]
    void* second = nullptr;                 // RE 0x34301: mov rdx, [rdi + 8]
};

/** The Mersenne Twister the nester embeds, at the offsets RE 0x342E0 gives it.
 *
 *  The constants are the module's own and they identify the algorithm: 0x6C078965 is 1812433253, the standard seeding multiplier, and 0x270
 *  is 624, the state size. **A reader of `imul eax, eax, 0x6c078965` should not have to recognise a magic number to learn that this class
 *  carries a random number generator**, so both are named rather than left in a comment.
 */
struct Mt19937 {
    static constexpr std::size_t kStateSize = 624;                  // RE 0x3435C: cmp rdx, 0x270
    static constexpr std::uint32_t kSeedMultiplier = 0x6C078965u;   // RE 0x3434B: the standard 1812433253

    std::array<std::uint32_t, kStateSize> state{};                  // RE 0x34354: [rbx + rdx*4 + 0x38]
    std::uint32_t index = kStateSize;                               // RE 0x3436D: 0x270 means untwisted
};

/** Multi::NestingNester's layout, as RE 0x342E0 builds it, as a STANDARD-LAYOUT struct so every offset below is guaranteed.
 *
 *  THE MEMBER NAMES SAY WHAT IS KNOWN AND NOT MORE. `seedP` and `seedQ` are the two halves of the constructor's third argument and nothing
 *  read so far says what they mean, so they are named by their ROLE in the constructor rather than given a meaning the evidence does not
 *  support: **a name needs an oracle** -- the module's own string, or a setter whose instruction is the field's -- and these have neither.
 *  What they have is a type and an offset, which is what a C++ declaration needs and what a table of offsets is not.
 *
 *  THIS STRUCT BEGINS WHERE THE MODULE'S FIRST DATA MEMBER BEGINS, at +0x18. The vtable pointer at +0 is not a member of it: it belongs to
 *  the polymorphic class in lcns/nester.hpp, and adding a virtual here to represent it would shift every offset below by eight and make the
 *  whole layout wrong.
 */
struct NestingNesterFields {
    void* seedP = nullptr;                  // +0x18, RE 0x34312 from [rdi]
    void* seedQ = nullptr;                  // +0x20, RE 0x3430E from [rdi + 8]
    std::uint32_t seed = 0;                 // +0x28, RE 0x34341 -- converted from a double by 0x34323's cvttsd2si
    double ratio = 0.0;                     // +0x30, RE 0x343E3 -- one measurement divided by another at 0x343DF

    Mt19937 twister{};                      // +0x38, RE 0x34354 and 0x3436D: 624 words and their index, INSIDE the object

    /** RE 0x34388: `lea rcx, [rbx + 0xa00]` -- a sub-object past the state, handed to 0x4f0c20. Its size is NOT established; this is the
     *  bound the profile's class size leaves, and the comment says it is a bound rather than a measurement. */
    std::array<std::byte, 0x40> tail{};
};

/** The offsets in the MODULE's object, which is what the instructions above use. The first data member is at 0x18 because a vtable pointer
 *  occupies 0x00 and a second pointer precedes it at 0x10. */
constexpr std::size_t kNestingNesterVtablePointer = 0x00;   // RE 0x34308: mov [rbx], rax
constexpr std::size_t kNestingNesterFieldsStart = 0x18;     // RE 0x34312: the first store past the two pointers
constexpr std::size_t kNestingNesterObjectBytes = 0xA40;    // RE: the class size the profile gives

// EVERY OFFSET IS CHECKED AGAINST THE INSTRUCTION THAT PLACED IT. The first four are the standard-layout struct's own, so they are exact.
static_assert(offsetof(SeedPair, first) == 0x00, "RE 0x3430B: mov rax, [rdi]");
static_assert(offsetof(SeedPair, second) == 0x08, "RE 0x34301: mov rdx, [rdi + 8]");
static_assert(offsetof(Mt19937, state) == 0x00, "the array starts at the twister's own base");
static_assert(offsetof(Mt19937, index) == 624 * 4, "RE 0x3436D: 0x9F8 - 0x38 = 624 * 4");
static_assert(offsetof(NestingNesterFields, seedP) == 0x00, "RE 0x34312 minus the 0x18 the field block starts at");
static_assert(offsetof(NestingNesterFields, seedQ) == 0x08, "RE 0x3430E: 0x20 - 0x18");
static_assert(offsetof(NestingNesterFields, seed) == 0x10, "RE 0x34341: 0x28 - 0x18");
static_assert(offsetof(NestingNesterFields, ratio) == 0x18, "RE 0x343E3: 0x30 - 0x18");
static_assert(offsetof(NestingNesterFields, twister) == 0x20, "RE 0x34354: 0x38 - 0x18");
static_assert(kNestingNesterFieldsStart + offsetof(NestingNesterFields, twister) == 0x38,
              "the field block plus the twister's offset is the module's 0x38");
// THE `tail` MEMBER IS NOT ASSERTED, AND THE REASON IS WORTH KEEPING: its size is NOT established -- RE 0x34388 says a sub-object begins at
// 0xa00 and says nothing about how long it is -- so its offset depends on the twister's size PLUS whatever padding the compiler chooses.
// **An offset that depends on a guessed member's size is not a measurement**, so the module's 0xa00 is recorded as a constant with its
// instruction and the member that happens to land near it is not asserted against it. A first version asserted 0x9E8 and the compiler
// refused, which is the assertion doing its job.
static_assert(Mt19937::kStateSize == 624, "RE 0x3435C: cmp rdx, 0x270");
static_assert(Mt19937::kSeedMultiplier == 1812433253u, "RE 0x3434B: imul eax, eax, 0x6c078965");
static_assert(sizeof(Mt19937::state) == 2496, "624 words of four bytes");
// the twister's own two members are exact, because Mt19937 has no padding between them
static_assert(offsetof(Mt19937, state) == 0x00, "the array starts at the twister's own base");
static_assert(offsetof(Mt19937, index) == 624 * 4, "the index follows all 624 words with no padding");

/** The offsets the INSTRUCTIONS use, which is what the module's object has. These are the numbers a reader needs, and each carries its site. */
constexpr std::size_t kNestingNesterSeedP = 0x18;    // RE 0x34312: mov [rbx + 0x18], rax
constexpr std::size_t kNestingNesterSeedQ = 0x20;    // RE 0x3430E: mov [rbx + 0x20], rdx
constexpr std::size_t kNestingNesterSeed = 0x28;     // RE 0x34341: mov [rbx + 0x28], eax
constexpr std::size_t kNestingNesterRatio = 0x30;    // RE 0x343E3: movsd [rbx + 0x30], xmm6
constexpr std::size_t kNestingNesterTwister = 0x38;  // RE 0x34354: [rbx + rdx*4 + 0x38]
constexpr std::size_t kNestingNesterIndex = 0x9F8;   // RE 0x3436D: mov qword [rbx + 0x9f8], 0x270
constexpr std::size_t kNestingNesterTail = 0xA00;    // RE 0x34388: lea rcx, [rbx + 0xa00]
static_assert(kNestingNesterTwister - kNestingNesterSeedP == offsetof(NestingNesterFields, twister),
              "the field block's start: the module's 0x38 minus the block's own twister offset equals 0x18");

/** The constructor's SIGNATURE, as RE 0x342E0's register use gives it: rcx is the object, rdx is the second argument and r8 a SeedPair*. */
using NestingNesterCtor = void (*)(void* self, void* second, const SeedPair* seeds);
constexpr std::uintptr_t kNestingNesterCtorAddress = 0x342E0;   // 422 bytes
constexpr std::uintptr_t kNestingNesterBaseCtor = 0xB4470;      // RE 0x342F5, called before the vtable is installed

}  // namespace Multi
}  // namespace lcns
