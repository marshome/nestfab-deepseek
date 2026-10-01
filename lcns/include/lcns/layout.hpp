// include/lcns/layout.hpp -- record layout facts read off the binary (goal rounds 141-157).
//
// Every constant here is either the immediate of an instruction (with its address) or the result of a
// numeric experiment over the compiler's magic-multiply sequence. Nothing is inferred from names.
#pragma once

#include "lcns/recovery.hpp"

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


// --- two strides appearing in one body (round 203) --------------------------------------------------
// RE 0x72B6A0, which computes both element addresses:
//     72B6B9 lea rcx,[rsi+rsi*2] ; 72B6BD shl rcx,4              ; rsi * 48  (0x30)
//     72B6CE lea rdx,[rbx+rbx*2] ; 72B6D5 lea rax,[rax+rdx*8]     ; rbx * 24  (0x18)
// so the 48-byte stride of round 159 and the 24-byte stride of round 157 are exercised by the same routine.
inline constexpr int kNestedStrideCheck = 2;   // the two strides seen together at 0x72B6A0

// RE 0x704400 (the division shape round 183 established, here a ONE-operand imul):
//     704435 movabs rdx,0xC30C30C30C30C30D ; 704442 imul rdx ; 70444F sar rdx,4 ; 704453 sub rdx,rax
inline constexpr std::uint64_t kIndexDivMagic = 0xC30C30C30C30C30DULL;
inline constexpr int kIndexDivShift = 4;
inline constexpr int kIndexDivisor = 21;   // determined by experiment over 19 samples


// --- the blocked container of 0x704400: 21 elements of 24 bytes per block (round 205) ---------------
//     704420 cmp r8,0x14 ; 704424 ja 0x704430           ; the fast path applies while the index is <= 20
//     704426 lea rdx,[rdx+rdx*2] ; 70442A lea rax,[rax+rdx*8]   ; base + index*24
//     704442 imul rdx (0xC30C30C30C30C30D) ; 70444F sar rdx,4 ; 704453 sub rdx,rax   ; q = index / 21
//     70445A lea rcx,[rdx+rdx*4] ; 70445E lea rcx,[rdx+rcx*4]   ; q * 21
//     704462 sub r8,rcx                                          ; the remainder
//     704469 mov rax,[rax + rdx*8] ; 70446D lea rax,[rax + rcx*8] ; block[q] + remainder*24
// and 21 * 24 = 504, which is exactly kContainerBlockBytes from round 200 -- the two were found in different
// functions, so this is a cross-verification rather than a repetition.
inline constexpr std::size_t kBlockElements = 21;        // RE the `q * 21` at 0x70445A/0x70445E
inline constexpr std::size_t kBlockFastPathLimit = 0x14; // RE 0x704420: 20 = 21 - 1
inline constexpr std::size_t kBlockElementStride = 24;   // RE 0x70442A: rdx * 3 * 8
static_assert(kBlockElements * kBlockElementStride == kContainerBlockBytes,
              "21 elements of 24 bytes is the 504-byte block measured in round 200");
static_assert(kBlockFastPathLimit + 1 == kBlockElements, "the fast path covers the first block");


// --- the tree lookup of 0x924EA0 (round 212): a second sighting of the node layout ----------------
//     924ECC mov r9,[rcx+0x20] ; 924ED0 cmp r9,r11 ; 924ED5 setg ; 924EDE mov rax,[rcx+0x18]
//     924EC0 mov rax,[rcx+0x10]                       ; the other child
//     924F01 mov [rsi],rdi ; 924F04 mov [rsi+8],0      ; node at +0x00, flag at +0x08
// The offsets 0x10/0x18/0x20 are the same ones round 178 read out of 0x89D2F0, so the node layout now rests on two
// independent functions, and the two-word out parameter is the pair<iterator,bool> a find returns.
inline constexpr std::size_t kTreeLookupOutNode = 0x00;   // RE 0x924F01
inline constexpr std::size_t kTreeLookupOutFlag = 0x08;   // RE 0x924F04

// --- the push_back of 0x8C36F0 (round 212) -----------------------------------------------------------
//     8C36FF/8C3702/8C3706/8C3709 copy sixteen bytes; 8C370D advances the end by 0x10.
inline constexpr std::size_t kPushBackElementBytes = 0x10;   // RE 0x8C370D
// cross-checked at run time in tests/test_recovered.cpp, which sees compare.hpp as well


// --- the default state of the 48-byte record (round 214) --------------------------------------------
// RE 0x5CE310, which writes six consecutive doubles:
//     5CE327 [rcx+0x00] = -1.0    5CE32B [rcx+0x08] = -1.0    5CE330 [rcx+0x10] = 0.0
//     5CE335 [rcx+0x18] = -1.0    5CE33A [rcx+0x20] = 0.0     5CE33F [rcx+0x28] = 0.0
// Six doubles is 48 bytes, the indexed record stride measured in round 159, so this is that record's default
// state: -1 where an index or flag belongs, 0 where a value does.
inline constexpr int kRecord48Doubles = 6;
inline constexpr double kRecord48Defaults[kRecord48Doubles] = {-1.0, -1.0, 0.0, -1.0, 0.0, 0.0};

// --- the translate-and-invalidate of 0x136C50 (round 214) -------------------------------------------
// RE 0x136C60/0x136C65/0x136C69/0x136C6D: each 16-byte element's second double gets xmm1 added.
inline constexpr std::size_t kTranslateFieldOffset = 0x08;   // RE 0x136C60
inline constexpr std::size_t kTranslateStride = 0x10;        // RE 0x136C65
// RE 0x136C77/0x136C7F: -1.0 written at +0x50 after the walk, i.e. the result marked invalid.
inline constexpr std::size_t kTranslateInvalidate = 0x50;
inline constexpr double kTranslateInvalidValue = -1.0;

// --- the ninety degree literal of 0x5C3D30 (round 214) -----------------------------------------------
// RE 0x5C3D35: movsd xmm2,[90.0] at rva 0x9DE7C0, passed to 0x5C3820. The literal is landed; the callee's meaning
// is not claimed here.
inline constexpr double kDefaultAngleDegrees = 90.0;


// --- the epsilon-gated orientation test of 0x24B790 (round 215) --------------------------------------
// RE 0x24B7CB: the literal 0.001 at rva 0x9C2930, compared with the magnitude of a determinant formed by
//     24B7A5/24B7A9/24B7AD   (third - first) * (fourth - second)
//     24B7B6/24B7C3/24B7C7   (another difference) * (another difference)
//     24B7D3 sub             the difference of the two products
//     24B7DB andpd           the sign mask -> magnitude
//     24B7E7 ja              inside the band -> the function returns zero
//     24B7ED/24B7F1 seta     otherwise the sign decides
// so this is an orientation predicate with a tolerance below which the figure is treated as degenerate.
inline constexpr double kOrientationEpsilon = 0.001;    // RE 0x24B7CB (rva 0x9C2930)
inline constexpr int kOrientationFieldCount = 4;        // RE the four fields read: +0x00,+0x08,+0x10,+0x18,+0x20,+0x28

// --- the tolerance'd dominance test of 0x5436C0 (round 215) ------------------------------------------
//     5436C8/5436CB  the count of eight byte elements
//     5436E5 addsd   first[i] + 0.0001
//     5436EE ucomisd ; 5436F2 ja -> 1     second[i] exceeds that -> a violation, reported immediately
inline constexpr double kArrayCompareEpsilon = 0.0001;  // RE 0x5436D8 (rva 0x9DBF88)
inline constexpr std::size_t kArrayCompareStride = 8;   // RE 0x5436CB: sar rcx,3

// --- the constructor fields of 0x21F9F0 (round 215) --------------------------------------------------
//     21FA27 byte [rbx+0x140] = sil      ; a byte flag
//     21FA2E qword [rbx+0x138] = 0       ; a zeroed word just before it
//     21FA15 [rcx+8] = 1.0              ; RE rva 0x9C1BF0
inline constexpr std::size_t kCtorFlagByteOffset = 0x140;    // RE 0x21FA27
inline constexpr std::size_t kCtorZeroQwordOffset = 0x138;   // RE 0x21FA2E
inline constexpr double kCtorDoubleDefault = 1.0;            // RE 0x21FA15


// --- the ratio comparator of 0x7DB6E0 (round 216) ---------------------------------------------------
// RE the key words it walks first: +0x00 (0x7DB6E3), +0x18 (0x7DB6F4), +0x10 (0x7DB6FE), +0x08 (0x7DB708).
// Then, with xmm1 = [rcx+0x38] and xmm2 = [rdx+0x38]:
//     7DB718 movsd xmm3,[50.0]      ; rva 0x9DFC20, the shared literal block of round 172
//     7DB728 andpd xmm0,<sign mask> ; |xmm1 - xmm2|
//     7DB730 ucomisd xmm3,xmm0 ; jbe -> the direct comparison at 7DB752
//     7DB736 mulsd [rcx+0x28],[rdx+0x30] ; 7DB73B mulsd [rdx+0x28],[rcx+0x30]
//     7DB74A ucomisd xmm1,xmm0 ; seta al   ; the two ratios compared as a cross product
// so equal keys are ordered by the primary field when it differs by at least the margin, and by the ratio of
// (+0x28 / +0x30) when it does not.
inline constexpr double kRatioCompareMargin = 50.0;        // RE 0x7DB718 (rva 0x9DFC20)
inline constexpr std::size_t kRatioNumeratorOffset = 0x28; // RE 0x7DB736
inline constexpr std::size_t kRatioDenominatorOffset = 0x30;
inline constexpr std::size_t kRatioPrimaryOffset = 0x38;   // RE 0x7DB70E
inline constexpr int kComparatorKeyWords = 4;              // RE the four comparisons at +0x00/+0x18/+0x10/+0x08

// --- the scaled sum of 0x525760 (round 216) ----------------------------------------------------------
//     525767 movsd xmm1,[0.95] (rva 0x9DBC10) ; 5257B4 call 0x5253E0 ; 5257B9/5257BF add the two results
inline constexpr double kScale095 = 0.95;                  // RE 0x525767
inline constexpr int kScaledSumTerms = 2;                  // RE 0x5257BF

// --- the 512-byte block indexing of 0x5522B0 (round 216) ---------------------------------------------
//     5522E3 cmp rcx,0x1ff ; jbe          ; more than 511 bytes needs block indexing
//     5522F5 sar rdx,9 ; 55230E shl r8,9  ; divide and multiply by 512
//     552307/552315 [rdx + rax*8]         ; the block table
//     552337 movsd xmm0,[10.0] (rva 0x9DC228) ; 552344 mulsd xmm0,[rdx + rax*8] ; 552351 ucomisd ; seta
inline constexpr std::size_t kDequeBlockSize = 0x200;      // 512
inline constexpr std::size_t kDequeBlockMask = 0x1FF;      // RE 0x5522E3
inline constexpr int kDequeBlockShift = 9;                 // RE 0x5522F5 / 0x55230E
inline constexpr double kTenfoldFactor = 10.0;             // RE 0x552337 (rva 0x9DC228)


