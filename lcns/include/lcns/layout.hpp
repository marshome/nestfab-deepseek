// include/lcns/layout.hpp -- record layout facts read off the binary (goal rounds 141-157).
//
// Every constant here is either the immediate of an instruction (with its address) or the result of a
// numeric experiment over the compiler's magic-multiply sequence. Nothing is inferred from names.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

// --- strides -------------------------------------------------------------------------------------
// RE 0x1A90BB `add rbx,0xF0` (inside 0x1A9060) and RE 0x1B3943 `add rdx,0xF0` (inside 0x1B33B0): the same
// 240-byte record is walked in both places, so the two functions share one record type.
inline constexpr std::size_t kRunRecordStride = 0xF0;        // 240

// RE 0x1F8327 `add rdx,0x158` (inside 0x1F8300) and RE 0x1B53D9 `add r12,0x158` (inside 0x1B33B0).
inline constexpr std::size_t kTimingRecordStride = 0x158;    // 344

// RE 0x1AA8B1..0x1AA8B8: `sub rdx,rcx ; sar rdx,4 ; imul rdx,0xAAAAAAAAAAAAAAAB`. Round 157's experiment
// emulated that sequence and matched TRUNCATING division by 24 over 23 samples including negatives, so the
// container 0x1AA890 bounds-checks holds 24-byte records. The `sar 4` is a separate scaling step and is NOT
// folded into this number.
inline constexpr std::size_t kSmallRecordStride = 24;

// --- field offsets -------------------------------------------------------------------------------
// RE 0x1B3940 `add ecx,[rdx+0x4C]` (summed across the 0xF0 records) and RE 0x1CCA/0x1CD8 (the thread
// shutdown pair compares this same field against 9 and 10).
inline constexpr std::size_t kCounterOffset = 0x4C;

// RE 0x1F8320 `mov rax,[rdx+0x140]` and RE 0x1F832E `sub rax,[rdx-0x20]`: the per-record difference that
// 0x1F8300 accumulates. The second is addressed relative to the NEXT record, hence -0x20 from that base.
inline constexpr std::size_t kLeadingCountOffset = 0x140;
inline constexpr std::size_t kTrailingCountOffset = 0x20;

// RE 0x1AA8BC `mov r8d,[rsi+0x28]` -- the bound that the 24-byte-stride count is compared against.
inline constexpr std::size_t kSmallRecordLimitOffset = 0x28;

// RE 0x1AA8C5 `mov eax,[rsi+0x18] ; lea rbx,[rax+rax*2]` -- a field used three times over.
inline constexpr std::size_t kTripledFieldOffset = 0x18;

// --- the two-step divisions, kept as two steps ---------------------------------------------------
// RE 0x1F832E..0x1F8336: (a - b) >> 3 then /10. Round 157 confirmed the divisor 10 by experiment.
inline constexpr int kCountShift = 3;                        // right shift, /8
inline constexpr int kCountDivisor = 10;                     // confirmed by experiment (round 157)

// RE 0x1AA8B1..0x1AA8B8: span >> 4 then /24. Round 157 confirmed the divisor 24 by experiment.
inline constexpr int kSmallSpanShift = 4;                    // right shift, /16
inline constexpr int kSmallSpanDivisor = 24;                 // confirmed by experiment (round 157)

// The net effect of the two steps, written out rather than folded silently into one constant.
inline constexpr int kCountNetDivisor = (1 << kCountShift) * kCountDivisor;            // 80
inline constexpr int kSmallSpanNetDivisor = (1 << kSmallSpanShift) * kSmallSpanDivisor; // 384

}  // namespace lcns
