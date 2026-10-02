// lcns/include/lcns/small_buffer.hpp -- the object RE 0x6DE480 constructs, as a TYPE with real members.
//
// THIS REPLACES SIX CONSTANTS. layout.hpp described this object as `kInlineBufferA/B/C`, `kInlineTargetA/B/C` and `kInlineBufferPairs = 3` --
// six `constexpr std::size_t` and a count, with instructions in comments -- and the human asked what kind of C++ that is. **It is not C++; it
// is notes about C++.** These are the types those notes were about, and every member below carries the instruction that placed it.
//
// THE CONSTRUCTOR 0x6DE480, in full:
//
//     0x6DE48E  mov ecx, 0x18              ; the block is 0x18 bytes
//     0x6DE493  lea rax, [rax + 0x10]      ; a buffer begins at +0x10
//     0x6DE497  mov [rbx + 8], 0           ; the first pair's SIZE is zero
//     0x6DE49F  mov [rbx], rax             ; and its POINTER is that buffer
//     0x6DE4A2  xor eax, eax / 0x6DE4A4 mov word [rbx + 0x10], ax
//     0x6DE4A8  lea rax, [rbx + 0x30]      ; a SECOND buffer, at +0x30
//     0x6DE4AC  mov [rbx + 0x20], rax      ; the second pair's pointer
//     0x6DE4B4  mov [rbx + 0x28], 0        ; and its size
//     0x6DE4BC  mov word [rbx + 0x30], dx  ; two zero bytes at the second buffer's start
//     0x6DE4C0  mov [rbx + 0x40], rax      ; a THIRD pair pointing at the SAME +0x30
//     0x6DE4C4  mov [rbx + 0x48], 0
//     0x6DE4CC  mov byte ptr [rbx + 0x50], 0
//
// THE FOUR FACTS THAT ONLY A TYPE CAN STATE, and that six constants could not:
//
//   * there are THREE (pointer, size) pairs, and the third SHARES the second's storage -- `0x6DE4C0` stores the same rax that `0x6DE4A8`
//     computed. A list of offsets can say both addresses; it cannot say they are one buffer.
//   * the storage is INSIDE the object: the pointers are to `this + 0x10` and `this + 0x30`, not to the heap.
//   * the object is ALLOCATED, because 0x6DE48E asks for 0x18 -- so it is not embedded in whatever holds it.
//   * the two byte-pairs at the buffers' starts are written with `word` operands, so their width is two bytes and their meaning is not known.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

/** A (pointer, size) pair, which RE 0x6DE480 writes three times. **This type is the difference between this header and the one it replaces**:
 *  the constants named the offsets of a shape that had no name. */
struct BufferView {
    void* data = nullptr;       // RE 0x6DE49F, 0x6DE4AC and 0x6DE4C0 all store a buffer address here
    std::size_t size = 0;       // RE 0x6DE497, 0x6DE4B4 and 0x6DE4C4 all store zero here
};

/** The object RE 0x6DE480 constructs.
 *
 *  ITS SIZE IS 0x58 BYTES and the allocator is asked for 0x18, so **the 0x18 is a SUB-BLOCK the object points at** rather than the object
 *  itself: `mov ecx, 0x18` is a separate allocation from the two 0x60 blocks the same function takes. The `inline_` arrays are that
 *  sub-block, which is why the class holds them by value and the BufferViews point INTO them.
 *
 *  THE MEMBER NAMES SAY WHAT IS KNOWN AND NOT MORE. `first` and `second` are the two pairs the instructions write in that order; nothing read
 *  says what they mean, and **a name needs an oracle** -- the module's own string, or a setter whose instruction is the field's. What they
 *  have is a type and an offset, which is what a declaration needs and what a table of offsets is not.
 */
class SmallBuffer {
public:
    SmallBuffer() = default;