// --- the tiling cancellation guard of 0x7D3530 (round 217) ------------------------------------------
//     7D353B movzx edx,byte [rcx+0x10] ; 7D3541 je      ; the flag at +0x10 means "already stopped"
//     7D3554 call 0x2FC90                               ; a progress value
//     7D355D ucomisd xmm0,[0.75] (rva 0x9AF938) ; 7D3565 jbe
//     7D3581 lea rdx,[rip+...] 'Tiling time cancelled !'
//     7D35B8 byte [rbx+0x10] = 1 ; 7D35BC mfence        ; set under a fence, so other threads see it
//     7D35CA eax = ([rbx+0x10] != 0)
inline constexpr double kTilingCancelThreshold = 0.75;    // RE 0x7D355D (rva 0x9AF938)
inline constexpr std::size_t kCancelFlagOffset = 0x10;    // RE 0x7D353B and 0x7D35B8
inline constexpr std::size_t kCancelOuterFlagOffset = 0x348;   // RE 0x7D356C

// --- the negated box centre of 0x1DD870 (round 217) --------------------------------------------------
//     1DD8A3/1DD8B0 and 1DD8B5/1DD8BA sum the box's coordinate pairs; 1DD8BF loads 0.5 (rva 0x9C0590);
//     1DD8C7/1DD8CB multiply by it; 1DD905/1DD90F xor with a sign mask, i.e. negate.
inline constexpr double kBoxCentreHalf = 0.5;             // RE 0x1DD8BF
inline constexpr std::uint64_t kSignFlipMask = 0x8000000000000000ULL;   // RE 0x1DD905/0x1DD90F (xorpd)
inline constexpr std::size_t kBoxCentreFromBoxFieldA = 0x08;   // RE 0x1DD8A3 (compare.hpp names it kObjectFieldA)
inline constexpr std::size_t kBoxCentreFromBoxFieldC = 0x18;   // RE 0x1DD8B0 (compare.hpp names it kObjectFieldC)


// --- the 120-byte scan of 0x4B8220 (round 218) ------------------------------------------------------
//     4B82A3 add rbx,0x78        ; a 120-byte record -- a stride not recorded before
//     4B828F movsd xmm6,[0.01]   ; rva 0x9D9360
//     4B82C7 call 0x5C8F30       ; with xmm3 = that literal and r8d = 1
inline constexpr std::size_t kScanStride120 = 0x78;        // RE 0x4B82A3
inline constexpr double kScanTolerance = 0.01;             // RE 0x4B828F (rva 0x9D9360)
inline constexpr int kScanFlag = 1;                        // RE 0x4B82C1

// --- the element comparison of 0x99F470 (round 218) --------------------------------------------------
//     99F4CE imul rcx,rcx,0x30   ; 48 bytes per element, multiplied directly
//     99F4C6 movsd xmm2,[0.001]  ; rva 0x9DBD80
inline constexpr std::size_t kRecord48Mul = 0x30;          // RE 0x99F4CE
inline constexpr double kElementCompareTolerance = 0.001;  // RE 0x99F4C6 (rva 0x9DBD80)

// --- the 32-bit saturation limits (round 218) --------------------------------------------------------
//     62FCB0 loads 2.14748e9 (rva 0xA067E8) and -2.14748e9 (rva 0xA067E0) alongside 0.5 and 1
//     5FCA80 loads 4.29497e9 (rva 0x9E1488)
inline constexpr double kInt32MaxExact = 2147483647.0;       // RE rva 0xA067E8
inline constexpr double kUint32MaxExact = 4294967295.0;      // RE rva 0x9E1488
inline constexpr std::size_t kSaturationHalves = 2;         // RE 0x62FCB0: 0.5 and 1 accompany the limits


// --- the cancel threshold's tiers (round 219) -------------------------------------------------------
// RE 0x7D34DE/0x7D34E6/0x7D34EB: the kind comes back in eax, `cmp eax,3 ; jbe` keeps 0.5 and anything larger takes
// 0.3; round 217 recorded 0.75 at 0x7D355D. The family therefore has three tiers, and which one applies depends
// on the kind and on the call site.
inline constexpr double kCancelTierLow = 0.3;        // RE 0x7D34EB (rva 0x9AF930)
inline constexpr double kCancelTierMid = 0.5;        // RE 0x7D34DE (rva 0x9AF928)
inline constexpr double kCancelTierHigh = 0.75;      // RE 0x7D355D (rva 0x9AF938), round 217
inline constexpr int kCancelKindBoundary = 3;        // RE 0x7D34E6
inline constexpr int kCancelKindDefault = 2;         // RE 0x7D34F7's result is inverted at 0x7D351F

// --- the initialiser fields of 0x1A60B0 (round 219) -------------------------------------------------
//     1A60E7 movsd xmm1,[0.06]      ; rva 0x9BEBB0, handed to 0x4D5060
//     1A6119 dword [rbx+0x138] = 1  ; the same +0x138 round 215's constructor zeroes
//     1A613D/1A6145 the pair (0, 0x14) written to [rsp+0x40]/[rsp+0x44]
//     1A6157 lea rax,[rax+rax*2]    ; times three, with a scale of eight -> 24-byte entries
//     1A6162 [rbx+0x58] = the table entry
inline constexpr double kInitConstant006 = 0.06;      // RE 0x1A60E7 (rva 0x9BEBB0)
inline constexpr std::size_t kInitWord138 = 0x138;    // RE 0x1A6119, cross-checked with kCtorZeroQwordOffset
inline constexpr std::size_t kInitField58 = 0x58;     // RE 0x1A6162
inline constexpr int kInitPairFirst = 0;              // RE 0x1A613D
inline constexpr int kInitPairSecond = 0x14;          // RE 0x1A6145: 20
inline constexpr std::size_t kInitEntryStride = 24;   // RE 0x1A615B: rax*3 scaled by 8

// --- two DEFAULT method stubs, not type anchors (round 219, corrected in round 223) --------------------
// RE 0x7C68E5 `lea r8,[rip-0x448C]` and 0x7C6904 `lea r8,[rip-0x449B]`: 0x7C68E5 + 7 - 0x448C = 0x7C2460 and
// 0x7C6904 + 7 - 0x449B = 0x7C2470. Round 219 called these "type anchors" and round 221 repeated it; reading the
// bytes at those addresses settles the matter:
//     0x7C2460: 31 C0 C3 90 90 90 90 90   =   xor eax,eax ; ret ; nops
//     0x7C2470: 31 C0 C3 90 90 90 90 90   =   the same tiny stub
// They are CODE in .text, so they are not vtables or typeinfo. What the comparisons test is whether an object's
// function pointer at +0x10 / +0x18 is STILL the default stub, i.e. whether a callback has been overridden. The
// offsets landed in round 221 keep their meaning; only the naming and the "type" claim are withdrawn.
inline constexpr std::uintptr_t kDefaultStubA = 0x7C2460;   // RE 0x7C68E5
inline constexpr std::uintptr_t kDefaultStubB = 0x7C2470;   // RE 0x7C6904
inline constexpr std::uintptr_t kDefaultStubGap = 0x10;     // the stubs are one object apart
inline constexpr std::uint64_t kDefaultStubEncoding = 0x9090909090C3C031ULL;   // `xor eax,eax ; ret` + nops


// --- the hash table of 0x1C65B0 (round 220) ---------------------------------------------------------
//     1C667E mov eax,[rax+0x48]                            ; the 32 bit hash
//     1C668B and ebx,0x7F                                  ; the bucket is hash modulo 128
//     1C669B sar edx,7                                     ; and hash / 128 indexes the bucket array
//     1C66A7 lea rcx,[rax+rdx*8]  (rdx = bucket * 3)        ; 24 bytes per entry
//     1C66AF cmp rax,[rcx+0x10]                            ; the chain continues at +0x10
//     1C6658 lock add dword [rdx+8],1                       ; an atomic reference count at +8
// Both the modulo and the quotient look the way they do because the hash is signed, so the four instructions
// around them are the sign correction; the test below reproduces the whole sequence.
inline constexpr std::size_t kHashFieldOffset = 0x48;      // RE 0x1C667E
inline constexpr int kBucketCount = 128;                   // RE 0x1C668B (`and 0x7F`) and 0x1C669B (`sar 7`)
inline constexpr int kBucketShift = 7;                     // RE 0x1C669B
inline constexpr std::size_t kBucketEntryStride = 24;      // RE 0x1C66A7 (bucket * 3 scaled by 8)
inline constexpr std::size_t kBucketChainOffset = 0x10;    // RE 0x1C66AF
inline constexpr std::size_t kRefCountOffset = 0x08;       // RE 0x1C6658: the `lock add` target
static_assert((1 << kBucketShift) == kBucketCount, "the shift and the bucket count agree");
static_assert(kBucketEntryStride == kSmallRecordStride, "the entries are the 24-byte records of round 157");


// --- the adaptive time budget guard of 0x65C0F0 (round 221) -----------------------------------------
//     65C11A/65C131 the retry counter lives at +0xC and its limit at +8
//     65C1F3 ucomisd xmm0,[rbx]        ; the budget itself is a double at +0x00
//     65C198 movsd xmm2,[1000.0]       ; rva 0x9BF510, the milliseconds divisor
//     65C1A8 addsd xmm1,[2.0]          ; rva 0x9BF518, the retry term added to the count
//     65C1D0 divsd xmm0,xmm2           ; elapsed milliseconds / 1000
//     65C1DE divsd xmm0,xmm1           ; / (count + 2)
//     65C1EF addsd                     ; plus the earlier interval
// and the elapsed time comes from the nanosecond clock 0x8A8190, with the /1e6 magic of round 148
// (0x431BDE82D7B634DB with `sar rdx,0x12`) -- so this function cross-verifies both.
inline constexpr std::size_t kGuardBudgetOffset = 0x00;    // RE 0x65C1F3
inline constexpr std::size_t kGuardLimitOffset = 0x08;     // RE 0x65C134
inline constexpr std::size_t kGuardCountOffset = 0x0C;     // RE 0x65C11A and 0x65C137
inline constexpr double kGuardDivisorMs = 1000.0;          // RE 0x65C198 (rva 0x9BF510)
inline constexpr double kGuardRetryTerm = 2.0;             // RE 0x65C1A8 (rva 0x9BF518)

// --- the vtable slots the guard tests against the two anchors (round 221) -----------------------------
//     65C10D mov rax,[rdx+0x10] ; 65C111 cmp rax,r8   with r8 = 0x7C2460
//     65C121 mov rdx,[rdx+0x18] ; 65C12C cmp rdx,r8   with r8 = 0x7C2470
inline constexpr std::size_t kGuardTypeSlotA = 0x10;       // RE 0x65C10D
inline constexpr std::size_t kGuardTypeSlotB = 0x18;       // RE 0x65C121


// --- the time-of-hour wraparound of 0x5C2200 (round 224) ---------------------------------------------
//     5C2273 movabs rdx,0x34630B8A000     ; 3,600,000,000,000 -- one hour in nanoseconds
//     5C2290 add rax,rdx ; js             ; negatives wrap upward
//     5C22AA movabs rdx,0x34630B89FFF     ; one less, the upper bound
//     5C22B4 cmp rax,rdx ; jle            ; values above it wrap downward
//     5C2262 addsd [0.5] (rva 0x9DE750)   ; the rounding term added before the second round helper
//     5C2220 movsd xmm7,[360.0] (rva 0x9DE748)
inline constexpr std::uint64_t kNanosecondsPerHour = 3600000000000ULL;      // RE 0x5C2273
inline constexpr std::uint64_t kNanosecondsPerHourMax = 3599999999999ULL;  // RE 0x5C22AA
inline constexpr double kHourRoundTerm = 0.5;                             // RE 0x5C2262
inline constexpr double kDegreesFullTurn = 360.0;                         // RE 0x5C2220
static_assert(kNanosecondsPerHour == 3600ULL * 1000000000ULL, "one hour in nanoseconds");
static_assert(kNanosecondsPerHourMax == kNanosecondsPerHour - 1ULL, "one less than the hour");

