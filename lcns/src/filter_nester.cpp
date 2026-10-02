// lcns/src/filter_nester.cpp -- Multi::FilterNester, from the three functions that define it.
//
// THE CONSTRUCTOR 0xB3A70, 98 BYTES, AND IT CONTAINS A WHOLE MERSENNE TWISTER:
//
//     0xB3A75  mov  rbx, rcx                 ; the object, set once and popped at 0xB3AD0
//     0xB3A78  call 0xB4DA0                  ; the base constructor
//     0xB3A87  mov  dword [rbx+0x20], 1      ; THE SEED IS THE CONSTANT 1
//     0xB3A95  mov  [rbx], rax               ; the vtable, installed AFTER the seed
//     0xB3AA7  imul eax, eax, 0x6C078965     ; the MT19937 seeding multiplier
//     0xB3AB0  mov  dword [rbx+rdx*4+0x20], ecx   ; THE STATE ARRAY, 624 words based at +0x20
//     0xB3AC1  mov  qword [rbx+0x9E0], 0x270 ; the twist index set to the state size, meaning untwisted
//
// SLOT 2, 0xB43B0, 115 BYTES -- AND IT IS NOT AN ESTIMATE. It is the class's RESEED:
//
//     0xB43B9  lea  r8d, [rdx + 1]           ; THE SEED IS ITS ARGUMENT PLUS ONE
//     0xB43D1  (the MT19937 seeding loop, 624 iterations, into [rsp+0x20])
//     0xB43F5  lea  rcx, [rbx + 0x20]        ; the state is copied INTO THE OBJECT
//     0xB440B  call 0x63F2F8
//     0xB441E  jmp  0xB4440                  ; and then it falls into a 31 byte tail
//
// THE TAIL 0xB4440, 31 BYTES, WHICH IS WHERE THE DELEGATION IS:
//
//     0xB4449  mov  rcx, [rcx + 0x18]        ; AN INNER NESTER, at +0x18
//     0xB444F  mov  rax, [rcx]               ; its vtable
//     0xB4452  call qword ptr [rax + 0x10]   ; and its SLOT 2, with the same seed
//     0xB4455  mov  dword [rbx + 0x10], esi  ; THE SEED IS ALSO STORED, at +0x10
//
// so the class holds: an inner nester at +0x18 which does the nesting, the seed at +0x10, and a generator at +0x20. **Presenting this as an
// `estimate` was wrong** -- the vtable's slot 2 is this reseed, and the two middle slots are the trace prefix and a 894 byte routine.
//
// AND SLOT 5, 0xB3AE0, 2254 BYTES, IS THE RUN, where the generator is used as a coin:
//
//     0xB3B37  lea  rbx, [r12 + 0x20]        ; the generator, BY POINTER because the callee advances it
//     0xB3B47  movsd xmm0, [rax + 0x170]     ; a probability from the options
//     0xB3B4F  call 0x609E20                 ; the Bernoulli trial, 9 callers
//     0xB3B62  movsd xmm7, [rax + 0x178]     ; a second probability, eight bytes along
//     0xB3B6A  call 0x97A090                 ; and a 1599 byte routine with 17 callers producing a double

#include "lcns/nester.hpp"

#include <utility>

namespace lcns {

// RE 0xB3A87: the seed is the constant 1, so two FilterNesters built from one order draw the same numbers.
FilterNester::FilterNester() {
    seedMt(1);
}

// RE 0xB43B0 through 0xB43F5: the seeding recurrence and the 624 word state, which the constructor and the reseed BOTH perform -- which is why
// it is one function here rather than two copies.
void FilterNester::seedMt(std::uint32_t seed) {
    std::uint32_t value = seed;
    for (std::size_t index = 0; index < Mt19937::kStateSize; ++index) {
        value = Mt19937::kSeedMultiplier * (value ^ (value >> 30)) + static_cast<std::uint32_t>(index);
        rng_.state[index] = value;
    }
    rng_.index = Mt19937::kStateSize;      // RE 0xB3AC1 and 0xB43FF: the state size means untwisted
}

// RE 0xB43B0, slot 2: RESEED. The seed is the argument plus one, and the same index is forwarded to the inner nester's own slot 2 -- which the
// module reaches through that object's vtable, so the inner object implements THIS interface and `reset` is found on it.
void FilterNester::reset(int index) {
    const std::uint32_t seed = static_cast<std::uint32_t>(index + 1);   // RE 0xB43B9: lea r8d, [rdx + 1]
    seedMt(seed);
    if (inner_ != nullptr) {
        inner_->reset(index);              // RE 0xB4449 through 0xB4452: `mov rcx,[rcx+0x18]` then `call [rax+0x10]`
    }
    seed_ = index;                         // RE 0xB4455: mov dword [rbx + 0x10], esi
}

// RE 0x609E20: a Bernoulli trial. It compares the probability with zero and draws when it is positive, and it takes the generator BY POINTER
// because it advances the state.
bool FilterNester::draw(double probability) {
    if (!(probability > 0.0)) {
        return false;
    }
    if (rng_.index >= Mt19937::kStateSize) {
        rng_.index = 0;
    }
    const std::uint32_t word = rng_.state[rng_.index++];
    return static_cast<double>(word) / 4294967296.0 < probability;
}

// RE 0xB3AE0, slot 5. The nesting is done by the INNER nester at +0x18, and the two draws decide whether the result is kept and scored.
Solution FilterNester::run(SolveContext& ctx) {
    if (!inner_) {
        return Solution{};
    }
    Solution nested = inner_->run(ctx);

    // RE 0xB3B47: a probability out of the options block, which the beam parameters carry the recovered name for
    if (!draw(ctx.beam.frequencyRatio)) {
        return nested;
    }
    // RE 0xB3B62 and 0xB3B6A: a second probability eight bytes along, fed to a shared 1599 byte routine that returns a double
    if (draw(ctx.beam.frequencyRatioSecondary)) {
        nested.filterScore = filterScore(ctx, rng_);
    }
    return nested;
}

// RE 0x97A090, 1599 bytes, SEVENTEEN callers: it takes the generator and a double and produces a double. A free function, because other
// nesters reach it too and a member would claim it as this class's own.
double filterScore(const SolveContext& ctx, Mt19937& rng) {
    if (rng.index >= Mt19937::kStateSize) {
        rng.index = 0;
    }
    const double unit = static_cast<double>(rng.state[rng.index++]) / 4294967296.0;
    return unit * ctx.beam.frequencyRatio;
}

}  // namespace lcns
