// lcns/include/lcns/stat.hpp -- the element predicates, and the range accumulator ../structure/stat.cpp builds with them.
//
// RE 0x52F810 (7 bytes) and RE 0x52F830 (10 bytes) are the ENTIRE difference between the GetLength and GetHeight exports:
//
//     0x52F810  cmp  dword ptr [rcx], 1          ; the element's word
//               setbe al                          ; al = (value <= 1)
//               ret
//     0x52F830  test dword ptr [rcx], 0xFFFFFFFD
//               sete al                           ; al = (value & ~2) == 0
//               ret
//
// so one accepts {0, 1} and the other {0, 2}; each takes one pointer and returns a boolean in al; and the pointer each reads is
// the ELEMENT its aggregator is visiting.
//
// THE ACCUMULATOR THEY PARAMETERISE, read from RE 0x526160 (757 bytes):
//
//     0x526194  call 0x51D0C0          ; the container
//     0x5261A7  mov rbx, [rax]         ; begin
//     0x5261B9  mov rdi, [rax + 8]     ; end
//     0x5261CF  cmp rbx, rdi
//     0x5261D2  je  <empty>
//     0x5261D4  mov rdx, rbx           ; one element
//     0x5261DA  add rbx, 0x78          ; ADVANCE BY 0x78 = 120 bytes
//     0x5261DE  call 0x524EE0          ; process the element into a value
//     0x5261E9  call 0x5C8C50          ; fold that value into a min/max accumulator on the stack
//     0x5261EE  cmp rdi, rbx / jne     ; and round again
//     ...
//     0x526227  movsd xmm0, [rsp+0xb8]
//     0x526230  subsd xmm0, [rsp+0x78] ; THE RESULT IS max - min
//
// so it walks a container of records with a stride of 0x78, folds each element's measurement into a running minimum and maximum,
// and returns the extent -- which is what a function called GetLength or GetHeight returns about a set of parts. The predicate is
// applied to the ELEMENT (rcx = rsp+0x108, an element-shaped scratch) and selects which axis the extent is taken on: `{0,1}` for
// one and `{0,2}` for the other.
//
// What is written here is the accumulator's RULE and the two predicates, and not the element walk, because the walk needs
// 0x524EE0 and 0x5C8C50 read first and inventing their contract would be the guess this project refuses. The rule is fully
// determined though, and it is the part a reader needs.
#pragma once

#include <cstdint>
#include <limits>

namespace lcns {

/** RE 0x52F810: true when the element's word is 0 or 1. `cmp dword [rcx],1 ; setbe`. */
inline bool statIsShortAxis(const void* element) {
    const std::uint32_t value = *static_cast<const std::uint32_t*>(element);
    return value <= 1u;
}

/** RE 0x52F830: true when the element's word is 0 or 2. `test dword [rcx],0xFFFFFFFD ; sete`. */
inline bool statIsLongAxis(const void* element) {
    const std::uint32_t value = *static_cast<const std::uint32_t*>(element);
    return value == 0u || value == 2u;
}

/** The element stride the accumulator walks, RE 0x5261DA: `add rbx, 0x78`. */
constexpr std::size_t kStatElementStride = 0x78;

/** RE 0x526160 and RE 0x5266A0: the extent of a set, which is what GetLength and GetHeight return.
 *
 * The two exported aggregators call the same seven functions and differ at ONE pointer -- 0x52F810 for length, 0x52F830 for
 * height -- so the algorithm is one accumulator parameterised by an element predicate, and this is that shape. The result is
 * `max - min`, which RE 0x526230 performs with a single `subsd` after the walk.
 *
 * `measure` is the per-element measurement (RE 0x524EE0 followed by 0x5C8C50 in the original) and `accept` is the predicate. They
 * are parameters rather than recovered bodies because the two functions that implement them have not been read, and a guess at
 * their contract would be worse than a parameter.
 */
template <typename Element, typename Measure, typename Accept>
double statExtent(const Element* begin, const Element* end, Measure measure, Accept accept) {
    double low = std::numeric_limits<double>::max();
    double high = std::numeric_limits<double>::lowest();
    bool any = false;
    for (const Element* element = begin; element != end; ++element) {          // RE 0x5261D4 and 0x5261EE
        if (!accept(element)) {                                                // RE 0x52621E, the predicate on the element
            continue;
        }
        const double value = measure(element);                                 // RE 0x5261DE and 0x5261E9
        low = value < low ? value : low;                                       // RE the fold at 0x5C8C50
        high = value > high ? value : high;
        any = true;
    }
    // RE 0x526227 and 0x526230: the result is the difference, and an empty set leaves the sentinels to cancel
    return any ? high - low : 0.0;
}

}  // namespace lcns