// --- the steps constructor of 0x1BF1A0 (round 224) ---------------------------------------------------
//     1BF1E1/1BF1E8 [rbx] = [rbx+8] = 0
//     1BF1C0/1BF1C5/1BF1CA the three doubles at +0x10/+0x18/+0x20 start at zero
//     1BF1D2 dword [rbx+0x28] = 1
//     1BF1D9 [rbx+0x30] = 0
//     1BF23A [rbx] = the truncated steps figure
//     1BF24D/1BF257 [rbx+0x10] = [rbx+0x18] = 1.0 (rva 0x9BF8B0) ; 1BF252 [rbx+0x20] = -1.0 (rva 0x9BF8E0)
inline constexpr std::size_t kStepsField0 = 0x00;        // RE 0x1BF23A
inline constexpr std::size_t kStepsField8 = 0x08;        // RE 0x1BF1E8
inline constexpr std::size_t kStepsDoubleA = 0x10;       // RE 0x1BF24D
inline constexpr std::size_t kStepsDoubleB = 0x18;       // RE 0x1BF257
inline constexpr std::size_t kStepsDoubleC = 0x20;       // RE 0x1BF252
inline constexpr std::size_t kStepsFlag28 = 0x28;        // RE 0x1BF1D2
inline constexpr std::size_t kStepsField30 = 0x30;       // RE 0x1BF1D9
inline constexpr double kStepsDefaultPlus = 1.0;         // RE 0x1BF23D
inline constexpr double kStepsDefaultMinus = -1.0;       // RE 0x1BF245


// --- the machine-kind preset table of 0x7F41C0 (round 225) -------------------------------------------
// RE 0x7F41DE onward: nine dwords written from one of three variants, chosen by the kind that 0x183F50 returns
// and compared with the literal 1.0 (rva 0x9BEAB0) then 2.0 (rva 0x9BEAE0).
//      kind 1: 0x14 0x14 0x64 0x0A 0x0A 0x32 0x14 0x14 0x14   = 20 20 100 10 10 50 20 20 20
//      kind 2: 0x28 0x14 0x64 0x14 0x0A 0x32 0x14 0x14 0x14   = 40 20 100 20 10 50 20 20 20
//      other : 0x64 0x14 0x64 0x32 0x0A 0x32 0x14 0x14 0x14   = 100 20 100 50 10 50 20 20 20
inline constexpr int kPresetCount = 9;
inline constexpr int kPresetKindOne[kPresetCount] = {20, 20, 100, 10, 10, 50, 20, 20, 20};
inline constexpr int kPresetKindTwo[kPresetCount] = {40, 20, 100, 20, 10, 50, 20, 20, 20};
inline constexpr int kPresetOther[kPresetCount] = {100, 20, 100, 50, 10, 50, 20, 20, 20};
inline constexpr int kPresetStride = 4;                  // RE the `mov dword [rbx+4*n]` forms
inline constexpr int kPresetKindOneValue = 1;            // RE 0x7F41D2: the literal at rva 0x9BEAB0
inline constexpr int kPresetKindTwoValue = 2;            // RE 0x7F422F: the literal at rva 0x9BEAE0

// --- the tolerance'd containment test of 0x14F5F0 (round 225) ----------------------------------------
//     14F5FB movsd xmm6,[1e-6] (rva 0x9BD1B0)
//     14F61E call 0x5C8F30                     ; the same predicate 0x4B8220 uses
//     14F623 cmp byte [rbx+0x28],0 ; je
//     14F63D/14F64C/14F650  compares [rsi+0x10] against the epsilon and against [rbx+0x38] - epsilon
//     14F668/14F685/14F6A9  the same shape for +0x20, +0x8 and +0x18
//     14F6C3/14F6C8/14F6CA  and/cmovne combine the four outcomes
inline constexpr double kContainTolerance = 1e-06;      // RE 0x14F5FB (rva 0x9BD1B0)
inline constexpr std::size_t kContainFlagOffset = 0x28; // RE 0x14F623
inline constexpr std::size_t kContainSizeOffset = 0x38; // RE 0x14F64C
inline constexpr int kContainCoordinateCount = 4;       // RE the four comparisons


// --- the 0x98-byte initialiser of 0x704260 (round 226) ----------------------------------------------
//     704264 movsd xmm1,[1.0] (rva 0x9DFBC8)
//     70428C [rcx+0x30] = 1.0    70429B [rcx+0x48] = 1.0
//     7042AE [rcx+0x68] = 1.0    7042BD [rcx+0x80] = 1.0
//     7042A5 byte [rcx+0x58] = 0 7042CD byte [rcx+0x90] = 0
//     70426C [rcx] = 0           704273/704278/70427D/704282/704287/704291/704296/7042A0/7042B3/7042B8/7042C5
//                                 all zero as doubles
// so the object is 0x98 bytes with four unit entries, separated by 0x18, 0x20 and 0x18 bytes, and two zeroed
// byte flags. That is the shape of a transform with four unit scale entries rather than a plain record.
inline constexpr std::size_t kCtor098Bytes = 0x98;
inline constexpr std::size_t kCtor098UnitA = 0x30;    // RE 0x70428C
inline constexpr std::size_t kCtor098UnitB = 0x48;    // RE 0x70429B
inline constexpr std::size_t kCtor098UnitC = 0x68;    // RE 0x7042AE
inline constexpr std::size_t kCtor098UnitD = 0x80;    // RE 0x7042BD
inline constexpr std::size_t kCtor098FlagA = 0x58;    // RE 0x7042A5, a byte
inline constexpr std::size_t kCtor098FlagB = 0x90;    // RE 0x7042CD, a byte
inline constexpr int kCtor098UnitCount = 4;

// --- the smaller initialiser of 0x2B3990 (round 226) --------------------------------------------------
//     2B39AC/2B39B0/2B39B5 zeros at +0x00, +0x08, +0x10 ; 2B39BA +0x28 zero
//     2B39C7/2B39CC the same constant double to +0x18 and +0x20
//     2B39D1 [rcx+0x30] = 1.0 (rva 0x9C6CC0)
//     2B39D6 movups [rcx+0x38], <sixteen bytes from a constant block>
//     2B39DA dword [rcx+0x48] = 0
inline constexpr std::size_t kCtor4CUnit = 0x30;         // RE 0x2B39D1
inline constexpr std::size_t kCtor4CBlock = 0x38;        // RE 0x2B39D6, sixteen bytes
inline constexpr std::size_t kCtor4CBlockBytes = 0x10;
inline constexpr std::size_t kCtor4CDword = 0x48;        // RE 0x2B39DA
inline constexpr std::size_t kCtor4CBytes = 0x4C;
inline constexpr std::size_t kCtor4CPairA = 0x18;        // RE 0x2B39C7
inline constexpr std::size_t kCtor4CPairB = 0x20;        // RE 0x2B39CC

// --- the shared unit literal (round 226) --------------------------------------------------------------
// RE the queue: 0x704260, 0x700250 and 0x72D7E0 all read the 1.0 at rva 0x9DFBC8, so the same pool entry feeds
// three different initialisers.
inline constexpr std::uintptr_t kSharedUnitRva = 0x9DFBC8;