    BufferView first{};                             // +0x00 .. +0x10, RE 0x6DE49F and 0x6DE497
    std::byte inline_a[0x10]{};                     // +0x10 .. +0x20, the first buffer, RE 0x6DE493 and 0x6DE4A4
    BufferView second{};                            // +0x20 .. +0x30, RE 0x6DE4AC and 0x6DE4B4
    std::byte inline_b[0x10]{};                     // +0x30 .. +0x40, the second buffer, RE 0x6DE4A8 and 0x6DE4BC
    BufferView third{};                             // +0x40 .. +0x50, RE 0x6DE4C0 and 0x6DE4C4 -- and it SHARES inline_b
    std::uint8_t tail = 0;                          // +0x50, RE 0x6DE4CC

    /** RE 0x6DE48E: the sub-block the allocator is asked for, so the two inline arrays are one 0x18 byte region at +0x10. */
    static constexpr std::size_t kSubBlockBytes = 0x18;
    static constexpr std::size_t kFirstBufferOffset = 0x10;
    static constexpr std::size_t kSecondBufferOffset = 0x30;
};

/** The 0x60 byte block that OWNS a SmallBuffer, RE 0x6DE4D0 onward. It is polymorphic: 0x6DE4F5 stores a vtable pointer at its first
 *  quadword, and the vtable is 0x35E739. */
struct BufferOwner {
    void** vtable = nullptr;                    // +0x00, RE 0x6DE4F5: mov qword ptr [rax], rdx
    std::uint32_t refcount = 1;                 // +0x08, RE 0x6DE4E7: mov dword ptr [rax + 8], 1
    std::uint32_t flags = 1;                    // +0x0C, RE 0x6DE4EE: mov dword ptr [rax + 0xc], 1
    SmallBuffer* payload = nullptr;             // +0x10, RE 0x6DE4D9: mov qword ptr [rax + 0x10], rbx

    static constexpr std::uintptr_t kVtableRva = 0x35E739;   // RE 0x6DE4E0: lea rdx, [rip + 0x35e739]
    static constexpr std::size_t kBytes = 0x60;              // RE 0x6DE4D0
};

// THE LAYOUT IS THE TYPE'S OWN. Every offset below is the instruction's, so a member added in the wrong place fails the build rather than
// producing a class that is quietly not the module's.
static_assert(sizeof(BufferView) == 0x10, "a pointer and a size, which is the 0x10 the pairs are apart by");
static_assert(offsetof(SmallBuffer, first) == 0x00, "RE 0x6DE49F: mov [rbx], rax");
static_assert(offsetof(SmallBuffer, inline_a) == 0x10, "RE 0x6DE493: lea rax, [rax + 0x10]");
static_assert(offsetof(SmallBuffer, second) == 0x20, "RE 0x6DE4AC: mov [rbx + 0x20], rax");
static_assert(offsetof(SmallBuffer, inline_b) == 0x30, "RE 0x6DE4A8: lea rax, [rbx + 0x30]");
static_assert(offsetof(SmallBuffer, third) == 0x40, "RE 0x6DE4C0: mov [rbx + 0x40], rax");
static_assert(offsetof(SmallBuffer, tail) == 0x50, "RE 0x6DE4CC: mov byte ptr [rbx + 0x50], 0");

/** **THE FACT SIX CONSTANTS COULD NOT STATE**: the third pair points at the SAME storage as the second. The constructor computes the address
 *  once at 0x6DE4A8 and stores it twice, at 0x6DE4AC and 0x6DE4C0. */
inline bool thirdSharesSecondStorage() {
    SmallBuffer probe;
    probe.second.data = &probe.inline_b;        // RE 0x6DE4AC
    probe.third.data = &probe.inline_b;         // RE 0x6DE4C0
    return probe.second.data == probe.third.data;
}

static_assert(offsetof(BufferOwner, refcount) == 0x08, "RE 0x6DE4E7");
static_assert(offsetof(BufferOwner, flags) == 0x0C, "RE 0x6DE4EE");
static_assert(offsetof(BufferOwner, payload) == 0x10, "RE 0x6DE4D9");
static_assert(BufferOwner::kVtableRva == 0x35E739, "RE 0x6DE4E0");

}  // namespace lcns
