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

/** RE 0x5C8C50: fold one element's FOUR doubles into a box of two (low, high) pairs.
 *
 * READ FROM THE WHOLE 255 BYTE BODY, both halves, which is what three earlier attempts did not do. The routine's three branches:
 *
 *     the ELEMENT's flag at +0x00 is zero   -> return without touching the box     (0x5C8C50, je, 0x5C8C55 ret)
 *     the BOX's flag at +0x00 is NONZERO    -> BUILD, then fall into the compare of c and d   (0x5C8D10 .. 0x5C8D4D)
 *     the BOX's flag at +0x00 is ZERO       -> COMPARE a, b, c and d against the box          (0x5C8C69 .. 0x5C8D0B)
 *
 * THE BUILD PATH, 0x5C8D10, copies the element's first two doubles into ALL FOUR slots and clears the flag:
 *
 *     0x5C8D1B  mov [rcx + 8],   [rdx + 8]        ; low0  = a
 *     0x5C8D24  mov [rcx + 0x10],[rdx + 0x10]     ; low1  = b
 *     0x5C8D35  mov [rcx + 0x18],[rdx + 8]        ; high0 = a
 *     0x5C8D39  mov [rcx + 0x20],[rdx + 0x10]     ; high1 = b
 *     0x5C8D14  mov byte ptr [rcx], 0             ; AND THE FLAG IS CLEARED
 *     0x5C8D47  ucomisd xmm1, xmm0 / ja 0x5C8CD1 / jmp 0x5C8CDB   ; then JOIN the compare path at c
 *
 * THE COMPARE PATH, four compare-and-keep pairs over
 *
 *     element +8    against low0 and high0        (0x5C8C69 .. 0x5C8C8F)
 *     element +0x10 against low1 and high1        (0x5C8C94 .. 0x5C8CBD)
 *     element +0x18 against low0 and high0 AGAIN  (0x5C8CC6 .. 0x5C8CE2)
 *     element +0x20 against low1 and high1 AGAIN  (0x5C8CE7 .. 0x5C8D06)
 *
 * **SO `valid` MEANS "BUILD ME" AND NOT "I AM VALID"**, which is why the initialiser RE 0x4E5B0 stores 1 into such a byte: a fresh box
 * needs its first element installed rather than compared against zeros. An earlier version of this struct had the polarity the other way
 * and one value per axis, and it was replaced rather than patched -- the three attempts are in re/blockers.json.
 *
 * THE ELEMENT IS FOUR DOUBLES, at +8, +0x10, +0x18 and +0x20, and all four reach the box: a and b set it, then c and d are compared
 * against what a and b installed.
 */
struct StatBox {
    unsigned char valid = 0;                // +0x00: NONZERO means build from the first element; zero means compare
    double low0 = 0.0;                      // +0x08
    double low1 = 0.0;                      // +0x10
    double high0 = 0.0;                     // +0x18
    double high1 = 0.0;                     // +0x20

    /** One axis's compare-and-keep, the pair of instructions the body repeats four times. */
    static void keep(double value, double& low, double& high) {
        if (value < low) {                                  // RE 0x5C8C73 with 0x5C8C79
            low = value;
        }
        if (value > high) {                                 // RE 0x5C8C88 with 0x5C8C8F
            high = value;
        }
    }

    /** Fold one element's four doubles in. RE 0x5C8C50, whole body.
     *
     * `element_valid` is the element's flag at its +0x00; a zero element is skipped entirely. `a`, `b`, `c` and `d` are the element's four
     * doubles at +8, +0x10, +0x18 and +0x20, named by POSITION because the routine gives them no other identity: a and b go to the two
     * axes, then c and d are compared against the same two axes.
     */
    void fold(bool element_valid, double a, double b, double c, double d) {
        if (!element_valid) {                               // RE 0x5C8C50 / je / 0x5C8C55 ret
            return;
        }
        if (valid) {
            // THE BUILD PATH: 0x5C8D10 installs a and b into both ends of both axes and clears the flag
            low0 = a;                                       // RE 0x5C8D1B
            low1 = b;                                       // RE 0x5C8D24
            high0 = a;                                      // RE 0x5C8D35
            high1 = b;                                      // RE 0x5C8D39
            valid = 0;                                      // RE 0x5C8D14
            // and then the compare path's second half runs, for c and d
            keep(c, low0, high0);                           // RE 0x5C8CC6 / 0x5C8CD1 / 0x5C8CDB / 0x5C8CE2
            keep(d, low1, high1);                           // RE 0x5C8CE7 / 0x5C8CF2 / 0x5C8CFC / 0x5C8D06
            return;
        }
        keep(a, low0, high0);                               // RE 0x5C8C69 / 0x5C8C79 / 0x5C8C88 / 0x5C8C8F
        keep(b, low1, high1);                               // RE 0x5C8C94 / 0x5C8CA4 / 0x5C8CB2 / 0x5C8CBD
        keep(c, low0, high0);                               // RE 0x5C8CC6 / 0x5C8CD1 / 0x5C8CDB / 0x5C8CE2
        keep(d, low1, high1);                               // RE 0x5C8CE7 / 0x5C8CF2 / 0x5C8CFC / 0x5C8D06
    }

    /** The single-axis form kept for statExtent, which folds one measurement per element. It is NOT RE 0x5C8C50: it is a convenience for
     *  the accumulator at 0x526160, which uses one axis, and it is named apart so the two cannot be confused again. */
    void foldSingle(bool element_valid, double value, bool& seen, double& low, double& high) {
        if (!element_valid) {
            return;
        }
        if (!seen) {
            low = high = value;
            seen = true;
            return;
        }
        keep(value, low, high);
    }
};

/** RE 0x526160 and RE 0x5266A0: the extent of a set, which is what GetLength and GetHeight return.
 *
 * The walk advances by kStatElementStride, folds each element into a box, and returns `max - min`, which RE 0x526230 performs with
 * a single `subsd` after the walk. `measure` is the per-element measurement -- RE 0x524EE0 followed by the fold -- and `accept` is
 * the predicate that selects the axis: 0x52F810 for one twin and 0x52F830 for the other.
 */
template <typename Element, typename Measure, typename Accept>
double statExtent(const Element* begin, const Element* end, Measure measure, Accept accept) {
    StatBox box;
    bool seen = false;
    for (const Element* element = begin; element != end; ++element) {          // RE 0x5261D4 and 0x5261EE
        if (!accept(element)) {                                                // RE 0x52621E, the predicate on the element
            continue;
        }
        const double value = measure(element);                                 // RE 0x5261DE and 0x5261E9
        box.foldSingle(true, value, seen, box.low0, box.high0);                // one axis, not RE 0x5C8C50's four
    }
    return (box.high0 - box.low0);                                             // RE 0x526227 and 0x526230
}

}  // namespace lcns