// --- the second member of the ratio comparator family (round 227) ------------------------------------
// RE 0x724E40, which applies the same margin-then-ratio rule as 0x7DB6E0 of round 216 but on other fields:
//     724E68/724E6D  the pair whose absolute difference is compared with the margin: +0x50 and +0x88
//     724E8F/724E94  the cross multiplied pair: (+0x40 * +0x80) against (+0x78 * +0x48)
//     724E85 jbe     the margin test, as in round 216
//     724EA6 seta    the ratio test, as in round 216
//     724EB4 dword [rbx+0x10] = 6   ; the tag this member writes
//     724ED7 lea rax,[rax+rcx*8]    ; rdx * 7 * 8 = a 56-byte element stride
inline constexpr double kRatioFamilyMargin = 50.0;         // the same 50.0 as round 216 (rva 0x9DFC20)
inline constexpr std::size_t kRatioFamilyPrimaryA = 0x50;  // RE 0x724E68
inline constexpr std::size_t kRatioFamilyPrimaryB = 0x88;  // RE 0x724E6D
inline constexpr std::size_t kRatioFamilyNumA = 0x40;      // RE 0x724E8F
inline constexpr std::size_t kRatioFamilyDenA = 0x80;      // RE 0x724E8F
inline constexpr std::size_t kRatioFamilyNumB = 0x78;      // RE 0x724E94
inline constexpr std::size_t kRatioFamilyDenB = 0x48;      // RE 0x724E94
inline constexpr int kRatioFamilyTag = 6;                  // RE 0x724EB4 (the 0x724E40/0x725140 variant)
// RE 0x72D638 (round 243): 0x72D5B0 writes FIVE where the other two write six, and yet its constant, its
// primary pair (+0x50/+0x88), its ratio pair (+0x40/+0x78/+0x80/+0x48), its rule and its 56-byte stride are
// all identical to theirs. So the group of three is NOT three copies of one template: it is one field layout
// with TWO TAGS, i.e. two variants. Rounds 231/232 called them "twins", which overstated it, and that wording
// is corrected here: field-identical variants distinguished by the tag they write.
inline constexpr int kRatioFamilyTagA = 6;                  // RE 0x724EB4 and 0x7251B4
inline constexpr int kRatioFamilyTagB = 5;                  // RE 0x72D638
inline constexpr int kRatioFamilyTagCount = 2;              // the two variants the group splits into
// RE 0x712740 (round 244): the SAME rule and the SAME tag of five as 0x72D5B0, but operating on stack copies
// rather than on object fields:
//     712E40/712E49  xmm1 = [rsp+0xD0], xmm2 = [rsp+0x108]     ; the primary pair, on the stack
//     712E52 xmm3 = [50.0] ; 712E5E subsd ; 712E62 andpd ; 712E6A ucomisd ; 712E6E ja
//     712E74/712E78 seta                                        ; the direct comparison
//     712E83 dword [rsp+0x160] = 5                              ; the tag, FIVE again
//     712E96 shl rax,4 ; 712EA3/712EAB/712EAE rdx*8-rdx then *8  ; the 16-byte selection and the 56 stride
// so the variants are not tied to a storage form: the same two tags appear on object fields and on stack copies.
// Each tag now has TWO sites.
inline constexpr int kRatioFamilyTagSites6 = 2;              // 0x724E40 and 0x725140
inline constexpr int kRatioFamilyTagSites5 = 2;              // 0x72D5B0 and 0x712740
inline constexpr std::size_t kRatioFamilyStackPrimaryA = 0xD0;   // RE 0x712E40
inline constexpr std::size_t kRatioFamilyStackPrimaryB = 0x108;  // RE 0x712E49
inline constexpr std::size_t kRatioFamilyStackTag = 0x160;       // RE 0x712E83
static_assert(kRatioFamilyTagSites6 + kRatioFamilyTagSites5 == 4, "four tag sites in the group");
inline constexpr int kRatioFamilyMembers = 3;              // 0x7DB6E0, 0x724E40 and 0x725140
// RE 0x725140 (round 231) is a NEAR TWIN of 0x724E40: the same 50.0 slot, the same field offsets (+0x50 and
// +0x88 for the margin, +0x40/+0x80 and +0x78/+0x48 for the ratio), the same `dword [rbx+0x10] = 6` tag and
// the same 56-byte stride at 0x7251CC/0x7251D4. Two instantiations of one rule, as with the twins of round
// 174 -- so the family has three distinct field-sets of which two are a twin pair.
inline constexpr int kRatioFamilyTwins = 3;                 // CORRECTED in round 232: see below
// RE round 232's member scan: 0x72D5B0 touches the SAME field set as 0x725140 and 0x724E40 --
// +0x10, +0x40, +0x48, +0x50, +0x78, +0x80, +0x88 -- so the twin group is THREE, not two. My round-231
// value of two was written before that scan and is corrected here.
// The scan also splits the family's remaining members into groups by the fields they touch and the
// predicate they call:
//   +0x30/+0x38 and a call to 0x5E6060 (the almostEqual predicate of round 185): 0x7DB7D0 and 0x7DC360
//   +0x10/+0x18/+0x20 (the tree layout of round 178): 0x714D40 and 0x716DA0, the latter calling 0x7DB6E0
//   the wide variant +0x08..+0x38: 0x71FFB0
inline constexpr std::size_t kRatioFamilyRatioFields = 7;   // the shared field count of the twin group
inline constexpr std::size_t kRatioFamilyAlmostFieldA = 0x30;   // RE the 0x7DB7D0/0x7DC360 pair
inline constexpr std::size_t kRatioFamilyAlmostFieldB = 0x38;
inline constexpr std::uintptr_t kAlmostEqualPredicate = 0x5E6060;   // RE their calls, round 185's predicate
inline constexpr int kRatioFamilyAlmostPair = 2;            // 0x7DB7D0 and 0x7DC360
inline constexpr int kRatioFamilyTreePair = 2;              // 0x714D40 and 0x716DA0
// RE 0x716DA0 (round 231) is the family's USE SITE: it walks a tree with [rax+0x20] as the key and [rax+0x10]
// / [rax+0x18] as the children -- the layout of round 178 -- and calls the round-216 comparator 0x7DB6E0 from
// inside that walk (0x716E6A), carrying the family's 50.0 too (0x716E24).
// RE round 235: 0x714D40 is the SAME shape as 0x716DA0 -- a tree walk on [rax+0x20] with children at
// [rax+0x10] / [rax+0x18] followed by a call to the same comparator 0x7DB6E0 (0x714E21) -- but its branch
// uses `setl` (0x714DF3) where 0x716DA0 uses `setg` (0x716E43). So these are the two DIRECTIONS of the same
// ordered container, not two unrelated users, and they share the comparator and the tree layout.
inline constexpr std::uintptr_t kTreeLookupGreater = 0x716DA0;   // RE 0x716E43, `setg`
inline constexpr std::uintptr_t kTreeLookupLess = 0x714D40;      // RE 0x714DF3, `setl`
inline constexpr int kTreeLookupDirections = 2;
inline constexpr std::size_t kTreeLookupAlloc = 0x68;            // RE 0x714E2E: 104 bytes
inline constexpr std::uintptr_t kComparatorUseSite = 0x716DA0;   // RE 0x716E6A
inline constexpr std::size_t kUseSiteTreeKey = 0x20;             // RE 0x716E3C
inline constexpr std::size_t kUseSiteTreeChildA = 0x10;          // RE 0x716E33
inline constexpr std::size_t kUseSiteTreeChildB = 0x18;          // RE 0x716E4F
static_assert(kRatioFamilyTwins <= kRatioFamilyMembers, "the twins are members");

// --- two sizes seen for the first time (round 227) ----------------------------------------------------
//     724ECC/724ED7  `lea rcx,[rdx*8] ; sub rcx,rdx` then scaled by eight: 7 * 8 = 56 bytes per element
//     18052A         `mov ecx,0x148`: 328 bytes, in 0x180500
inline constexpr std::size_t kStride56 = 7 * 8;            // RE 0x724ED7
inline constexpr std::size_t kSize148 = 0x148;             // RE 0x18052A (328)
static_assert(kStride56 == 56, "seven words per element");


// --- the container element accessor 0x824B40, thirty callers (round 247) -------------------------------
//     824B4B/824B4F/824B53  three pointers at +0x8, +0x10, +0x18 of the iterator/container argument
//     824B5A/824B5D/824B63  (begin - blockStart) then `sar rdx,3`   -- a pointer difference in words
//     824B67 imul rdx,rbx   ; the constant 0x82FA0BE82FA0BE83 is multiplied in
//     824B6B add rdx,r8     ; plus the requested index
//     824B7E/824B81 r9 = [r10] ; r11 = r9 + 0x158        ; the element and the NEXT one, 0x158 apart
//     824B8F/824B93        writes the element at +0x8 and its successor at +0x10
//     824BA0 imul rdx,r8,0x158 ; 824BB3 imul rcx,rdx,0x158   ; the same size on both the positive and the
//                                                              negative index paths (cf. rounds 204/205)
// SO: the container whose accessor this is holds 0x158-byte elements, and the accessor has THIRTY callers, so the
// element size 0x158 (344 -- the same value as round 156's walk stride and round 228's allocation) is the record
// size of a container used throughout the binary.
// WHAT IS NOT CLAIMED: the constant 0x82FA0BE82FA0BE83 is recorded as read, NOT interpreted as a division
// constant. The multiply is the TWO-OPERAND low-64 form (`imul rdx,rbx`), and rounds 183/204 established that only
// the one-operand form produces the high half a division would need, so calling this a divide-by-21 idiom would
// repeat exactly the error those rounds retracted.
inline constexpr std::uint64_t kAccessorMagic = 0x82FA0BE82FA0BE83ULL;   // RE 0x824B41, UNINTERPRETED
inline constexpr std::size_t kAccessorElementBytes = 0x158;               // RE 0x824B81 and 0x824BA0
inline constexpr int kAccessorShift = 3;                                  // RE 0x824B63
inline constexpr int kAccessorCallers = 30;
static_assert(kAccessorElementBytes == 344, "the element size is 344 bytes");

// --- the pairwise loop of 0x5E8870 (round 242) --------------------------------------------------------
//     5E8899 add rbx,0x10                       ; the container holds SIXTEEN-byte elements
//     5E88B1 cmp rbx,[r9+8] ; 5E88C2 je         ; walked until the end pointer
//     5E88CC mov r12,0xFFFFFFFFFFFFFFFF         ; the -1 sentinel again -- the fifth sighting
//     5E88E5 movsd xmm6,[50.0]                  ; the family's constant
//     5E893D and 5E8950 call 0x824B40           ; the same callee TWICE per iteration, i.e. pairwise
//     5E8959 lea rdx,[rsi+rsi*8]                ; a nine multiplier, the first step of the 19-word indexing
// so this member consumes the same constant and calls the same helper as the mapper, and it uses the -1 sentinel
// for a local slot. The nine multiplier is landed as what it is -- an intermediate of the addressing -- and the
// full nineteen is already a constant from round 240.
inline constexpr std::uintptr_t kPairwiseCallee = 0x824B40;   // RE 0x5E893D and 0x5E8950
inline constexpr std::size_t kPairwiseElementStride = 0x10;   // RE 0x5E8899
inline constexpr int kPairwiseCallsPerStep = 2;               // RE the two calls per iteration
inline constexpr int kSentinelSightings = 5;                  // 0x5E88CC joins rounds 178/180/219/237
inline constexpr int kNineMultiplier = 9;                     // RE 0x5E8959
// NOTE: the equality with kPoint2dSize is checked at run time in tests/test_recovered.cpp, which includes
// compare.hpp as well; a static_assert here cannot see that constant (the same trap as round 212).

// --- the mapper of 0x711AD0: a 40-byte walk and the twins' offsets again (round 241) -------------------
//     711BDF add rsi,0x28                    ; the walk steps FORTY bytes per record
//     711B36/711B47 cmp rbx,1 ; cqo ; idiv rbx    ; 1 / rbx, with rdx as the remainder
//     711B4A/711B51 lea rax,[rdx+rdx*4] ; lea r14,[rsi+rax*8]   ; the remainder times 40
//     711BA1/711BA5/711BAD lea rdx,[rax+rax*8] ; lea rdx,[rax+rdx*2] ; shl rdx,3   ; 19 words again
//     711BB5/711BC0 [r8+0x80] = ... ; [r8+0x78] = ...          ; writes at the twins' ratio offsets
//     711BD5 cmp [r8+0x48], rax                                ; and compares at their denominator offset
// so this function walks 40-byte records and produces or checks the same 152-byte elements the twins read, writing
// +0x78 and +0x80 and comparing +0x48 -- which independently agrees with kRatioFamilyNumB, kRatioFamilyDenA and
// kRatioFamilyDenB from rounds 227/232. The 40-byte walk is new. That the 19-word stride appears here too is its
// second sighting.
inline constexpr std::size_t kRecordStride40 = 0x28;      // RE 0x711BDF (40)
inline constexpr std::size_t kMapperFieldA = 0x78;        // RE 0x711BC0, agrees with kRatioFamilyNumB
inline constexpr std::size_t kMapperFieldB = 0x80;        // RE 0x711BB5, agrees with kRatioFamilyDenA
inline constexpr std::size_t kMapperCompare = 0x48;       // RE 0x711BD5, agrees with kRatioFamilyDenB
inline constexpr int kStride152Sightings = 2;             // RE 0x7DE230 and 0x711BAD
static_assert(kMapperFieldA == kRatioFamilyNumB, "the mapper writes the numerator offset the twins read");
static_assert(kMapperFieldB == kRatioFamilyDenA, "and the denominator offset");
static_assert(kMapperCompare == kRatioFamilyDenB, "and compares the other denominator offset");

// --- the family's fifth member and a NINETEEN-word stride, from 0x7DE1B0 (round 240) -----------------
//     7DE212 movsd xmm3,[50.0]
//     7DE21A lea rdx,[rbp+rbp*8]                  ; rbp * 9
//     7DE223 lea rdx,[rbp+rdx*2]                  ; rbp + 18*rbp  =  rbp * 19
//     7DE230 lea rdx,[r15 + rdx*8 + 0x30]         ; rbp * 152 + 0x30   <- a 152-byte element stride
//     7DE235 lea rax,[rdi + rax*8 + 0x30]
//     7DE23A/7DE23F xmm1 = [rdx+0x10], xmm2 = [rax+0x10]   ; the primary pair, at record + 0x40
//     7DE254 ucomisd ; 7DE258 ja ; 7DE25A seta             ; the margin test, as in the other members
// so this member's primary offset is +0x40 (0x30 + 0x10), which agrees with the pair of round 238, and the
// element stride here is nineteen words -- 152 bytes -- a value not recorded before.
inline constexpr std::size_t kStride152 = 19 * 8;          // RE 0x7DE230 (152)
inline constexpr int kStride152Words = 19;                 // RE 0x7DE223
inline constexpr std::size_t kFamilyMember5Primary = 0x40; // RE 0x7DE23A (record + 0x30 + 0x10)
inline constexpr std::size_t kFamilyMember5Base = 0x30;    // RE 0x7DE230
inline constexpr int kRatioFamilyMembers2 = 5;             // 0x7DB6E0, 0x724E40/0x725140/0x72D5B0, 0x7DB7D0/0x7DC360, this one
static_assert(kStride152 == 152, "nineteen words");
static_assert(kFamilyMember5Primary == kFamilyMember5Base + 0x10, "the primary field is the base plus ten");

