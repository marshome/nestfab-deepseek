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


// --- confirmed in round 159 ----------------------------------------------------------------------
// RE 0x1AA8C5 `mov eax,[rsi+0x18]` ; 0x1AA8C8 `lea rbx,[rax+rax*2]` ; 0x1AA8CC `shl rbx,4`:
// the indexed records are field*48 bytes apart. That is a THIRD stride, distinct from kRunRecordStride
// (240), kTimingRecordStride (344) and the /24 count of round 157; all four are kept side by side rather
// than one being made to overwrite another.
inline constexpr std::size_t kIndexedRecordStride = 48;

// RE 0x1AA8FB..0x1AA910: the record copied into the container has a dword at +0x18, a qword at +0x20 and a
// byte at +0x28 -- and round 155 read the same three fields being ASSEMBLED ON THE STACK at [rsp+0x748],
// [rsp+0x750], [rsp+0x758] before being passed on. Two independent functions, one layout.
inline constexpr std::size_t kRecordValueOffset = 0x18;   // dword
inline constexpr std::size_t kRecordWideOffset = 0x20;    // qword
inline constexpr std::size_t kRecordFlagOffset = 0x28;    // byte

// RE 0x6D6510 carries the assertion text '!m_elements.empty()', which names the container this insert
// helper works on: m_elements.
inline constexpr const char* kElementsContainerAssert = "!m_elements.empty()";   // RE 0x6D6510


// --- the search tree of 0x89D2F0 (round 178) ------------------------------------------------------
// Read from its entry: the root lives at [rcx+8]; each node links left at +0x10, right at +0x18 and carries its
// key at +0x20; insertion allocates 0x98 bytes and zeroes or sentinels the new node:
//     89D360  mov ecx,0x98 ; call 0x998500                        ; 152 bytes
//     89D38F  [rsi+0x40] = 0.0, [rsi+0x48] = 0.0, [rsi+0x50] = 0.0
//     89D3B9  [rsi+0x60] = -1, [rsi+0x68] = -1, [rsi+0x70] = -1     ; "no index"
//     89D3C5  movsd [rsi+0x78], [-1.0]                             ; from rva 0x9DFBD8
//     89D3CA  [rsi+0x80] = 0, [rsi+0x88] = 0, [rsi+0x90] = 0
inline constexpr std::size_t kTreeNodeBytes = 0x98;      // RE 0x89D360: 152
inline constexpr std::size_t kTreeNodeLeft = 0x10;       // RE 0x89D33D
inline constexpr std::size_t kTreeNodeRight = 0x18;      // RE 0x89D323
inline constexpr std::size_t kTreeNodeKey = 0x20;        // RE 0x89D32C
inline constexpr std::size_t kTreeNodeFirstDouble = 0x40;   // RE 0x89D38F
inline constexpr std::size_t kTreeNodeFirstSentinel = 0x60;  // RE 0x89D3B9
inline constexpr std::size_t kTreeNodeSentinelDouble = 0x78; // RE 0x89D3C5
inline constexpr std::size_t kTreeNodeTail = 0x80;          // RE 0x89D3CA
inline constexpr std::int64_t kTreeNodeNoIndex = -1;        // RE 0x89D3B2/0x89D3B9


// --- the size gate of 0x5E78D0 (round 179) --------------------------------------------------------
// RE 0x5E7936/0x5E7939: the container's byte span is compared with 0x2F (47) and the routine returns
// immediately unless the span EXCEEDS it. The threshold is "more than 47 bytes", and its meaning depends on the
// record: for 48-byte records (round 159's stride) it means "at least one", while in 0x70C810 -- which reads the
// same threshold at 0x70C832 over a container of 16-byte POINTS -- it means "at least three" (3 * 16 = 48).
// Both readings are recorded; round 189's cross-assertion tying 47+1 to the 48-byte stride was removed because
// the same literal serves more than one record type.
inline constexpr std::size_t kMinSpanForOneRecord = 47;   // RE 0x5E7939: cmp rbx,0x2F

inline bool hasAtLeastOneRecord(std::size_t spanBytes) {
    return spanBytes > kMinSpanForOneRecord;              // RE the `ja` at 0x5E7939
}


