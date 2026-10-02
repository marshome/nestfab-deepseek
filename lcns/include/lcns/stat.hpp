// lcns/include/lcns/stat.hpp -- the element predicates, the bounding-box fold, and the range they compute.
//
// Three routines from ../structure/stat.cpp, each read from its own instructions.
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
// so one accepts {0, 1} and the other {0, 2}; each takes one pointer and returns a boolean in al.
//
// RE 0x5C8C50 (255 bytes) is the FOLD, and its instructions give the accumulator's layout outright:
//
//     0x5C8C50  cmp  byte ptr [rdx], 0        ; rdx is the element, and its +0x00 is a VALID flag
//               je   <return>                  ; an invalid element is skipped entirely
//     0x5C8C60  cmp  byte ptr [rcx], 0        ; rcx is the accumulator, same flag
//               jne  <other route>
//     0x5C8C69  movsd xmm0, [rdx + 8]         ; the element's first measurement
//     0x5C8C6E  movsd xmm1, [rcx + 8]         ; the accumulator's current minimum
//     0x5C8C73  ucomisd xmm1, xmm0 / jbe
//     0x5C8C79  movsd [rcx + 8], xmm0         ; LOW = min(LOW, value)
//     0x5C8C88  ucomisd xmm0, [rcx + 0x18] / jbe
//     0x5C8C8F  movsd [rcx + 0x18], xmm0      ; HIGH = max(HIGH, value)
//     0x5C8C94  movsd xmm0, [rdx + 0x10]      ; and the same pair for the SECOND dimension
//     0x5C8C99  movsd xmm3, [rcx + 0x10]
//
// so the accumulator is `{flag +0x00, (min, max) per dimension starting at +0x08 and +0x18}` and the element is
// `{flag +0x00, one measurement per dimension}`, with the dimensions interleaved 0x10 apart. An element whose flag is zero
// contributes nothing.
//
// RE 0x526160 (757 bytes) is the walk that uses both, and RE 0x5266A0 (759 bytes) is its twin:
//
//     0x526194  call 0x51D0C0          ; the container
//     0x5261A7  mov  rbx, [rax]        ; begin
//     0x5261B9  mov  rdi, [rax + 8]    ; end
//     0x5261A2  mov  byte [rsp+0x70], 1 ; the accumulator's flag, set before the walk
//     0x5261D4  mov  rdx, rbx          ; one element
//     0x5261DA  add  rbx, 0x78         ; ADVANCE BY 0x78 = 120 bytes
//     0x5261DE  call 0x524EE0          ; measure the element
//     0x5261E9  call 0x5C8C50          ; fold it in
//     0x5261EE  cmp  rdi, rbx / jne    ; round again
//     0x526227  movsd xmm0, [rsp+0xb8]
//     0x526230  subsd xmm0, [rsp+0x78] ; THE RESULT IS max - min
//
// and the two twins differ at ONE pointer -- 0x52F810 for length, 0x52F830 for height -- so the original is this walk
// parameterised by an element predicate.
//
// What is a parameter here and why: 0x524EE0 is 1054 bytes and has NOT been read, so `statExtent` takes the measurement as a
// callable rather than inventing its contract. A guess at it would be the failure the ledger exists to refuse, and it is also why
// the four exports behind it are not forwarded.
#pragma once

#include <cstddef>
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

/** The element stride the walk uses, RE 0x5261DA: `add rbx, 0x78`. */
constexpr std::size_t kStatElementStride = 0x78;

/** The accumulator's own offsets, RE 0x5C8C50: `flag`, then (min, max) per dimension 0x10 apart. */
constexpr std::size_t kStatFlag = 0x00;
constexpr std::size_t kStatMin0 = 0x08;
constexpr std::size_t kStatMin1 = 0x10;
constexpr std::size_t kStatMax0 = 0x18;
constexpr std::size_t kStatMax1 = 0x20;

/** RE 0x5C8C50: fold one element's measurements into a running bounding box.
 *
 * An element whose +0x00 flag is zero is skipped, which is the routine's first instruction and the reason a set can contain
 * elements that do not contribute. Each dimension is a pair of comparisons, one against the current minimum and one against the
 * current maximum.
 */
struct StatBox {
    unsigned char valid = 0;                // +0x00
    double low0 = 0.0;                      // +0x08
    double low1 = 0.0;                      // +0x10
    double high0 = 0.0;                     // +0x18
    double high1 = 0.0;                     // +0x20

    /** RE 0x5C8C50 with one dimension, which is the whole of the two comparisons the routine performs per axis. */
    void fold(bool element_valid, double value, double& low, double& high) {
        if (!element_valid) {                                  // RE 0x5C8C50: cmp byte [rdx],0 ; je
            return;
        }
        if (!valid) {                                          // RE 0x5C8C60: the accumulator being unset
            low = high = value;
            valid = 1;
            return;
        }
        if (value < low) {                                     // RE 0x5C8C73: ucomisd + the jbe
            low = value;                                       // RE 0x5C8C79
        }
        if (value > high) {                                    // RE 0x5C8C88
            high = value;                                      // RE 0x5C8C8F
        }
    }
};

static_assert(offsetof(StatBox, low0) == kStatMin0, "RE 0x5C8C6E: movsd xmm1, [rcx+8]");
static_assert(offsetof(StatBox, low1) == kStatMin1, "RE 0x5C8C94: movsd xmm0, [rdx+0x10]");
static_assert(offsetof(StatBox, high0) == kStatMax0, "RE 0x5C8C88: ucomisd xmm0, [rcx+0x18]");
static_assert(offsetof(StatBox, high1) == kStatMax1, "the second dimension's maximum");

/** RE 0x526160 and RE 0x5266A0: the extent of a set, which is what GetLength and GetHeight return.
 *
 * The walk advances by kStatElementStride, folds each element into a box, and returns `max - min`, which RE 0x526230 performs with
 * a single `subsd` after the walk. `measure` is the per-element measurement -- RE 0x524EE0 followed by the fold -- and `accept` is
 * the predicate that selects the axis: 0x52F810 for one twin and 0x52F830 for the other.
 */
template <typename Element, typename Measure, typename Accept>
double statExtent(const Element* begin, const Element* end, Measure measure, Accept accept) {
    StatBox box;
    for (const Element* element = begin; element != end; ++element) {          // RE 0x5261D4 and 0x5261EE
        if (!accept(element)) {                                                // RE 0x52621E, the predicate on the element
            continue;
        }
        const double value = measure(element);                                 // RE 0x5261DE and 0x5261E9
        box.fold(true, value, box.low0, box.high0);                            // RE 0x5C8C50
    }
    return (box.high0 - box.low0);                                             // RE 0x526227 and 0x526230
}

}  // namespace lcns