// --- the record container joined against the tree, in 0x71FFB0 (round 239) ---------------------------
//     71FFE0 r14 = [rcx+0x10]   ; the container's begin
//     71FFEB rdx = [rcx+0x30]   ; its end
//     72000A cmp r14,rdx ; 72000D je            ; walk it
//     720030 cmp byte [r14+0x20],0 ; jne        ; a flag byte at +0x20 of each record
//     720048 lea r13,[r14+0x30]                 ; and a key tuple starting at +0x30
//     720057/72005B/72005F/720066  four qwords: [r13], [r13+8], [r13+0x10], [r13+0x18]
//     72006A/720070/720076  three doubles: [r13+0x28], [r13+0x30], [r13+0x38]  -> +0x58, +0x60, +0x68
//     72009C/7200A0/7200A3  rdx = [rax+0x20] ; cmp r8,rdx ; setg cl   ; then a tree walk on the node key
//     720093 mov rax,[rax+0x10]                                     ; descending the tree's child
// so the routine walks one container and, for each record, looks the record's key tuple up in the tree whose
// layout round 178 recorded. The record's own offsets are what is landed here; the tree offsets are already
// constants from that earlier round and are deliberately not re-asserted as if they were new.
inline constexpr std::size_t kJoinBeginOffset = 0x10;    // RE 0x71FFE0
inline constexpr std::size_t kJoinEndOffset = 0x30;      // RE 0x71FFEB
inline constexpr std::size_t kJoinRecordFlag = 0x20;     // RE 0x720030, a byte
inline constexpr std::size_t kJoinRecordKey = 0x30;      // RE 0x720048
inline constexpr int kJoinKeyWords = 4;                  // RE the four qword loads
inline constexpr std::size_t kJoinRecordDoubleA = 0x58;  // RE 0x72006A (r13+0x28)
inline constexpr std::size_t kJoinRecordDoubleB = 0x60;  // RE 0x720070
inline constexpr std::size_t kJoinRecordDoubleC = 0x68;  // RE 0x720076
static_assert(kJoinRecordDoubleB - kJoinRecordDoubleA == 8, "three consecutive doubles");
static_assert(kJoinRecordDoubleC - kJoinRecordDoubleB == 8, "three consecutive doubles");
static_assert(kJoinRecordDoubleA - kJoinRecordKey == 0x28, "the doubles follow the key tuple");

// --- the two-allocation wrapper of 0x21C770 (round 236) ---------------------------------------------
//     21C792 mov ecx,0x50 ; 21C79D call 0x998500        ; allocate 80 bytes
//     21C7AA..21C7DA zero qwords at +0x08, +0x10, +0x18, +0x20, +0x28, +0x30, +0x38
//     21C7ED [rbx+0x40] = [rdi]                         ; the source pointer
//     21C7E5 [rbx+0x48] = 0
//     21C7F1 lea rax,[rip+0x81AD18] ; 21C7F8 [rbx] = rax ; a vtable at offset zero
//     21C7A2 mov ecx,0x1B8 ; 21C7FB call 0x998500       ; then a second allocation of 440 bytes
//     21C80D call 0x1FD180
// so this wrapper allocates twice -- 80 bytes for the header it fills in above and 440 for the body it hands to
// 0x1FD180 -- and both sizes were unrecorded before.
inline constexpr std::size_t kAlloc0x50 = 0x50;          // RE 0x21C792 (80)
inline constexpr std::size_t kAlloc0x1B8 = 0x1B8;        // RE 0x21C7A2 (440)
inline constexpr std::size_t kWrapperVtable = 0x00;      // RE 0x21C7F8
inline constexpr std::size_t kWrapperFirstField = 0x08;  // RE 0x21C7AA
inline constexpr std::size_t kWrapperSource = 0x40;      // RE 0x21C7ED
inline constexpr std::size_t kWrapperBody = 0x48;        // RE 0x21C812
inline constexpr int kWrapperZeroedQwords = 7;           // RE the seven stores from 0x21C7AA
static_assert(kAlloc0x50 == 80 && kAlloc0x1B8 == 440, "the two allocation sizes of 0x21C770");

// --- the identity quad and the sentinel's fourth sighting, from 0x72E120 (round 237) ------------------
//     72E13E movsd xmm1,[1.0] (rva 0x9DFBC8)     ; the shared unit literal of round 226
//     72E174/72E17D/72E186  a four-double group on the stack: zero at +0xC8, ONE at +0xD0, zeros at +0xD8/+0xE0
//     72E198/72E1A1/72E1AA  the same pattern again at +0x160 (one at +0x168)
//     72E1BE and 72E1E9/72E1F1/72E1F9/72E221  five qwords of 0xFFFFFFFFFFFFFFFF (rbp = -1)
//     72E201 byte 1 at +0x100
// so this initialiser lays down (0, 1, 0, 0) twice -- the identity for a four-component quantity -- and uses the
// -1 sentinel of rounds 178/180/219 five more times, this time for stack slots rather than object fields.
inline constexpr double kIdentityQuadPattern[4] = {0.0, 1.0, 0.0, 0.0};   // RE 0x72E174..0x72E186
inline constexpr int kIdentityQuadCount = 2;              // RE 0x72E174 and 0x72E198
inline constexpr int kSentinelQwordUses = 5;              // RE 0x72E1BE, 0x72E1E9, 0x72E1F1, 0x72E1F9, 0x72E221
inline constexpr std::size_t kIdentityQuadStride = 0x98;  // the two groups are 0x98 apart on the stack
static_assert(kIdentityQuadPattern[1] == 1.0, "the second component carries the unit");

// --- the constructor family of 0x21F9F0 / 0x220730 / 0x220230 (round 228) ---------------------------
// Shared by all three:
//     the unit literal at rva 0x9C1BF0: 21FA15 in round 215, 220780 (0x220730) and 22026A (0x220230)
//     the callee 0x1FD6C0: 21FA22, 220796 and 22029B
//     a byte flag next to a zeroed qword, eight bytes earlier:
//         22079B byte [rbx+0x140] = ...   with 2207A9 qword [rbx+0x138] = 0
//         2202A3 byte [rbx+0x150] = ...   with 2202AD qword [rbx+0x148] = 0
//         21FA27 byte [rbx+0x140] = ...   with 21FA2E qword [rbx+0x138] = 0   (round 215)
// so the pair (zero word, flag byte) appears twice, one at 0x138 and one at 0x148, i.e. 0x10 apart.
inline constexpr std::uintptr_t kCtorFamilyUnitRva = 0x9C1BF0;   // RE 0x220780 and 0x22026A (and 0x21FA15)
inline constexpr std::uintptr_t kCtorFamilyCallee = 0x1FD6C0;    // RE 0x220796 and 0x22029B (and 0x21FA22)
inline constexpr std::size_t kCtorPairAWord = 0x138;             // RE 0x2207A9
inline constexpr std::size_t kCtorPairAFlag = 0x140;             // RE 0x22079B
inline constexpr std::size_t kCtorPairBWord = 0x148;             // RE 0x2202AD
inline constexpr std::size_t kCtorPairBFlag = 0x150;             // RE 0x2202A3
inline constexpr std::size_t kCtorPairSpacing = 0x10;            // the two pairs are this far apart
inline constexpr std::size_t kCtorFamilyMembers = 4;             // 0x21F9F0, 0x220730, 0x220230, 0x2204A0
// RE 0x2204A0 (round 230), the fourth member: it initialises [rcx] with a vtable, zeros +0x10/+0x18/+0x20,
// stores its argument at +0x28, takes +0x30 from the source, writes the family's 1.0 at +0x08 (0x22050D, the
// same rva 0x9C1BF0), and then walks the source range [r8+0x10]..[r8+0x18] ALLOCATING 0x158 BYTES PER ELEMENT
// (0x220554/0x220567) while reading the byte flag at +0x140 (0x22055C). So it builds a vector of the family's
// 344-byte records, and 0x158 is now confirmed a third time: round 156's walk stride, round 228's allocation
// and this round's per-element allocation.
inline constexpr std::size_t kCtorFamilyRecordBytes = 0x158;    // RE 0x220554
inline constexpr std::size_t kCtorVecVtable = 0x00;             // RE 0x2204CE
inline constexpr std::size_t kCtorVecUnit = 0x08;               // RE 0x22050D
inline constexpr std::size_t kCtorVecZeroA = 0x10;              // RE 0x2204DC
inline constexpr std::size_t kCtorVecZeroB = 0x18;              // RE 0x2204E4
inline constexpr std::size_t kCtorVecZeroC = 0x20;              // RE 0x2204EC
inline constexpr std::size_t kCtorVecArgument = 0x28;           // RE 0x220505
inline constexpr std::size_t kCtorVecSource = 0x30;             // RE 0x2204F4
// NOTE: the equalities with kSize158 (declared below) and kTimingRecordStride are asserted at run time in
// tests/test_recovered.cpp, which sees the whole header; a static_assert here would precede the declaration.
static_assert(kCtorFamilyMembers == 4, "four functions carry this layout");

// --- the allocation size of 0x220230 (round 228) ------------------------------------------------------
//     220243 mov ecx,0x158 ; 220250 call 0x998500
// 0x158 is 344, the timing record stride of round 156 -- an independent corroboration of that stride, this time
// as an allocation size inside a constructor rather than as a walk step.
inline constexpr std::size_t kSize158 = 0x158;                   // RE 0x220243 (344)
static_assert(kSize158 == kTimingRecordStride, "the allocation size is the stride of round 156");
static_assert(kCtorPairAFlag - kCtorPairAWord == 8, "the flag follows its zeroed word");
static_assert(kCtorPairBWord - kCtorPairAWord == kCtorPairSpacing, "the two pairs are one spacing apart");


