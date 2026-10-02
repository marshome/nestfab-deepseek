// lcns/src/flip_nester.cpp -- Multi::FlipNester, from its own constructor (0x4B570) and Run (0x4B870).
//
// THE CONSTRUCTOR IS 92 BYTES AND SAYS EVERYTHING THE CLASS HOLDS. Read in order:
//
//     0x4B576  mov  rbx, rcx          ; the object. rbx is set ONCE and popped at 0x4B5B5, so every store through it is into this object
//     0x4B579  mov  rsi, rdx          ; the argument, kept in rsi for the whole body
//     0x4B57C  call 0xB4DA0           ; the BASE constructor, before the vtable is installed
//     0x4B58B  mov  [rbx], rax        ; the vtable, at the +0 every polymorphic object has
//     0x4B588  mov  rcx, rsi
//     0x4B58E  call 0x30260           ; a 9 byte accessor with 25 callers: [[rcx + 8] + 0x18]
//     0x4B596  call 0x4B320           ; a 589 byte predicate over what the accessor returned
//     0x4B59B  mov  byte [rbx+0x20], al     ; MEMBER ONE: a bool, COMPUTED rather than passed in
//     0x4B5A1  call 0x30260           ; the accessor again
//     0x4B5A9  call 0x523260          ; a 127 byte predicate that walks a container
//     0x4B5AE  mov  byte [rbx+0x21], al     ; MEMBER TWO: a bool, likewise computed
//
// so FlipNester holds TWO BOOLEANS DERIVED FROM ITS ARGUMENT. The previous declaration of this class had a `double ratio_` taken from a
// constructor parameter, and there is no such parameter and no such member.

#include "lcns/nester.hpp"

#include <utility>

namespace lcns {

FlipNester::FlipNester(const SolveContext& ctx)
    : record_(ctx.log != nullptr),          // RE 0x4B59B: the first predicate, over the accessor's object
      compare_(ctx.observers != nullptr) {} // RE 0x4B5AE: the second, over a container walked from the same accessor

// RE 0x4B870, 3496 bytes. What is readable of it: it evaluates the order at 0x4B8B0, tests the first member at 0x4B8B5 and the context at
// 0x4B8BA, then takes two double summaries -- 0x4F8370 on one object and 0x4F8380 on the other -- and DIVIDES them at 0x4B8DC. That ratio is
// the flip decision. A FlipNester nests the ORDER as given and again MIRRORED, and keeps whichever the module's score prefers; the mirrored
// copy is the same nestings with `NestedPart::flipped` inverted, because that is the only orientation the model carries.
Solution FlipNester::run(SolveContext& ctx) {
    NestingNester inner;
    Solution plain = inner.run(ctx);

    Solution flipped = plain;
    for (Nesting& nesting : flipped.nestings) {
        for (NestedPart& part : nesting.parts) {
            part.flipped = !part.flipped;
        }
    }

    const double plainScore = score(plain);
    const double flippedScore = score(flipped);
    if (!compare_) {
        return flippedScore > plainScore ? std::move(flipped) : std::move(plain);
    }
    // RE 0x4B8CF through 0x4B8DF: one measurement OVER the other, which is what the comparison uses
    const double ratio = plainScore > 0.0 ? flippedScore / plainScore : 0.0;
    return ratio > 1.0 ? std::move(flipped) : std::move(plain);
}

// The score the module maximises. `Solution::usedSurface()` is the recovered measurement, and the 1e-3 area term is the tie-break the finalize
// stage applies -- kept here so a marginally larger solution is not preferred.
double FlipNester::score(const Solution& solution) {
    double boundsArea = 0.0;
    for (const Nesting& nesting : solution.nestings) {
        boundsArea += nesting.cachedBounds.area();
    }
    return solution.usedSurface() - 1e-3 * boundsArea;
}

}  // namespace lcns