// --- the 16-byte container of 0x6DE940 (round 180) ------------------------------------------------
// RE 0x6DE94E/0x6DE95A/0x6DE960: the byte span is shifted right by four, so the element count of that
// container follows a 16-byte record. That is a FIFTH stride beside 48 (round 159), 240 (round 141),
// 344 (round 156) and the /24 count (round 157); each keeps its own evidence and none overwrites another.
inline constexpr std::size_t kSizeRecordStride = 16;      // RE 0x6DE960: sar rax,4
inline constexpr int kSizeRecordShift = 4;                // RE 0x6DE960

inline std::int64_t elementCount16(std::size_t spanBytes) {
    return static_cast<std::int64_t>(spanBytes) >> kSizeRecordShift;   // RE the shift itself
}

// --- the sentinel convention, seen in two independent constructors (round 180) ---------------------
// 0x5E6360 tail:  [rax+0x28], [rax+0x30], [rax+0x38] = 0xFFFFFFFFFFFFFFFF ; movsd [rax+0x40], [-1.0]
// 0x89D2F0     :  [rsi+0x60], [rsi+0x68], [rsi+0x70] = -1               ; movsd [rsi+0x78], [-1.0]
inline constexpr int kSentinelCount = 3;                  // RE both sites: three qwords
inline constexpr std::int64_t kInvalidIndexSentinel = -1; // RE the all-ones word
inline constexpr double kInvalidDoubleSentinel = -1.0;    // RE 0x5E6400 and 0x89D3C5


// --- the 4-byte accessors of the geometry chain (round 191) ----------------------------------------
//     0x5C61D0  mov rax,rcx ; ret          67 callers     -> identity
//     0x5C5260  mov rax,rcx ; ret          81 callers     -> identity
//     0x5C5F30  mov rax,rcx ; ret         103 callers     -> identity
//     0x5C5270  mov rax,rcx ; ret          23 callers     -> identity
//     0x5C5F40  lea rax,[rcx+0x18] ; ret    81 callers     -> a FIELD getter
// The identity ones are inline member accessors the compiler kept as distinct symbols; when reading the
// geometry functions their calls can be treated as no-ops, which is what makes that disassembly tractable.
inline constexpr int kIdentityAccessorCount = 4;      // RE the four `mov rax,rcx ; ret` sites
inline constexpr std::size_t kGetterFieldOffset = 0x18;   // RE 0x5C5F44, 81 callers


// --- the gate family is "at least k points" (round 196) -------------------------------------------
// Three sites, one pattern:
//     0x5E37B5  cmp rsi,0x1f   ; 31 = 2*16 - 1   -> more than 31 bytes means at least TWO points
//     0x5E7939  cmp rbx,0x2f   ; 47 = 3*16 - 1   -> at least THREE points (rounds 179/190)
// and 0x70C832 repeats the 0x2f form. Since one point is 16 bytes (round 189), the family's meaning is
// "more than k * 16 - 1 bytes", i.e. "at least k points" -- not "one 48-byte record", which was only one reading
// of the 47.
inline constexpr std::size_t kTwoPointSpan = 2 * 16 - 1;     // RE 0x5E37B5: 31
inline constexpr std::size_t kThreePointSpan = 3 * 16 - 1;   // RE 0x5E7939 / 0x70C832: 47

// RE 0x5E37B5 and 0x5E37C2: a container holds a point per 16 bytes.
inline std::size_t pointsInSpan(std::size_t spanBytes) { return spanBytes / 16; }

inline bool hasAtLeastPoints(std::size_t spanBytes, std::size_t wanted) {
    return pointsInSpan(spanBytes) >= wanted;                // RE the `ja`/`jbe` after each comparison
}

// --- the text serialiser's delimiter (round 196) ---------------------------------------------------
// RE 0x5E37CB: the eight bytes loaded there are 2C 00 50 4F 4C 59 47 4F -- a comma, a NUL, then "POLYGO..." --
// so a comma delimiter precedes the word POLYGON. 0x5E3760 passes it to 0x9920C0 and then calls 0x70C480.
inline constexpr char kPolygonDelimiter = ',';


// --- the five-qword record of 0x734620 (round 197) --------------------------------------------------
//     734634 mov rax,[rdx]       ; +0x00     73463c mov rax,[rdx+8]    ; +0x08
//     73465d mov rax,[rdx+0x10]  ; +0x10     73466b mov rax,[rdx+0x18] ; +0x18
//     734674 mov rax,[rdx+0x20]  ; +0x20
// Five qwords copied by value, and +0x20 is the offset the search tree of round 178 keys on, so this record
// carries a key at the end of its five words.
inline constexpr int kFiveFieldRecord = 5;
inline constexpr std::size_t kRecordWord5Offset = 0x20;         // RE 0x734674
inline constexpr std::size_t kFiveFieldRecordBytes = 5 * 8;     // 40