// --- the family rule completed: the ratio comparison is epsilon-guarded (round 233) ------------------
// RE 0x7DC360: after the margin test, the two ratios are compared by cross multiplication
//     7DC401 mulsd [rdx+0x30],[rcx+0x38]      ; the numerator is +0x30, the denominator +0x38
//     7DC416 mulsd [rcx+0x30],[rdx+0x38]
//     7DC42E call 0x5E6060                    ; and then almostEqual guards the comparison
//     7DC433 jne -> the comparison falls through (treated as equal)
//     7DC437 ucomisd ; seta                   ; otherwise the order of the products decides
// so this pair of members differs from the round-216 member exactly by that tie test, which is why they call
// almostEqual. The rule is: margin, then the epsilon-guarded cross-multiplied ratio.
inline constexpr std::size_t kRatioAlmostNum = 0x30;        // RE 0x7DC401
inline constexpr std::size_t kRatioAlmostDen = 0x38;        // RE 0x7DC40B
inline constexpr int kRatioAlmostPair = 2;                  // 0x7DB7D0 and 0x7DC360
// RE 0x7DB7D0 (round 238), the pair's larger member, read to complete the family's field table:
//     7DB844/7DB84E/7DB858  it compares three key words first: +0x20, then +0x18, then +0x10
//     7DB85E/7DB863        xmm1 = [rcx+0x40], xmm2 = [rdx+0x40]   <- the PRIMARY pair is +0x40 here
//     7DB868 xmm3 = [50.0] ; 7DB874 subsd ; 7DB878 andpd ; 7DB880 ucomisd ; 7DB884 ja
//     7DB886 seta          the direct comparison, taken when the margin is not exceeded
//     7DB89D/7DB8BB        the ratio cross products from +0x30 and +0x38, as in round 233
//     7DB8CC call 0x5E6060 ; 7DB8D5 seta   the epsilon guarded ratio comparison
// So each family member has its own PRIMARY OFFSET (+0x38 for the round-216 member, +0x50/+0x88 for the
// twin group, +0x40 here) AND its own ratio offsets: the twin group reads +0x40/+0x80 and +0x78/+0x48 while
// this pair reads +0x30/+0x38. Round 233's note that the ratio fields are shared was wrong and is corrected
// here: what the members share is the 50.0 literal and the rule, not the offsets. This pair additionally
// compares three key words before applying the rule.
inline constexpr std::size_t kRatioAlmostPrimary = 0x40;    // RE 0x7DB85E
inline constexpr int kRatioAlmostKeyWords = 3;              // RE 0x7DB844, 0x7DB84E, 0x7DB858
inline constexpr std::size_t kRatioAlmostKeyA = 0x20;       // RE 0x7DB844
inline constexpr std::size_t kRatioAlmostKeyB = 0x18;       // RE 0x7DB84E
inline constexpr std::size_t kRatioAlmostKeyC = 0x10;       // RE 0x7DB858
static_assert(kRatioAlmostKeyA > kRatioAlmostKeyB && kRatioAlmostKeyB > kRatioAlmostKeyC,
              "the key words are compared in descending offset order");
inline constexpr int kRatioFamilyRuleCases = 3;             // equal by tie test, ordered, or margin


// --- four widely called primitives (round 248) -------------------------------------------------------
// (1) THE ATOMIC RELEASE, 0x86A2C0, sixty-one callers:
//     86A2C0 mov eax,0xFFFFFFFF                    ; -1
//     86A2C5 lock xadd dword [rcx+0x10], eax       ; atomic fetch-add of -1; eax holds the OLD count
//     86A2CC test eax,eax ; 86A2CC jle 0x86A2D0
//     86A2D0 jmp 0x9984B0                          ; only a non-positive old count reaches the deallocator
inline constexpr std::size_t kReleaseCounterOffset = 0x10;      // RE 0x86A2C5
inline constexpr std::uintptr_t kReleaseDealloc = 0x9984B0;     // RE 0x86A2D0
inline constexpr int kReleaseCallers = 61;
inline constexpr std::uint32_t kReleaseDecrement = 0xFFFFFFFFu; // RE 0x86A2C0, i.e. -1 as an int32

// (2) THE STRICT GREATER PREDICATE, 0x5C4D30, thirty-nine callers:
//     5C4D30/5C4D33 al = [rcx], r8b = [rdx] ; 5C4D3A je ; 5C4D3C cmp ; 5C4D3F seta
//     5C4D43/5C4D47 rax = [rcx+8] ; cmp [rdx+8],rax ; 5C4D4F setg al
//     5C4D56 mov edx,0 ; 5C4D5B cmove eax,edx
// NOTE what it is NOT: with equality mapped to zero and `setg`/`seta` for the rest, this answers "is a greater
// than b" and never -1. Calling it a three-way comparator would be wrong and is avoided here.
inline constexpr std::size_t kCompareByteOffset = 0x00;         // RE 0x5C4D30
inline constexpr std::size_t kCompareWordOffset = 0x08;         // RE 0x5C4D43
inline constexpr int kCompareCallers = 39;
inline constexpr bool kCompareIsStrictGreater = true;           // RE the seta/setg/cmove shape

// (3) THE THUNK, 0x8774F0, five bytes and sixty-seven callers: `jmp 0x8771C0`, so every one of those call sites
//     really reaches 0x8771C0.
inline constexpr std::uintptr_t kThunkTarget = 0x8771C0;        // RE 0x8774F0
inline constexpr int kThunkCallers = 67;

// (4) THE ONCE GUARD, 0x8AA7E0, sixty-five callers: it calls 0x63F6A8 and then returns the qword at the data slot
//     rip+0x100502, which is the once/singleton shape.
inline constexpr std::uintptr_t kOnceCallee = 0x63F6A8;         // RE 0x8AA7F2
inline constexpr int kOnceCallers = 65;


// --- the tag-aware comparator of 0xF2000, sixty-six callers (round 249) ------------------------------
//     0xF2004/0xF200A/0xF2020/0xF2040  a 32-bit tag at +0x20 whose value ONE means unset
//     0xF2014/0xF202B                  delegate to 0xF1F50 when neither is tagged
//     0xF2030 neg eax                  when BOTH are tagged the delegate's answer is NEGATED
inline constexpr std::size_t kTagFieldOffset = 0x20;       // RE 0xF2004
inline constexpr int kTagUnsetValue = 1;                   // RE 0xF2004, 0xF200A, 0xF2020, 0xF2040
inline constexpr std::uintptr_t kDelegateCompare = 0xF1F50; // RE 0xF2014 and 0xF202B
inline constexpr bool kBothUnsetNegates = true;             // RE 0xF2030
inline constexpr int kTagAwareCallers = 66;

// --- the tagged sign object of 0xF12C0, sixty-four callers (round 249) --------------------------------
//     0xF12D8 lea rax,[rip+0x960411] ; 0xF12EC [rsi] = rax    ; a vtable at offset zero
//     0xF12DF [rsi+0x10] = 2                                  ; a kind of two
//     0xF12E7 mov ecx,0x10 ; 0xF12EF call 0xFE1F0             ; a sixteen-byte payload
//     0xF12F6/0xF12FE/0xF1300  sign extraction: negate and set the flag when negative
//     0xF1308 [rsi+0x20] = edx                                ; the sign lives at the same +0x20 as the tag
//     0xF130B/0xF130E  the payload is {magnitude, 0}
inline constexpr std::uintptr_t kSignVtableRva = 0x960411;  // RE 0xF12D8
inline constexpr std::size_t kKindOffset = 0x10;            // RE 0xF12DF
inline constexpr int kKindValue2 = 2;                       // RE 0xF12DF
inline constexpr std::size_t kSignOffset = 0x20;            // RE 0xF1308, the same offset as the tag
inline constexpr std::size_t kPayloadBytes = 0x10;          // RE 0xF12E7
inline constexpr std::uintptr_t kPayloadAlloc = 0xFE1F0;    // RE 0xF12EF
inline constexpr std::uintptr_t kLazyInitCallee = 0xEEEE0;  // RE 0xF1320
inline constexpr int kSignObjectCallers = 64;

// --- the suspected small-object accessor of 0x4189B0, fifty-eight callers (round 249) ------------------
//     0x4189B7/0x4189E0/0x4189E2  counts at +0x14 and +0x00
//     0x4189C1/0x4189C5           the pointer at +0x18
//     0x4189D4 jmp 0x9984A0       tail call with it
// INFERENCE, not a recovered layout: the offsets and the tail call are read, but the claim that this is a
// small-object/SSO accessor is a reading of the SHAPE only and is marked as such.
inline constexpr std::size_t kSsoCapacity = 0x14;           // RE 0x4189B7
inline constexpr std::size_t kSsoSize = 0x00;               // RE 0x4189E0
inline constexpr std::size_t kSsoData = 0x18;               // RE 0x4189C1
inline constexpr std::uintptr_t kSsoTailCall = 0x9984A0;    // RE 0x4189D4
inline constexpr int kSsoCallers = 58;
inline constexpr bool kSsoInference = true;                 // NOT proven, see the comment above


// --- the bit-length algorithm of 0xF1AA0, fifty-five callers (round 250) ------------------------------
//     0xF1AA0/0xF1AA4  the word count at +0x10 and the word array at +0x18
//     0xF1AAD          a zero count returns zero
//     0xF1AB0/0xF1AB6  trailing zero words are skipped
//     0xF1AC4 shl eax,6          -- each word contributes 64 bits, applied as a shift of six
//     0xF1ADE mov eax,0x40       -- the bisection starts at 64
//     0xF1AF0..0xF1B09 the bisection itself: shr r8,cl, test, cmp ecx,1, ja
inline constexpr std::size_t kBigIntCountOffset = 0x10;      // RE 0xF1AA0
inline constexpr std::size_t kBigIntWordsOffset = 0x18;      // RE 0xF1AA4
inline constexpr int kBitsPerWord = 0x40;                    // RE 0xF1ADE
inline constexpr int kBitShiftPerWord = 6;                   // RE 0xF1AC4 (a shift of six is times 64)
inline constexpr bool kBitLengthBisect = true;               // RE the loop at 0xF1AF0
inline constexpr int kBitLengthCallers = 55;
static_assert(1 << kBitShiftPerWord == kBitsPerWord, "the shift counts the bits of one word");

// --- the container walk of 0x8F2CA0, fifty-one callers (round 250) ------------------------------------
//     0x8F2CA7/0x8F2CAB  the end at +0x08 and the begin at +0x00
//     0x8F2CB1 cmp rsi,rbx ; je                     ; walk until they meet
//     0x8F2CC3 lea rax,[rbx+0x10] ; 0x8F2CC7 cmp rcx,rax   ; the element stride is sixteen bytes
inline constexpr std::size_t kWalkBeginOffset = 0x00;        // RE 0x8F2CAB
inline constexpr std::size_t kWalkEndOffset = 0x08;          // RE 0x8F2CA7
inline constexpr std::size_t kWalkElementStride = 0x10;      // RE 0x8F2CC3
inline constexpr int kWalkCallers = 51;


// --- the byte-length sibling, 0xF19E0, fifty callers (round 251) --------------------------------------
//     0xF19E0/0xF19E4  the same word count at +0x10 and word array at +0x18
//     0xF1A0A lea r10d,[rax*8]     ; eight bytes per word, where the bit version shifts by six
//     0xF1A46 cmp ecx,8 ; ja       ; the bisection stops at eight rather than one
//     0xF1A4B shr eax,3            ; and the answer is divided by eight
inline constexpr int kBytesPerWord = 8;                      // RE 0xF1A0A
inline constexpr int kByteShiftPerWord = 3;                  // RE 0xF1A4B
inline constexpr int kByteLengthCallers = 50;
static_assert(kBitsPerWord == kBytesPerWord * 8, "bits per word are eight times bytes per word");
static_assert(1 << kByteShiftPerWord == kBytesPerWord, "the shift is the byte count");

