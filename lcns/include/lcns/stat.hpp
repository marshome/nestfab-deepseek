// lcns/include/lcns/stat.hpp -- the two element predicates that ../structure/stat.cpp's aggregators are parameterised by.
//
// RE 0x52F810 (7 bytes) and RE 0x52F830 (10 bytes). They are the ONLY difference between the length and height aggregators
// 0x526160 and 0x5266A0, whose bodies call the same seven functions in the same order and then differ at this one pointer:
//
//     0x52F810   cmp  dword ptr [rcx], 1          ; the element's word
//                setbe al                          ; al = (value <= 1)
//                ret
//
//     0x52F830   test dword ptr [rcx], 0xFFFFFFFD
//                sete al                           ; al = (value & ~2) == 0
//                ret
//
// so the predicate is `value <= 1`, which is true exactly for {0, 1}, and `(value & ~2) == 0`, which is true exactly for {0, 2}.
// Both take one pointer and return a boolean in al, and the pointer they read is the ELEMENT the aggregator is visiting.
//
// Two facts follow and both are the reason this is worth a header rather than a comment:
//
//   * the two exports `GetLength` and `GetHeight` differ ONLY here, so writing the aggregator once with this predicate as a
//     parameter writes both of them -- and the original did exactly that, since the two leaf functions are twenty bytes apart and
//     the two aggregators are 757 and 759 bytes;
//   * `(value & ~2) == 0` is the compiler's way of writing `value == 0 || value == 2` for a value already known to be small, and
//     writing the mask rather than the comparison would be reproducing the compiler instead of the source. The recovered form is
//     the comparison, and the mask is recorded beside it as the evidence.
#pragma once

#include <cstdint>

namespace lcns {

/** RE 0x52F810: true when the element's word is 0 or 1. The instruction is `cmp dword [rcx],1 ; setbe`. */
inline bool statIsShortAxis(const void* element) {
    const std::uint32_t value = *static_cast<const std::uint32_t*>(element);
    return value <= 1u;
}

/** RE 0x52F830: true when the element's word is 0 or 2. The instruction is `test dword [rcx],0xFFFFFFFD ; sete`. */
inline bool statIsLongAxis(const void* element) {
    const std::uint32_t value = *static_cast<const std::uint32_t*>(element);
    return value == 0u || value == 2u;
}

}  // namespace lcns