// --- the stream fallback seen in the library operator (round 197) ----------------------------------
// RE 0x9920F8/0x9920FB: `mov edx,[rcx+0x20] ; or edx,1` -- the setstate bit the C-string insertion sets on the
// null path. 0x9920C0 is libstdc++'s operator<< for a C string, registered as toolchain in covlib.
inline constexpr int kOstreamSetstateBit = 1;


// --- the four-double object is a rectangle (round 200) ---------------------------------------------
// RE 0x5E5DD0: it loads [rcx+8], [rcx+0x10], [rcx+0x18] and [rcx+0x20] -- the four doubles round 177 recorded --
// and then selects one by index:
//     5E5E1C and edx,3      ; modulo FOUR
//     5E5E35 shl rdx,4      ; times SIXTEEN, one point
//     5E5E3E/5E5E42         ; read that point's two doubles
//     5E5E47/5E5E4F         ; write them through r9
// The four fields are EIGHT bytes apart (0x20 - 0x08 = 24 = 3 * 8), i.e. four consecutive doubles = two points
// (x1,y1,x2,y2). The routine loads them as two xmm pairs and builds a four-point stack array with `shufpd` and
// `movhpd` (0x5E5E23/0x5E5E28), and only then indexes that array with `and edx,3 ; shl rdx,4`. So the four corners
// are DERIVED from the two opposite corners by permutation -- the standard rectangle corner accessor -- and the
// earlier wording here, which called the fields themselves four points, was wrong and is withdrawn.
inline constexpr int kBoxCornerCount = 4;                 // RE 0x5E5E1C
inline constexpr std::size_t kBoxCornerBytes = 16;        // RE 0x5E5E35

inline std::size_t cornerIndex(std::size_t i) { return i & (kBoxCornerCount - 1); }   // RE the `and edx,3`

// --- the 504-byte block of 0x5E5EE0 (round 200) -----------------------------------------------------
//     5E5F06 mov ecx,0x1F8 ; 5E5F12 call 0x998500      ; the allocation
//     5E5F17 lea rdx,[rax+0x1F8]                       ; the end of the block
//     5E5F21..5E5F3D store the block and its end at +0x28,+0x18,+0x20,+0x48,+0x38,+0x40,+0x10,+0x30
inline constexpr std::size_t kContainerBlockBytes = 0x1F8;   // RE 0x5E5F06: 504
inline constexpr std::size_t kContainerFieldLow = 0x10;      // RE 0x5E5F39
inline constexpr std::size_t kContainerFieldHigh = 0x48;     // RE 0x5E5F2D


// --- the large object of 0x5E6200 (round 201) -------------------------------------------------------
// RE the fields that function touches: +0x10, +0x20, +0x28, +0x30, +0xB8, +0xBD, +0x150, +0x155, +0x158.
// Two pairs sit five bytes apart, so each is a byte field followed by something five bytes later:
inline constexpr std::size_t kLargeObjectByteFieldA = 0xB8;    // RE 0x5E6200
inline constexpr std::size_t kLargeObjectByteFieldB = 0xBD;    // RE 0x5E6200
inline constexpr std::size_t kLargeObjectFieldA = 0x150;       // RE 0x5E6200
inline constexpr std::size_t kLargeObjectFieldB = 0x155;       // RE 0x5E6200
inline constexpr std::size_t kLargeObjectLastField = 0x158;    // RE 0x5E6200
inline constexpr std::size_t kLargeObjectSpacing = 5;          // RE 0xBD-0xB8 and 0x155-0x150
inline constexpr std::size_t kLargeObjectMinBytes = 0x159;     // one past the highest field touched

// --- the container fields of 0x5E5CD0 (round 201) ---------------------------------------------------
// RE the offsets it touches while allocating: +0x8, +0x10, +0x18, +0x20, +0x28, +0x30, +0x38, +0x40.
inline constexpr std::size_t kContainerLastField = 0x40;       // RE 0x5E5CD0
inline constexpr int kContainerFieldStep = 8;                  // the fields are eight bytes apart

}  // namespace lcns