// --- the two add-then-shift idioms, now explained (round 251) -----------------------------------------
// RE 0xF1AC4 (`lea eax,[rdx+0x3FFFFFF] ; shl eax,6`) and 0xF1A04/0xF1A0A (`lea eax,[rdx+0x1FFFFFFF] ; *8`).
// In 32-bit arithmetic these are exactly (count - 1) * 64 and (count - 1) * 8:
//     (count + 0x3FFFFFF) << 6 == count*64 + 0xFFFFFFC0 == (count - 1) * 64   (mod 2**32)
//     (count + 0x1FFFFFFF) * 8 == count*8  + 0xFFFFFFF8 == (count - 1) * 8    (mod 2**32)
// because 0x3FFFFFF == 2**26 - 1 and 0x1FFFFFFF == 2**29 - 1. The test asserts the identity, so this is checked,
// not merely claimed.
inline constexpr std::uint32_t kBitsScaleAddend = 0x3FFFFFFu;   // RE 0xF1AC4
inline constexpr std::uint32_t kBytesScaleAddend = 0x1FFFFFFFu; // RE 0xF1A04
static_assert(kBitsScaleAddend == (1u << 26) - 1, "the addend is 2**26 - 1");
static_assert(kBytesScaleAddend == (1u << 29) - 1, "the addend is 2**29 - 1");

// --- the search wrapper of 0x86B6B0, thirty-seven callers (round 251) ---------------------------------
//     0x86B6BC rdx = -1                        ; the default answer
//     0x86B6D0 call 0x63F238                   ; a length helper (skipped when the second argument is null)
//     0x86B6E4 call 0x869EF0                   ; the search itself
//     0x86B6E9 [rsi] = rax                     ; the result
inline constexpr std::uintptr_t kSearchHelper = 0x869EF0;       // RE 0x86B6E4
inline constexpr std::uintptr_t kLengthHelper = 0x63F238;       // RE 0x86B6D0
inline constexpr std::int64_t kSearchDefault = -1;              // RE 0x86B6BC
inline constexpr int kSearchCallers = 37;


// --- the error formatter of 0x77F2D0, forty-three callers (round 252) ---------------------------------
//     0x77F2D7 mov ecx,0x30 ; 0x77F2DC call 0x9988C0     ; a forty-eight byte buffer
//     0x77F2F7 lea rdx,[rip+0x233C92]                    ; the literal 'BER decode error'
//     0x77F303 and 0x77F332 call 0xC71D0                 ; CORRECTED (round 254): this is std::string's
//                                                          _M_construct, so the formatter builds a
//                                                          std::string rather than using its own helper
//     0x77F30D/0x77F340/0x77F354 three vtable pointers: rip+0x2D39DC, rip+0x2C2F49, rip+0x2BFA55
//     0x77F34F/0x77F3A0 call 0x9984B0                    ; release, the same deallocator as round 248's
inline constexpr std::size_t kFormatterAlloc = 0x30;         // RE 0x77F2D7 (48)
inline constexpr std::uintptr_t kFormatterTextHelper = 0xC71D0;   // RE 0x77F303
inline constexpr std::uintptr_t kFormatterRelease = 0x9984B0;     // RE 0x77F34F
inline constexpr std::uintptr_t kFormatterVtableA = 0x2D39DC;     // RE 0x77F30D, a vtable RVA
inline constexpr std::uintptr_t kFormatterVtableB = 0x2C2F49;     // RE 0x77F340
inline constexpr std::uintptr_t kFormatterVtableC = 0x2BFA55;     // RE 0x77F354
inline constexpr int kFormatterCallers = 43;
static_assert(kFormatterAlloc == 48, "forty-eight bytes");

// --- the gated getter block of 0x945370, forty-two callers (round 252) --------------------------------
//     0x94537F/0x945384 call 0x990540 ; test al,al ; je    ; a check
//     0x94538B call 0x9916E0 ; 0x945393 [rsi+0xF0] = rax  ; the get, landing at +0xF0
//     0x94539A/0x9453A1 the next check 0x990840
//     0x9453A6 call 0x9919E0 ; 0x9453AE [rsi+0xF8] = rax  ; and the next field, eight bytes on
//     0x9453B5 call 0x990780                               ; the pattern repeats
inline constexpr std::size_t kGetterFieldA = 0xF0;           // RE 0x945393
inline constexpr std::size_t kGetterFieldB = 0xF8;           // RE 0x9453AE
inline constexpr std::size_t kGetterStep = 8;                // the fields step by eight
inline constexpr std::uintptr_t kGetterCheckA = 0x990540;    // RE 0x94537F
inline constexpr std::uintptr_t kGetterGetA = 0x9916E0;      // RE 0x94538B
inline constexpr std::uintptr_t kGetterCheckB = 0x990840;    // RE 0x94539A
inline constexpr std::uintptr_t kGetterGetB = 0x9919E0;      // RE 0x9453A6
inline constexpr std::uintptr_t kGetterCheckC = 0x990780;    // RE 0x9453B5
inline constexpr int kGetterCallers = 42;
static_assert(kGetterFieldB - kGetterFieldA == kGetterStep, "the two fields are one step apart");


// --- the third member of the big-integer family, 0xF1580, forty-four callers (round 253) --------------
//     0xF1580 cmp dword [rcx+0x20],1 ; je 0xF15C0   ; the tag of round 249, unset == 1, answers zero
//     0xF1586 rdx = [rcx+0x18]                      ; the word array, as in 0xF1AA0 and 0xF19E0
//     0xF158C cmp qword [rdx],0 ; jne               ; a fast path on the first word
//     0xF1592 rax = [rcx+0x10]                      ; the word count
//     0xF15A0/0xF15A6 the same trailing-zero-word skip loop as the other two
//     0xF15AE test eax,eax ; sete al                ; zero exactly when nothing significant remains
inline constexpr std::uintptr_t kBigIntIsZero = 0xF1580;      // RE the whole routine
inline constexpr int kBigIntFamilyMembers = 3;                // bits 0xF1AA0, bytes 0xF19E0, this
inline constexpr int kBigIntZeroCallers = 44;
inline constexpr bool kBigIntFirstWordFastPath = true;        // RE 0xF158C
// The tag semantics of round 249 are CORROBORATED here: the same 32-bit field at +0x20 with the same value 1
// meaning unset, in a function that has nothing to do with that comparator. Two independent sightings.
inline constexpr int kTagSecondSighting = 1;                  // RE 0xF1580
static_assert(kBigIntFamilyMembers == 3, "three members share the +0x10 / +0x18 layout");

// --- the exception plumbing of 0x998CD0, thirty-six callers (round 253) --------------------------------
//     0x998CE7/0x998D12 call 0x63F6A8    ; the same callee round 248's once guard uses
//     0x998CF3 call 0x63F6C0 ; 0x998D1E call 0x63F720 ; 0x998D2E call 0x63F6B8
//     0x998D45 mov ecx,8 ; 0x998D4A call 0x9988C0     ; an eight-byte allocation
//     0x998D68/0x998D89 call 0x7C4AB0 / 0x7C4A80 ; 0x998D73 call 0x9A0700
inline constexpr std::uintptr_t kExceptionHelper = 0x63F6A8;   // RE 0x998CE7, the same as kOnceCallee
inline constexpr std::size_t kExceptionAlloc = 8;              // RE 0x998D45
inline constexpr int kExceptionCallers = 36;
static_assert(kExceptionHelper == kOnceCallee, "one helper serves both the once guard and this plumbing");


// --- the nested-container destructor 0x8CE510, thirty-six callers (round 254) --------------------------
//     0x8CE51E/0x8CE51A  the outer begin at +0x00 and end at +0x08
//     0x8CE534/0x8CE530  each outer element holds an inner begin at +0x18 and end at +0x20
//     0x8CE54D add rbx,0x18   ; inner elements are twenty-four bytes
//     0x8CE574 add rdi,0x30   ; outer elements are forty-eight bytes
//     0x8CE548/0x8CE562/0x8CE56F/0x8CE593 call 0x9984B0 -- the shared deallocator, third sighting
inline constexpr std::size_t kNestedOuterBegin = 0x00;       // RE 0x8CE51E
inline constexpr std::size_t kNestedOuterEnd = 0x08;         // RE 0x8CE51A
inline constexpr std::size_t kNestedInnerBegin = 0x18;       // RE 0x8CE534
inline constexpr std::size_t kNestedInnerEnd = 0x20;         // RE 0x8CE530
inline constexpr std::size_t kInnerStride24 = 0x18;          // RE 0x8CE54D
inline constexpr std::size_t kOuterStride48 = 0x30;          // RE 0x8CE574
inline constexpr std::uintptr_t kSharedDealloc = 0x9984B0;   // RE 0x8CE548, also rounds 248 and 252
inline constexpr int kNestedDestructorCallers = 36;
inline constexpr int kSharedDeallocSightings = 3;            // rounds 248, 252 and this one
static_assert(kOuterStride48 == 48 && kInnerStride24 == 24, "forty-eight outer, twenty-four inner");
static_assert(kNestedInnerEnd - kNestedInnerBegin == 8, "the inner pair is eight bytes apart");

// --- TOOLCHAIN, not domain: 0xC71D0 is std::string's _M_construct (round 254) --------------------------
// RE 0xC71E7: the assertion text at rva 0x8EBA82 is 'basic_string::_M_construct n', which is libstdc++'s own.
// The objective excludes libstdc++/MinGW, so this routine is registered as library evidence (see
// re/covlib.py) rather than counted as domain code. Its size and caller count are recorded for the audit:
// 177 bytes and eleven callers.
inline constexpr std::uintptr_t kStdStringConstruct = 0xC71D0;   // RE 0xC71E7, toolchain
inline constexpr int kStdStringConstructCallers = 11;


// --- the list-block destructor 0xC2510, fifty-eight callers (round 256) --------------------------------
//     0xC2518/0xC2528  two vtable pointers are installed at +0x00 and +0x08 first
//     0xC2521 rbx = [rcx+0x20]   ; the list head
//     0xC2546 rbp = [rbx]        ; the next pointer, at +0x00 of a node -- a SINGLY linked list
//     0xC2549 rcx = [rbx+0x10]   ; the node's buffer
//     0xC2540 rdx = [rbx+0x18]   ; its length
//     0xC2550 rep stosb          ; zero-fill that many bytes (al is zero)
//     0xC2555 call 0xFE240       ; a release helper
//     0xC2560 call 0x9984B0      ; the shared deallocator, now its fourth sighting
inline constexpr std::size_t kListNodeNext = 0x00;           // RE 0xC2546
inline constexpr std::size_t kListNodeBuffer = 0x10;         // RE 0xC2549
inline constexpr std::size_t kListNodeLength = 0x18;         // RE 0xC2540
inline constexpr std::size_t kListHeadOffset = 0x20;         // RE 0xC2521
inline constexpr std::uintptr_t kListReleaseHelper = 0xFE240; // RE 0xC2555
inline constexpr int kListDestructorCallers = 58;
inline constexpr int kSharedDeallocSightings2 = 4;           // rounds 248, 252, 254 and this one
static_assert(kListNodeBuffer < kListNodeLength, "the buffer pointer precedes the length");
static_assert(kListNodeLength < kListHeadOffset, "the node fields precede the head offset");

// --- the eight-byte allocation path 0x998920, forty-four callers (round 256) ---------------------------
//     0x998924 mov ecx,8 ; 0x998929 call 0x9988C0   ; eight bytes from the allocator of rounds 252/253
//     0x998943 [rax] = rcx+0x10                     ; the vtable-ish pointer is installed
//     0x99894D call 0x999030                        ; the throw path, also from rounds 252/253
inline constexpr std::size_t kAlloc8 = 8;                    // RE 0x998924
inline constexpr std::uintptr_t kAllocHelper = 0x9988C0;     // RE 0x998929, sighting three
inline constexpr std::uintptr_t kThrowHelper = 0x999030;     // RE 0x99894D, sighting three
inline constexpr int kAlloc8Callers = 44;
inline constexpr int kHelperSightings = 3;                   // rounds 252, 253 and this one
static_assert(kAlloc8 == 8, "eight bytes");


// --- the big-integer copy assignment 0xF3460, ONE HUNDRED AND SIXTY-TWO callers (round 257) ------------
//     0xF3470 je          a self-assignment guard -- assigning an object to itself does nothing
//     0xF3476/0xF347A     the source and destination word counts, both at +0x10
//     0xF347E             the source word array at +0x18
//     0xF3487..0xF34A1    the family's trailing-zero-word skip
//     0xF34A5 cmp rax,8   ; at most eight words takes a branch that was NOT dumped and is left unrecorded
//     0xF34AF cmp rax,0x10; above eight and at most sixteen -> SIXTEEN
//     0xF3530 cmp rax,0x20; at most thirty-two            -> THIRTY-TWO
//     0xF353F cmp rax,0x40; at most sixty-four            -> SIXTY-FOUR
//     0xF354E..0xF3588    beyond that, `mov ebx,1 ; shl rbx,cl` after a bisection: the NEXT POWER OF TWO
//     0xF34CD call 0x78F740   ; the allocation of the chosen capacity
//     0xF34EE call 0x63F2F8   ; the copy, with r8 = count * 8
//     0xF34F3/0xF34F6         the 32-bit field at +0x20 is copied: the tag/sign of rounds 249 and 253
inline constexpr std::uintptr_t kBigIntAssign = 0xF3460;      // RE the whole routine
inline constexpr int kBigIntAssignCallers = 162;
inline constexpr std::uintptr_t kBigIntAlloc = 0x78F740;      // RE 0xF34CD
inline constexpr std::uintptr_t kBigIntCopy = 0x63F2F8;       // RE 0xF34EE
inline constexpr std::size_t kBigIntCapSixteen = 0x10;        // RE 0xF34AF
inline constexpr std::size_t kBigIntCapThirtyTwo = 0x20;      // RE 0xF3530
inline constexpr std::size_t kBigIntCapSixtyFour = 0x40;      // RE 0xF353F
inline constexpr int kBigIntCapLadderKnown = 3;               // the three thresholds actually dumped
inline constexpr bool kBigIntAssignSelfGuard = true;          // RE 0xF3470
inline constexpr bool kBigIntSmallBranchUnknown = true;      // RE 0xF34A5: the <= 8 branch is NOT recorded
static_assert(kBigIntCapSixteen * 2 == kBigIntCapThirtyTwo, "the ladder doubles");
static_assert(kBigIntCapThirtyTwo * 2 == kBigIntCapSixtyFour, "the ladder doubles");


// --- the reset routine of the large object, 0x87D8E0, fifty-three callers (round 258) -----------------
//     0x87D8F1 call 0x822590      ; the eight-byte function: a predicate, its answer gates the reset
//     0x87D90D xor eax,1          ; a flag inverted before use
//     0x87D917 dword [rcx+0x58] = 0   ; round 226's first flag on the 0x98-byte object
//     0x87D91E byte  [rcx+0x90] = 0   ; and its second -- so this routine operates on THAT object
//     0x87D94E/0x87D952/0x87D956  +0x08, +0x10 and +0x18 all take the same value
//     0x87D93E/0x87D946/0x87D95D  +0x28, +0x20 and +0x30 are zeroed
//     0x87D95A/0x87D965/0x87D968  the dword at +0x5C is copied to both +0x60 and +0x64
//     0x87D936/0x87D93A           the bytes at +0x79 and +0x7A are cleared
//     0x87D96B call 0x8771C0      ; the target of round 248's five-byte thunk, called directly here
inline constexpr std::uintptr_t kResetEntry = 0x87D8E0;      // RE the whole routine
inline constexpr int kResetCallers = 53;
inline constexpr std::uintptr_t kResetPredicate = 0x822590;  // RE 0x87D8F1, the 8-byte predicate
inline constexpr std::uintptr_t kResetSubCall = 0x87D270;    // RE 0x87D908
inline constexpr std::uintptr_t kResetSubCallB = 0x87D4E0;   // RE 0x87D925
inline constexpr std::size_t kResetEmbedded = 0x48;          // RE 0x87D8E7, passed to the predicate
inline constexpr std::size_t kResetTripleA = 0x08;           // RE 0x87D94E
inline constexpr std::size_t kResetTripleB = 0x10;           // RE 0x87D952
inline constexpr std::size_t kResetTripleC = 0x18;           // RE 0x87D956
inline constexpr std::size_t kResetZeroA = 0x20;             // RE 0x87D946
inline constexpr std::size_t kResetZeroB = 0x28;             // RE 0x87D93E
inline constexpr std::size_t kResetZeroC = 0x30;             // RE 0x87D95D
inline constexpr std::size_t kResetSource = 0x5C;            // RE 0x87D95A
inline constexpr std::size_t kResetCopyA = 0x60;             // RE 0x87D965
inline constexpr std::size_t kResetCopyB = 0x64;             // RE 0x87D968
inline constexpr std::size_t kResetByteA = 0x79;             // RE 0x87D936
inline constexpr std::size_t kResetByteB = 0x7A;             // RE 0x87D93A
static_assert(kResetCopyB - kResetCopyA == 4, "the two copies are four bytes apart");
static_assert(kResetTripleB - kResetTripleA == 8, "the three pointers are eight bytes apart");
static_assert(kResetTripleC - kResetTripleB == 8, "the three pointers are eight bytes apart");
static_assert(kResetByteB - kResetByteA == 1, "the two bytes are adjacent");


// --- the non-null predicate, 0x822590, thirty-six callers (round 259) ---------------------------------
//     0x822590 cmp qword [rcx],0 ; 0x822594 setne al ; ret
// exactly "the first field of the object is not null", which is why round 258's reset gates on its answer.
inline constexpr std::uintptr_t kNonNullPredicate = 0x822590;   // RE the whole routine
inline constexpr std::size_t kNonNullFieldOffset = 0x00;        // RE 0x822590
inline constexpr int kNonNullCallers = 36;

// --- the polymorphic status query 0x87D270, three callers (round 259) ---------------------------------
//     0x87D28A cmp [rcx+0x20],[rcx+0x28] ; jb   ; an ordering or capacity check
//     0x87D297 cmp byte [rcx+0x7A],0            ; the byte round 258 clears
//     0x87D29D/0x87D2A7  the interface pointer at +0x98, null tested
//     0x87D2B0 call qword [rax+0x30]            ; virtual slot 0x30
//     0x87D2EA call qword [rax+0x18]            ; virtual slot 0x18
//     0x87D304 call qword [rax+0x68] with edx = 0xFFFFFFFF
//     0x87D307 cmp eax,-1 ; setne bl            ; the answer is "not the sentinel"
inline constexpr std::uintptr_t kStatusQuery = 0x87D270;        // RE the whole routine
inline constexpr std::size_t kInterfaceOffset = 0x98;           // RE 0x87D29D
inline constexpr std::size_t kVtableSlotA = 0x18;               // RE 0x87D2EA
inline constexpr std::size_t kVtableSlotB = 0x30;               // RE 0x87D2B0
inline constexpr std::size_t kVtableSlotC = 0x68;               // RE 0x87D304
inline constexpr std::int32_t kStatusSentinel = -1;             // RE 0x87D2FC
inline constexpr std::int32_t kStatusOne = 1;                   // RE 0x87D2F4
inline constexpr std::int32_t kStatusTwo = 2;                   // RE 0x87D2F2
inline constexpr std::uintptr_t kStatusHelper = 0x8772A0;       // RE 0x87D337
inline constexpr std::size_t kStatusCountA = 0x20;              // RE 0x87D28A
inline constexpr std::size_t kStatusCountB = 0x28;              // RE 0x87D28A
inline constexpr std::size_t kStatusFlag = 0x7A;                // RE 0x87D297
static_assert(kInterfaceOffset == 0x98, "the interface pointer sits at 0x98");
static_assert(kStatusCountB - kStatusCountA == 8, "the two counts are eight bytes apart");
static_assert(kStatusSentinel == -1, "the sentinel is minus one");


// --- the optional-buffer releaser 0x87D4E0, two callers (round 260) -----------------------------------
//     0x87D4E5 cmp byte [rcx+0x78],0 ; je        ; the FIRST byte of the trio round 258 half-cleared
//     0x87D4EE/0x87D4F7 the buffer at +0x68, released with 0x9984A0
//     0x87D4FC/0x87D504 the buffer pointer and its flag are both cleared
//     0x87D508/0x87D514 the second buffer at +0xA0, released the same way
//     0x87D519/0x87D524/0x87D52F/0x87D53A   +0xA0, +0xA8, +0xB0 and +0xB8 are zeroed
inline constexpr std::size_t kByteTrioA = 0x78;              // RE 0x87D4E5 -- round 258 cleared B and C
inline constexpr std::size_t kOptionalBuffer = 0x68;         // RE 0x87D4EE
inline constexpr std::size_t kSecondBuffer = 0xA0;           // RE 0x87D508
inline constexpr std::size_t kBlockA0 = 0xA0;                // RE 0x87D519
inline constexpr std::size_t kBlockA0End = 0xB8;             // RE 0x87D53A
inline constexpr int kBlockA0Qwords = 4;                     // RE the four stores
inline constexpr std::uintptr_t kReleaserAlt = 0x9984A0;     // RE 0x87D4F7, distinct from 0x9984B0
inline constexpr int kReleaserCallers = 2;
static_assert(kBlockA0End - kBlockA0 == (kBlockA0Qwords - 1) * 8, "four qwords, eight bytes apart");
static_assert(kByteTrioA + 2 == kResetByteB, "the trio starts two bytes before round 258's second byte");

// --- the two-step trampoline 0x8772A0, four callers (round 260) ----------------------------------------
//     0x8772AD call 0x877120                     ; obtain a value
//     0x8772BA mov ecx,eax ; 0x8772C1 jmp 0x65C940 ; and marshal it into the next function
inline constexpr std::uintptr_t kTrampoline = 0x8772A0;      // RE the whole routine
inline constexpr std::uintptr_t kTrampolineInner = 0x877120; // RE 0x8772AD
inline constexpr std::uintptr_t kTrampolineTarget = 0x65C940; // RE 0x8772C1
inline constexpr int kTrampolineCallers = 4;

}  // namespace lcns
LCNS_RECOVERED(layout.record_sizes);   // strides and block sizes, rounds 218-241
LCNS_RECOVERED(layout.sentinel_convention);   // three -1 qwords beside one -1.0 double
LCNS_STRUCTURAL(model.ctor_family);   // rva 0x9C1BF0 unit literal, callee 0x1FD6C0
LCNS_STRUCTURAL(model.hash_table);   // 128 buckets of 24-byte entries, +0x48 key
