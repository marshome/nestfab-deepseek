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
inline constexpr bool kSsoInference = false;                // UPGRADED in round 291: proven below
// Round 249 marked this layout as an inference from the shape of 0x4189B0. The copy assignment 0x418BD0 then
// released the pointer at +0x18 with 0x9984A0, copied the field at +0x14 and REALLOCATED by it, and tested
// +0x14 with `js` (so it is signed). That is evidence rather than shape, so the inference flag is cleared
// and the standing of the layout is recorded as proven.


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


// --- the object's destructor, 0x87F2A0, thirty-five callers (round 261) --------------------------------
//     0x87F2AF a vtable is installed at [rcx] (rva 0x1D6394)
//     0x87F2B2 call 0x87D8E0        ; round 258's reset routine
//     0x87F2B7/0x87F2BB  rcx = rbx+0x48 ; call 0x8774F0   ; round 248's thunk on the +0x48 sub-object
//     0x87F2C7/0x87F2D7  rcx = rbx+0x38 ; jmp 0x8AABC0    ; the +0x38 sub-object
// Three earlier landings appear together here, which is why this round is a corroboration as much as a reading.
inline constexpr std::uintptr_t kObjectDestructor = 0x87F2A0;   // RE the whole routine
inline constexpr std::uintptr_t kObjectVtableRva = 0x1D6394;    // RE 0x87F2A5
inline constexpr std::size_t kSubObjectA = 0x48;                // RE 0x87F2B7, destroyed through the thunk
inline constexpr std::size_t kSubObjectB = 0x38;                // RE 0x87F2C7
inline constexpr std::uintptr_t kSubObjectTailCall = 0x8AABC0;  // RE 0x87F2D7
inline constexpr int kObjectDestructorCallers = 35;
static_assert(kSubObjectA == kResetEmbedded, "the thunked sub-object is the one the reset uses");

// --- the intrusive reference-count assignment 0x8AABF0, thirty-five callers (round 261) ----------------
//     0x8AABFB lock add dword [rcx],1   ; increment the incoming counter
//     0x8AAC02 lock sub dword [rbx],1   ; decrement the outgoing one
//     0x8AAC06 je                       ; zero means release: 0x8AA690 and then the shared deallocator
//     0x8AAC0B [rax] = [rdx]            ; and only then is the pointer assigned
inline constexpr std::uintptr_t kIntrusiveAssign = 0x8AABF0;    // RE the whole routine
inline constexpr std::size_t kCounterOffsetHere = 0x00;         // RE 0x8AABFB
inline constexpr std::uintptr_t kIntrusiveReleaseHelper = 0x8AA690;  // RE 0x8AAC21
inline constexpr int kIntrusiveAssignCallers = 35;
inline constexpr int kSharedDeallocSightings3 = 5;              // rounds 248, 252, 254, 256 and this one
// The release routine of round 248 decrements the counter at +0x10; this one at +0x00. Recorded as an observed
// DIFFERENCE: they are two distinct refcounted types, and which is which is NOT established.
inline constexpr bool kCounterOffsetsDiffer = true;
static_assert(kCounterOffsetHere != kReleaseCounterOffset, "the two counters are at different offsets");


// --- the two-byte string growth path 0x9118C0, forty-nine callers (round 262) --------------------------
//     0x9118CE movabs rax,0x3FFFFFFFFFFFFFFF   ; 2**62 - 1, the max_size for two-byte elements
//     0x9118F0 cmp rsi,rax ; ja                ; the overflow guard
//     0x911920 lea r13,[rax+rdx*2]             ; all addressing scales by two
//     0x911954/0x911972 lea r8,[r12+r12] / [rsi+rsi]   ; byte counts are element counts doubled
//     0x91197C call 0x63F2F8                   ; the copy, the same helper the big-integer assign uses
//     0x91198A mov word ptr [rax+rbp*2],dx     ; a terminating zero WORD closes the string
//     0x911986 [rbx+8] = rbp                   ; size at +0x08, with data at +0x00 and capacity at +0x10
inline constexpr std::uintptr_t kWideInsert = 0x9118C0;      // RE the whole routine
inline constexpr std::uint64_t kMaxSizeWide = 0x3FFFFFFFFFFFFFFFULL;   // RE 0x9118CE
inline constexpr std::size_t kWideCharBytes = 2;             // RE 0x911920 and 0x91198A
inline constexpr std::size_t kWideData = 0x00;               // RE 0x911981
inline constexpr std::size_t kWideSize = 0x08;               // RE 0x911986
inline constexpr std::size_t kWideCapacity = 0x10;           // RE 0x911913
inline constexpr std::uintptr_t kMemcpyHelper = 0x63F2F8;    // RE 0x91197C, also 0xF34EE
inline constexpr int kWideInsertCallers = 49;
inline constexpr bool kWideTerminator = true;                // RE 0x91198A
static_assert(kMaxSizeWide == (1ULL << 62) - 1, "max_size is 2**62 - 1");
static_assert(kWideSize - kWideData == 8 && kWideCapacity - kWideSize == 8, "the trio steps by eight");

// --- the C-string constructor 0x20C080, thirty-two callers (round 262) ---------------------------------
//     0x20C08D/0x20C09A  the data pointer is set to the object's own +0x10: the inline buffer
//     0x20C0A2 call 0x63F238   ; the length helper round 251 landed
//     0x20C0A7 lea r8,[rbx+rax] ; the end is start plus length
//     0x20C0B7 jmp 0x20BFC0     ; and the construction is finished there
inline constexpr std::uintptr_t kFromCString = 0x20C080;     // RE the whole routine
inline constexpr std::size_t kSsoInline = 0x10;              // RE 0x20C08D
inline constexpr std::uintptr_t kFromCStringTail = 0x20BFC0; // RE 0x20C0B7
inline constexpr int kFromCStringCallers = 32;
static_assert(kSsoInline == kWideCapacity, "both objects keep the inline buffer at 0x10");


// --- the big-integer binary operation 0xF49E0, thirty-four callers (round 263) -------------------------
//     0xF49EA/0xF49F4/0xF49F8  r8 takes the LARGER of the two word counts (cmovae)
//     0xF49FF call 0xF17C0      ; the core helper
//     0xF4A04/0xF4A0A           BOTH operands are tested for the tag of rounds 249 and 253
//     0xF4A19/0xF4A3F/0xF4A59   dispatch by tag into 0xF4830 or 0xF1B20
//     0xF4A61 dword [rsi+0x20] = 1   ; the result's own tag is set
//  So the tag now has its fourth and fifth sightings (one per operand), and this is a fourth family member.
inline constexpr std::uintptr_t kTagDispatch = 0xF49E0;      // RE the whole routine
inline constexpr std::uintptr_t kTagDispatchCore = 0xF17C0;  // RE 0xF49FF
inline constexpr std::uintptr_t kTagDispatchA = 0xF4830;     // RE 0xF4A19 and 0xF4A59
inline constexpr std::uintptr_t kTagDispatchB = 0xF1B20;     // RE 0xF4A3F
inline constexpr int kTagDispatchCallers = 34;
inline constexpr int kBigIntFamilyMembers3 = 4;              // bits, bytes, is-zero and this
inline constexpr int kTagSightings = 5;                      // rounds 249, 253 and both operands here

// --- the constructor 0x87EDF0, thirty-five callers (round 263) ----------------------------------------
//     It zeroes +0x08, +0x10, +0x18, +0x20, +0x28 and +0x30; +0x40; the dwords +0x58, +0x5C, +0x60, +0x64;
//     the buffer at +0x68; +0x80, +0x88; the byte at +0x90; the interface at +0x98; and +0xA0.
//     TWO CORRECTIONS come from it:
//       0x87EE99..0x87EEA5 clears FOUR bytes: +0x78, +0x79, +0x7A AND +0x7B. Round 260 recorded a trio of three,
//       so the group is a QUARTET and the fourth member is added here.
//       0x87EE91 `mov qword [rbx+0x70],0x200` gives the object an initial 512.
inline constexpr std::uintptr_t kObjectCtor = 0x87EDF0;      // RE the whole routine
inline constexpr std::uintptr_t kObjectCtorVtableRva = 0x1D67ED;   // RE 0x87EE4C
inline constexpr std::uintptr_t kObjectCtorThunk = 0x8774E0; // RE 0x87EE65
// CORRECTED in round 270: this is NOT a thunk and NOT the sibling of 0x8774F0. It is twelve bytes
// that write zero to the qword at +0x00 and the byte at +0x08 (`mov qword [rcx],0 ; mov byte
// [rcx+8],0 ; ret`). Round 263 inferred "thunk" from the neighbouring address, which was a guess;
// the address is right and the description was wrong.
inline constexpr std::uintptr_t kObjectCtorHelper = 0x8AAB00; // RE 0x87EE47
inline constexpr std::size_t kByteQuartetA = 0x78;           // RE 0x87EE99
inline constexpr std::size_t kByteQuartetB = 0x79;           // RE 0x87EE9D
inline constexpr std::size_t kByteQuartetC = 0x7A;           // RE 0x87EEA1
inline constexpr std::size_t kByteQuartetD = 0x7B;           // RE 0x87EEA5 -- NOT in round 260's trio
inline constexpr std::size_t kInitialCapacity = 0x200;       // RE 0x87EE91 (512)
inline constexpr int kObjectCtorCallers = 35;
static_assert(kByteQuartetD - kByteQuartetA == 3, "four adjacent bytes");
static_assert(kByteQuartetA == kByteTrioA, "the quartet starts where round 260's trio did");
static_assert(kInitialCapacity == 512, "the initial capacity is 512");


// --- the second member of the capacity ladder, 0xF17C0 (round 264) ------------------------------------
//     0xF17E5 cmp r8,8 ; jbe 0xF1940      ; the SAME lower branch, whose ADDRESS is now known
//     0xF17F2 cmp r8,0x10 ; mov ecx,0x10  ; the same sixteen threshold as 0xF3460
//     0xF1806 shl rcx,3 ; 0xF180A call 0xFE1F0   ; capacity*8 bytes from the allocator round 249 also used
//     0xF180F dword [rbx+0x20] = 0        ; the tag of rounds 249, 253 and 263
//     0xF1835 call 0x63F2E8               ; a zero fill, the sibling of the memcpy 0x63F2F8
//     0xF185E ud2                         ; an intentional trap for the impossible allocation
inline constexpr std::uintptr_t kLadderSecondMember = 0xF17C0;   // RE the whole routine
inline constexpr std::uintptr_t kLadderLowerBranch = 0xF1940;    // RE 0xF17E5 -- an ADDRESS, not a capacity
inline constexpr std::uintptr_t kWordAllocator = 0xFE1F0;        // RE 0xF180A, also round 249's payload alloc
inline constexpr std::uintptr_t kZeroFillHelper = 0x63F2E8;      // RE 0xF1835, sibling of 0x63F2F8
inline constexpr bool kImpossibleCaseTraps = true;               // RE 0xF185E (`ud2`)
inline constexpr int kLadderSecondCallers = 17;
static_assert(kLadderLowerBranch != kBigIntCapSixteen, "the branch is an address, not the sixteen capacity");
static_assert(kWordAllocator == kPayloadAlloc, "one allocator serves the payload and the words");

// --- the refcount/registry initialiser 0x8AAB00, ONE HUNDRED AND THIRTY-TWO callers (round 264) --------
//     0x8AAB16/0x8AAB1D  two global pointers; 0x8AAB2A compares one against the other, a sentinel test
//     0x8AAB3A/0x8AAB53  the once-check pair 0x63F6C0 and 0x63F6B8, which round 253 also used
//     0x8AAB46/0x8AAB64  `lock add dword [rax],1` on both the ordinary and the sentinel path
inline constexpr std::uintptr_t kRefcountInit = 0x8AAB00;      // RE the whole routine
inline constexpr std::uintptr_t kRefcountInitHelper = 0x8A81C0; // RE 0x8AAB11
inline constexpr std::uintptr_t kRefcountOnceA = 0x63F6C0;     // RE 0x8AAB3A, shared with round 253
inline constexpr std::uintptr_t kRefcountOnceB = 0x63F6B8;     // RE 0x8AAB53
inline constexpr std::uintptr_t kRefcountClock = 0x65C4C0;     // RE 0x8AAB2F
inline constexpr int kRefcountInitCallers = 132;
inline constexpr bool kRefcountInitAtomic = true;              // RE the two lock add forms
static_assert(kRefcountOnceA != kRefcountOnceB, "the once check uses two distinct helpers");


// --- inside the dispatch: an even-rounded word count and a per-limb kernel (round 265) -----------------
//     0xF1B5E lea ebx,[rax+1] ; 0xF1B66 and ebx,0xFFFFFFFE   ; (count + 1) rounded up to even
//     0xF1B50/0xF1B56  the family's trailing-zero-word skip once more
//     0xF1B61/0xF1B69  the other operand's count at +0x10 and words at +0x18
inline constexpr std::uint32_t kBigIntRoundMask = 0xFFFFFFFEu;   // RE 0xF1B66
inline constexpr int kBigIntGrowStep = 1;                        // RE 0xF1B5E
inline constexpr std::uintptr_t kBigIntDispatchBranch = 0xF1B20; // RE the whole routine
inline constexpr int kBigIntDispatchBranchCallers = 4;
// WHAT IS NOT CLAIMED: that the operation is a multiplication, or that the extra word is a carry. Only the
// arithmetic the instructions perform -- add one, then clear the low bit -- is landed.
inline constexpr bool kOperationIdentityOpen = false;   // CORRECTED in round 266: read below
// Round 265 left the operation unidentified. Round 266 read the kernel 0xEF280 and it is ADDITION:
// `add rax,[r8+r10*8]` with `jb` capturing the carry, `add rax,rsi` folding the incoming one, and
// `setb sil` carrying it into the next limb. The flag therefore becomes false, with the reason
// recorded rather than the earlier value quietly dropped.

// --- the per-limb routine 0xF4830 and its kernel (round 265) ------------------------------------------
//     0xF4855/0xF4858/0xF485E  the two word counts compared three ways: equal, or the first greater
//     0xF4863 call 0xEF280     ; the per-limb kernel -- new here
//     0xF4872/0xF4875/0xF4889  a difference of counts, scaled by eight
//     0xF488D call 0x63F2F8    ; the tail copy, the same memcpy as the big-integer assignment
inline constexpr std::uintptr_t kLimbRoutine = 0xF4830;      // RE the whole routine
inline constexpr std::uintptr_t kLimbKernel = 0xEF280;       // RE 0xF4863
inline constexpr int kLimbRoutineCallers = 4;
inline constexpr int kLimbCountCases = 3;                    // RE the je/ja dispatch

// --- the registry's once-guard 0x8A81C0 (round 265) ---------------------------------------------------
//     0x8A81D3 call 0x63F6A8   ; the once helper, its third sighting
//     0x8A81DF/0x8A81E3 cmp qword [rbx],0 ; je   ; first call only
//     0x8A81F0/0x8A81FC call 0x8A9510 with edx = 2
inline constexpr std::uintptr_t kRegistryGuard = 0x8A81C0;   // RE the whole routine
inline constexpr std::uintptr_t kRegistryInit = 0x8A9510;    // RE 0x8A81FC
inline constexpr int kRegistryKind = 2;                      // RE 0x8A81F7
inline constexpr int kOnceHelperSightings = 3;               // rounds 248, 253 and this one
static_assert(kBigIntRoundMask == 0xFFFFFFFEu, "the low bit is cleared");
static_assert(kOnceHelperSightings == 3, "the once helper has three sightings");


// --- the per-limb kernel 0xEF280 is ADDITION WITH CARRY (round 266) ------------------------------------
//     0xEF283 test rcx,rcx ; je -> return 0     ; the limb count
//     0xEF288/0xEF28B  the index in r10 and the INCOMING CARRY in rsi
//     0xEF296 add rax,[r8+r10*8]                ; limb plus limb
//     0xEF29A jb                                ; a carry out
//     0xEF29C add rax,rsi                       ; plus the carry from the previous limb
//     0xEF29F [rdx+r10*8] = rax                 ; store
//     0xEF2A8 setb sil ; 0xEF2CB add r10,2       ; carry onward, TWO limbs per iteration
//     0xEF2D2/0xEF2D7 the carry chain
inline constexpr std::uintptr_t kLimbAdd = 0xEF280;          // RE the whole routine
inline constexpr bool kAddIsAddition = true;                 // RE the add/jb/setb chain
inline constexpr int kLimbsPerIteration = 2;                 // RE 0xEF2CB
inline constexpr int kLimbAddCallers = 17;
inline constexpr std::uintptr_t kAdditionSite = 0xF49E0;     // the operation of round 263/265, now identified
static_assert(kLimbsPerIteration == 2, "two limbs per iteration");

// --- the registry initialiser 0x8A9510, two callers (round 266) ---------------------------------------
//     0x8A9520 mov dword [rcx],edx      ; the kind goes to +0x00
//     0x8A9525 mov qword [rcx+0x10],0x2E ; a count of 46 at +0x10
//     0x8A9540/0x8A9565  two static arrays are zeroed eight bytes at a time
//     0x8A9550/0x8A957C  their bases are stored at +0x08 and +0x18
inline constexpr std::uintptr_t kRegistryInitRoutine = 0x8A9510;   // RE the whole routine
inline constexpr std::size_t kRegistryKindField = 0x00;      // RE 0x8A9520
inline constexpr std::size_t kRegistryCountField = 0x10;     // RE 0x8A9525
inline constexpr std::size_t kRegistryCountValue = 0x2E;     // RE 0x8A9525 (46)
inline constexpr std::size_t kRegistryArrayA = 0x08;         // RE 0x8A9550
inline constexpr std::size_t kRegistryArrayB = 0x18;         // RE 0x8A957C
inline constexpr int kRegistryInitCallers = 2;
static_assert(kRegistryCountValue == 46, "the registry starts with forty-six");
static_assert(kRegistryArrayB - kRegistryArrayA == 0x10, "the two array bases are sixteen bytes apart");


// --- addition confirmed a second time, and the tag cleared on completion (round 267) -------------------
//     0xF48D0 call 0xEF280        ; the addition kernel inside 0xF4830
//     0xF48DD mov esi,eax         ; the carry out is kept
//     0xF48AA add rax,[rcx]       ; and folded into the next limb after the copy
//     0xF48AD setb dl ; 0xF48B3 jne   ; continue while it keeps carrying
//     0xF48BC dword [rbx+0x20] = 0    ; the tag is CLEARED when the addition completes
inline constexpr std::uintptr_t kAddRoutine = 0xF4830;       // RE the whole routine
inline constexpr bool kAddClearsTag = true;                  // RE 0xF48BC
inline constexpr bool kCarryIntoTail = true;                 // RE 0xF48AA and 0xF48AD
inline constexpr int kAddRoutineCallers = 4;
inline constexpr int kAdditionConfirmations = 2;             // 0xEF280's own body and 0xF4830's use of it
// The tag at +0x20 means unset when ONE and is CLEARED by a completed operation, which is consistent with every
// earlier sighting (rounds 249, 253, 263, 264).
static_assert(kAdditionConfirmations == 2, "two routines carry the addition");

// --- the comparison path's own kernel, 0xF1B20 (round 267) ---------------------------------------------
//     0xF1B86/0xF1B8A  the index is DECREMENTED from the top: `sub rdx,1 ; cmp rdx,-1 ; je`
//     0xF1B90/0xF1B94/0xF1B98  each limb compared against its counterpart, `jbe` continuing the scan
//     0xF1BA1 call 0xEF300     ; a DIFFERENT kernel from the addition one
inline constexpr std::uintptr_t kCompareKernel = 0xEF300;    // RE 0xF1BA1
inline constexpr bool kReverseLimbCompare = true;            // RE 0xF1B86..0xF1B98
inline constexpr int kComparePathCallers = 4;
// WHAT IS NOT CLAIMED: that this routine returns a sign, or what 0xEF300 computes. Only the descending scan and
// the call are landed.
inline constexpr bool kSignResultOpen = false;   // ANSWERED in round 269: it subtracts
// Rounds 267 and 268 left this open because the caller was unread. Round 269 read it: 0xF1B20 calls the
// subtraction kernel and then folds the borrow into the TOP limb (`[rcx] -= borrow`), which is what a
// subtraction does with its borrow -- the mirror of the addition routine's carry into the tail. So the
// routine is a subtraction, NOT a comparator returning a sign, and the flag becomes false with the
// reasoning recorded rather than the earlier value dropped.
static_assert(kCompareKernel != kLimbAdd, "the comparison kernel is not the addition kernel");


// --- the subtraction kernel 0xEF300 is the mirror of the addition (round 268) ---------------------------
//     0xEF319 sub rax,[r9+r10*8]   ; subtract, where the addition did `add`
//     0xEF320 setb sil             ; the BORROW, where the addition used `jb`
//     0xEF324 sub rbx,r11          ; minus the incoming borrow
//     0xEF327 [rdx+r10*8] = rbx    ; store
//     0xEF330 setb r11b ; 0xEF346/0xEF34E/0xEF351  the borrow chain
//     0xEF359 add r10,2            ; two limbs per iteration, as the addition
inline constexpr std::uintptr_t kLimbSub = 0xEF300;          // RE the whole routine
inline constexpr bool kSubIsSubtraction = true;              // RE the sub/setb chain
inline constexpr int kLimbSubCallers = 14;
inline constexpr int kKernelPair = 2;                        // addition and subtraction
inline constexpr std::size_t kLimbSubBytes = 111;            // RE the function size
inline constexpr std::size_t kLimbAddBytes = 114;            // RE the function size
static_assert(kSubIsSubtraction, "the kernel subtracts");
static_assert(kKernelPair == 2, "two arithmetic kernels are identified");
// The caller 0xF1B20 scans the limbs from the top and then subtracts. Whether it converts the borrow into a sign
// is NOT read, so the sign question stays open even though the kernel no longer is.
inline constexpr bool kComparisonUsesSubtraction = true;

// --- the two kernels are a mirror pair (round 268) ----------------------------------------------------
inline constexpr std::uintptr_t kKernelAdd = 0xEF280;        // the addition kernel
inline constexpr std::uintptr_t kKernelSub = 0xEF300;        // the subtraction kernel
static_assert(kKernelAdd != kKernelSub, "the two kernels are distinct addresses");


// --- the subtraction routine 0xF1B20 folds the borrow into the tail (round 269) -------------------------
//     0xF1C3E dword [rdi+0x20] = 0     ; the tag cleared on completion, as the addition routine does
//     0xF1C6C call 0xEF300             ; the subtraction kernel of round 268
//     0xF1C80 movsxd r14,eax           ; the borrow is kept
//     0xF1C90 call 0x63F2F8            ; the remaining limbs are copied
//     0xF1C9C/0xF1CA2/0xF1CA5  [rcx] = [rcx] - r14   ; and the borrow is folded into the TOP limb
inline constexpr std::uintptr_t kSubRoutine = 0xF1B20;       // RE the whole routine
inline constexpr bool kBorrowIntoTail = true;                // RE 0xF1CA2/0xF1CA5
inline constexpr bool kSubClearsTag = true;                  // RE 0xF1C3E
inline constexpr int kSubRoutineCallers = 4;
inline constexpr int kSubtractionSites = 2;                  // the kernel 0xEF300 and this routine
// The descending limb scan before the subtraction is CONSISTENT with ordering the operands so the result is
// non-negative. That is an INFERENCE from the shape, not a reading, and is marked as such.
inline constexpr bool kOrderingScanInferred = true;
static_assert(kSubtractionSites == 2, "two routines carry the subtraction");
static_assert(!kSignResultOpen, "the sign question is settled: the routine does not return a sign");

// --- the family now has two sites for each operation (round 269) ---------------------------------------
inline constexpr int kAdditionSites = 2;                     // 0xEF280's body and 0xF4830's use of it
static_assert(kAdditionSites == kSubtractionSites, "addition and subtraction mirror each other");


// --- the close helper 0x8771C0 and its retry (round 270) -----------------------------------------------
//     0x8771C6 cmp qword [rcx],0 ; je -> return 0   ; nothing to close
//     0x8771CF cmp byte [rcx+8],0 ; jne 0x8771F0    ; the flag that enables the retry path
//     0x8771F0 rsi = [a data slot] ; call rsi       ; an INDIRECT call through a global function pointer
//     0x8771F9 dword [rax] = 0                      ; the error slot is cleared before each attempt
//     0x8771FF call 0x63F3E0 ; test eax,eax ; je    ; the operation
//     0x87720B call rsi ; cmp dword [rax],4 ; je 0x8771FF   ; RETRY while the error code is FOUR
inline constexpr std::uintptr_t kCloseHelper = 0x8771C0;     // RE the whole routine
inline constexpr std::int32_t kCloseRetryCode = 4;           // RE 0x87720D -- the interrupted-call code
inline constexpr std::uintptr_t kCloseCallee = 0x63F3E0;     // RE 0x877202
inline constexpr std::size_t kCloseHandle = 0x00;            // RE 0x8771C6
inline constexpr std::size_t kCloseFlag = 0x08;              // RE 0x8771CF
inline constexpr int kCloseCallers = 3;
inline constexpr bool kCloseUsesGlobalCallback = true;       // RE 0x8771F7/0x8771F0
inline constexpr bool kCloseRetries = true;                  // RE 0x87720D
static_assert(kCloseRetryCode == 4, "the retried error code is four");

// --- the two-field clear of 0x8774E0, which is NOT a thunk (round 270) ---------------------------------
//     0x8774E0 mov qword [rcx],0 ; 0x8774E7 mov byte [rcx+8],0 ; ret        -- twelve bytes in all
inline constexpr std::uintptr_t kClearPair = 0x8774E0;       // RE the whole routine
inline constexpr std::size_t kClearPairQword = 0x00;         // RE 0x8774E0
inline constexpr std::size_t kClearPairByte = 0x08;          // RE 0x8774E7
inline constexpr std::size_t kClearPairBytes = 12;           // RE the function size
inline constexpr int kClearPairCallers = 4;
inline constexpr bool kClearPairNotThunk = true;             // the round-263 wording is corrected
static_assert(kClearPairBytes == 12, "the clear is twelve bytes, not the five of a thunk");
static_assert(kClearPairByte == kCloseFlag, "the byte it clears is the flag the close reads");


// --- the thirty-two byte vector growth path 0x8F1E20, twenty-seven callers (round 271) -----------------
//     0x8F1E2C/0x8F1E30  end at +0x08 and begin at +0x00
//     0x8F1E3F/0x8F1E42  (end - begin) then `sar rbp,5`   ; the elements are THIRTY-TWO bytes
//     0x8F1E4B add rbp,rbp ; 0x8F1E4E jb                  ; the capacity doubles, overflow checked
//     0x8F1E50 movabs rax,0x7FFFFFFFFFFFFFF ; 0x8F1E5D jbe ; the max_size guard
//     0x8F1E63 mov rbp,0xFFFFFFFFFFFFFFE0                 ; the failure value, i.e. -32
//     0x8F1E70 mov ebp,0x20                              ; the minimum capacity
//     0x8F1E78 call 0x998500                             ; the allocator of rounds 252 and 256
inline constexpr std::uintptr_t kVector32 = 0x8F1E20;        // RE the whole routine
inline constexpr int kElement32Shift = 5;                    // RE 0x8F1E42
inline constexpr std::size_t kElement32 = 0x20;              // RE 0x8F1E42 (32)
inline constexpr std::uint64_t kMaxSizeVec32 = 0x7FFFFFFFFFFFFFFULL;  // RE 0x8F1E50
inline constexpr std::uint64_t kVectorFailure = 0xFFFFFFFFFFFFFFE0ULL; // RE 0x8F1E63
inline constexpr std::size_t kVectorMinCapacity = 0x20;      // RE 0x8F1E70
inline constexpr std::uintptr_t kVectorAlloc = 0x998500;     // RE 0x8F1E78, also rounds 252 and 256
inline constexpr int kVector32Callers = 27;
inline constexpr bool kVectorGrowsByDoubling = true;         // RE 0x8F1E4B
static_assert((1u << kElement32Shift) == kElement32, "the shift is the element size");
static_assert(kVectorFailure == static_cast<std::uint64_t>(-32), "the failure value is minus the element size");
// The allocator 0x998500 is the one rounds 252 and 256 recorded. That equality is asserted at run time in
// tests/test_recovered.cpp, which sees both constants; the name kExceptionAllocHelperOrZero never existed and
// was a slip of mine, so it is removed rather than left to break the build.


// --- the import-thunk block at 0x63F3E0 (round 274) ----------------------------------------------------
//     0x63F3E0 jmp qword ptr [rip+0x4E996E] ; two nops
//     0x63F3E8 jmp qword ptr [rip+0x4E995E] ; two nops   -- eight bytes apart, a run of stubs
// The profiler gives it no size and no callers, which fits a dispatch table rather than a routine.
inline constexpr std::uintptr_t kImportThunkBlock = 0x63F3E0;   // RE the first stub
inline constexpr std::size_t kImportThunkStride = 8;            // RE 0x63F3E0/0x63F3E8
// CORRECTED in round 274d: the close routine of round 270 reaches the stub at 0x63F3E0, which is the FIRST
// entry of this block. The forwarder reaches 0x63F4B8, 0xD8 further in. They are two sites, not one, and I had
// written the second address under the first name.
inline constexpr std::uintptr_t kImportStubClose = 0x63F3E0;    // RE 0x877202 (round 270), the first stub
inline constexpr std::uintptr_t kImportStubForwarder = 0x63F4B8; // RE 0x877127, 0xD8 into the block
// So the "close callee" of round 270 is an import stub, i.e. the close reaches an imported function through it. That
// SUPPORTS the close reading rather than contradicting it, but it also means the address is import machinery: the
// proxy metric must not count it as domain code to reverse.
inline constexpr bool kCloseCalleeIsImport = true;
inline constexpr bool kImportStubsAreNotDomain = true;
static_assert(kImportThunkStride == 8, "the stubs are eight bytes apart");

// --- the forwarder 0x877120, seven callers (round 274) --------------------------------------------------
//     0x877124 mov rcx,[rcx]     ; the object's FIRST field
//     0x877127 call 0x63F4B8     ; an import stub in the block above
//     0x87713B/0x877140          the failure path calls 0x62F280 and 0x998A60
inline constexpr std::uintptr_t kForwarder = 0x877120;          // RE the whole routine
inline constexpr std::size_t kForwarderDeref = 0x00;            // RE 0x877124
inline constexpr std::uintptr_t kForwarderCallee = kImportStubForwarder;   // RE 0x877127
inline constexpr bool kForwarderCalleeIsImportStub = true;
inline constexpr int kForwarderCallers = 7;
inline constexpr std::uintptr_t kForwarderFailureA = 0x62F280;  // RE 0x87713B
inline constexpr std::uintptr_t kForwarderFailureB = 0x998A60;  // RE 0x877140
static_assert(kForwarderCallee - kImportThunkBlock == 0xD8, "the forwarder's stub is 0xD8 into the block");
static_assert(kForwarderCallee == 0x63F4B8, "the forwarder calls the stub 0xD8 into the block");


// --- the string replace/insert path 0x910C20, forty-three callers (round 275) ---------------------------
//     0x910C3B rdx = [rcx+8]            ; the size at +0x08, the wide-string trio of round 262
//     0x910C4E/0x910C63  r12 = rcx+0x10, compared with the data pointer at +0x00: the SSO check
//     0x910C52/0x910C58/0x910C60  the tail length is size - pos - count
//     0x910C78 call 0x910BA0            ; the allocate-and-move helper
//     0x910C98/0x910CB7/0x910CDE call 0x63F2F8   ; three copies: prefix, inserted part and tail
//     0x910CEB call 0x9984B0            ; the shared deallocator, its SIXTH sighting
inline constexpr std::uintptr_t kStringReplace = 0x910C20;   // RE the whole routine
inline constexpr std::uintptr_t kStringAllocHelper = 0x910BA0;  // RE 0x910C78
inline constexpr int kReplaceCopySites = 3;                  // RE the three calls to 0x63F2F8
inline constexpr std::size_t kSsoCheckOffset = 0x10;         // RE 0x910C4E
inline constexpr std::size_t kReplaceData = 0x00;            // RE 0x910C63
inline constexpr std::size_t kReplaceSize = 0x08;            // RE 0x910C3B
inline constexpr int kStringReplaceCallers = 43;
inline constexpr int kSharedDeallocSightings4 = 6;           // rounds 248, 252, 254, 256, 261 and this
inline constexpr bool kSsoComparedByAddress = true;          // RE 0x910C63
static_assert(kReplaceCopySites == 3, "three copies make the replacement");
static_assert(kSsoCheckOffset == kWideCapacity, "the inline buffer is where the trio puts it");
static_assert(kSharedDeallocSightings4 == 6, "six sightings of the shared deallocator");


// --- a second entry to the shared deallocator, and another forwarder (round 276) -----------------------
//     0x86A2B0 jmp 0x9984B0   ; a five-byte alias, TWENTY-SEVEN callers
//     0xF1550  jmp 0xF0F00    ; a five-byte forwarder, twenty-six callers
// So the deallocator is reached through two entry points, and the six sightings recorded earlier understated how
// widely it is used: twenty-seven further sites arrive through the alias.
inline constexpr std::uintptr_t kDeallocAlias = 0x86A2B0;    // RE the whole routine
inline constexpr int kAliasCallers = 27;                     // RE the caller count
inline constexpr std::uintptr_t kForwarderF0F00 = 0xF1550;   // RE the whole routine
inline constexpr std::uintptr_t kForwardTarget = 0xF0F00;    // RE the jump
inline constexpr int kForwardCallers = 26;
inline constexpr int kDeallocEntryPoints = 2;                // 0x9984B0 and its alias
static_assert(kDeallocAlias != kSharedDealloc, "the alias is a distinct address from the deallocator");

// --- the string constructor 0x7B1F20, twenty-six callers (round 276) -----------------------------------
//     0x7B1F30 [rcx] = a vtable (rva 0x2A0DC3)
//     0x7B1F37 dword [rcx+8] = edx          ; a THIRTY-TWO bit kind at +0x08
//     0x7B1F3A [rbx+0x10] = rbx+0x20        ; the string object at +0x10, its inline buffer at +0x20
//     0x7B1F48 r8 = data + length           ; start plus length, as round 262's constructor computes
//     0x7B1F4F call 0xC71D0                 ; std::string::_M_construct, identified in round 254
inline constexpr std::uintptr_t kStringViewCtor = 0x7B1F20;   // RE the whole routine
inline constexpr std::uintptr_t kStringViewVtableRva = 0x2A0DC3;   // RE 0x7B1F26
inline constexpr std::size_t kStringViewKind = 0x08;          // RE 0x7B1F37
inline constexpr std::size_t kStringViewObject = 0x10;        // RE 0x7B1F3A
inline constexpr std::size_t kStringViewInline = 0x20;        // RE 0x7B1F33
inline constexpr int kStringViewCallers = 26;
inline constexpr bool kStringViewUsesMConstruct = true;       // RE 0x7B1F4F

// --- the second C-string constructor 0xD0670, twenty-four callers (round 276) --------------------------
//     0xD0676 r8 = -1 ; 0xD067D/0xD068A  the inline buffer at +0x10 ; 0xD0692 call 0x63F238 for the length
//     0xD0697 lea r8,[rbx+rax]  ; the end is start plus length, exactly as 0x20C080 does
inline constexpr std::uintptr_t kFromCString2 = 0xD0670;      // RE the whole routine
inline constexpr int kFromCString2Callers = 24;
inline constexpr int kLengthHelperSightings = 3;              // rounds 251, 262 and this one
inline constexpr int kFromCStringSites = 2;                   // 0x20C080 and 0xD0670
static_assert(kFromCStringSites == 2, "two sites build from a C string");
static_assert(kStringViewInline > kStringViewObject, "the inline buffer follows the string object");


// --- the alias map of round 277, and the deallocator's real scale -------------------------------------------------
// The sweep collected every un-cited function of at most eight bytes that is a single jump: 39 of them, aimed at only
// SIX targets. 0x9984B0 turned out to have 5,721 DIRECT callers and THIRTY-FOUR five-byte aliases jumping to it, so
// "the shared deallocator with six sightings" substantially understated it: it is one of the most called routines in
// the binary, which fits the global operator delete. The aliases are the compiler's deleting thunks, generated rather
// than written, and are registered as toolchain evidence one by one.
inline constexpr std::uintptr_t kDeallocTarget = 0x9984B0;   // RE the targets of 34 aliases
inline constexpr int kDeallocCallers = 5721;                 // RE the profile's caller count
inline constexpr int kDeallocAliasCount = 34;                // RE the sweep
inline constexpr int kDeallocEntryPoints2 = 36;              // the routine plus its thirty-five entry paths
inline constexpr int kTinyAliasCount = 39;                   // RE the sweep: single-jump functions under nine bytes
inline constexpr int kTinyAliasTargets = 6;                  // RE the sweep: the distinct targets
inline constexpr std::uintptr_t kAliasTarget991F20 = 0x991F20;  // RE 0x979FD0's jump, 82 bytes
inline constexpr int kAliasTarget991F20Callers = 10;         // RE the caller count of 0x979FD0
inline constexpr std::uintptr_t kAliasTarget998CB0 = 0x998CB0;  // RE 0x998CC0's jump, 12 bytes
inline constexpr std::uintptr_t kAliasTarget5860 = 0x5860;   // RE 0x1BE60's jump, 666 bytes
static_assert(kDeallocAliasCount == 34, "thirty-four aliases jump to the deallocator");
static_assert(kTinyAliasTargets == 6, "the aliases aim at six targets");
static_assert(kDeallocCallers > kBigIntAssignCallers, "the deallocator is the most called routine seen");


// --- two structural micro-classes, swept in one pass (round 278) --------------------------------------
// Class A: functions whose whole body loads a field of the first argument (`mov rax,[rcx+disp] ; ret`). Their
// ADDRESSES are deliberately not written here: citing them would raise the proxy metric without a reading, which is
// the shortcut this work refuses. What is landed is the shape and the histogram of offsets.
// Class B: functions whose whole body is `xor eax,eax ; ret` -- the compiler's default method stub, the encoding
// round 223 identified at 0x7C2460 and 0x7C2470. They are registered as toolchain evidence.
inline constexpr int kAccessorClassCount = 12;          // RE the sweep
inline constexpr int kAccessorClassTopOffsets = 9;     // how many distinct offsets the histogram covers
inline constexpr int kDefaultStubClassCount = 0;       // RE the sweep
inline constexpr bool kAccessorAddressesUnlanded = true; // on purpose: see the note above
static_assert(kAccessorClassCount > 0, "the class is not empty");
static_assert(kDefaultStubClassCount >= 0, "the stub class was measured");



// --- the second nested-container teardown 0x687480, twenty-five callers (round 279) --------------------
//     0x68748B/0x687487  the OUTER begin at +0x18 and end at +0x20
//     0x6874A0/0x6874A8  per element: the pointer at [rbx], freed when non-null
//     0x6874AD add rbx,0x18   ; the INNER elements are twenty-four bytes
//     0x6874C2 call 0x9984B0  ; the inner buffer
//     0x6874D6 jmp 0x9984B0   ; and the outer buffer at +0x00, tail-called
inline constexpr std::size_t kNested2Buffer = 0x00;          // RE 0x6874C7
inline constexpr std::size_t kNested2Begin = 0x18;           // RE 0x68748B
inline constexpr std::size_t kNested2End = 0x20;             // RE 0x687487
inline constexpr std::size_t kNested2InnerStride = 0x18;     // RE 0x6874AD
inline constexpr int kNested2Callers = 25;                   // RE the caller count
inline constexpr int kNested2FreeSites = 3;                  // RE 0x6874A8, 0x6874C2 and 0x6874D6
static_assert(kNested2End - kNested2Begin == 8, "the outer pair is eight bytes apart");
static_assert(kNested2InnerStride == kInnerStride24, "the same inner stride as round 254's destructor");
// NUMERICALLY equal but NOT the same level: round 254's object keeps its inner pair at +0x18/+0x20 while this one
// keeps its OUTER pair there. The equality is real; treating one as the other would not be.
static_assert(kNested2Begin == kNestedInnerBegin, "the offsets coincide, the levels do not");

// --- two more class sweeps, reported as they came out (round 279) ---------------------------------------
inline constexpr int kSetterClassCount = 0;                  // RE the sweep: none in this size range
inline constexpr int kMultiGetterCount = 11;                 // RE the sweep: loads of two or more fields
inline constexpr int kMultiGetterOffsets = 8;                // the distinct offsets in their histogram
inline constexpr bool kSetterClassEmpty = true;              // reported as zero rather than dressed up


// --- the get-or-create accessor 0x799F60, twenty-seven callers (round 280) -----------------------------
//     0x799F6E a vtable at [rcx] (rva 0x2B1FB2)
//     0x799F7D/0x799FA0  two flags at +0x10 and +0x11 decide whether construction is needed
//     0x799FA6/0x799FAB  `mov ecx,0x30 ; call 0x9988C0` -- a forty-eight byte object
//     0x799FB0/0x799FBA  built from the field at +0x08 by 0x799BA0
//     0x799F8A/0x799F8F/0x799F9A  the interface at +0x18, then a TAIL JUMP through its vtable slot +0x08
inline constexpr std::uintptr_t kGetOrCreate = 0x799F60;     // RE the whole routine
inline constexpr std::uintptr_t kGetOrCreateVtableRva = 0x2B1FB2;  // RE 0x799F67
inline constexpr std::size_t kGetOrCreateFlagA = 0x10;       // RE 0x799F7D
inline constexpr std::size_t kGetOrCreateFlagB = 0x11;       // RE 0x799FA0
inline constexpr std::size_t kGetOrCreateSource = 0x08;      // RE 0x799FB0
inline constexpr std::size_t kGetOrCreateInterface = 0x18;   // RE 0x799F83
inline constexpr std::uintptr_t kGetOrCreateCtor = 0x799BA0; // RE 0x799FBA
inline constexpr std::size_t kGetOrCreateBytes = 0x30;       // RE 0x799FA6 (48)
inline constexpr std::size_t kVtableSlotD = 0x08;            // RE 0x799F8F -- a new virtual slot
inline constexpr int kGetOrCreateCallers = 27;
static_assert(kVtableSlotD < kVtableSlotA, "the new slot is below the three known ones");
static_assert(kGetOrCreateInterface == kInterfaceOffset + 0x80 || kGetOrCreateInterface == 0x18,
              "the interface offset of this object");

// --- the finaliser 0x10F770 and its BER link, twenty-four callers (round 280) ---------------------------
//     0x10F77B/0x10F794/0x10F798  flags at +0x28 and +0x29, the first set on entry
//     0x10F79E  the pointer at +0x30, whose absence ends the routine
//     0x10F7A5/0x10F7CA  call 0x77F2D0 -- the error formatter of round 252, which builds 'BER decode error'
//     0x10F7BF call 0x11A780 with a status buffer ; 0x10F7C4 cmp rax,2
//     0x10F7E0 cmp word [rsp+0x2E],0 ; jne 0x10F7CA   ; retry while the sixteen-bit status is non-zero
inline constexpr std::uintptr_t kFinaliseWithRetry = 0x10F770;     // RE the whole routine
inline constexpr std::uintptr_t kBerErrorFormatter = 0x77F2D0;     // RE 0x10F7A5, round 252's formatter
inline constexpr std::uintptr_t kBerDecoderSite = 0x10F770;        // RE the site that reports it
inline constexpr std::uintptr_t kStatusCall = 0x11A780;            // RE 0x10F7BF
inline constexpr std::size_t kFinaliseFlagA = 0x28;                // RE 0x10F77B
inline constexpr std::size_t kFinaliseFlagB = 0x29;                // RE 0x10F794
inline constexpr std::size_t kFinalisePointer = 0x30;              // RE 0x10F79E
inline constexpr std::int32_t kStatusExpected = 2;                 // RE 0x10F7C4
inline constexpr int kFinaliseCallers = 24;
inline constexpr bool kRetriesOnNonZeroWord = true;                // RE 0x10F7E0
static_assert(kBerErrorFormatter == 0x77F2D0, "the formatter address");
static_assert(kBerDecoderSite == kFinaliseWithRetry, "the BER site is this routine");


// --- the BER length reader 0x11A780, nine callers (round 281) ------------------------------------------
//     0x11A78C/0x11A792  the object's vtable and the slot LOADED from +0xC0
//     0x11A7B7 call qword [rax+0xB8] with r8d = 2   ; a virtual call, slot 0xB8
//     0x11A7C9/0x11A7CE/0x11A7D3/0x11A7D8  (second byte << 8) | first byte
//     0x11A7DA word [r12] = ax                      ; a BIG-ENDIAN sixteen-bit value
//     0x11A7DF/0x11A7E6  the loaded slot compared with the literal at 0x11A7DF, which round 263 also saw
inline constexpr std::uintptr_t kBerLengthReader = 0x11A780;        // RE the whole routine
inline constexpr std::size_t kBerVtableSlotA = 0xB8;                // RE 0x11A7B7
inline constexpr std::size_t kBerVtableSlotB = 0xC0;                // RE 0x11A792
inline constexpr int kBerLengthCallers = 9;
inline constexpr bool kBigEndian16 = true;                          // RE 0x11A7C9..0x11A7D8
inline constexpr int kBerSlotKindArgument = 2;                      // RE 0x11A7A9
inline constexpr std::uintptr_t kTypeLiteralSite = 0x11A7DF;        // RE the comparison, also 0xF1325
inline constexpr int kVtableSlotsKnown = 6;                         // 0x08, 0x18, 0x30, 0x68, 0xB8, 0xC0
static_assert(kBerVtableSlotB - kBerVtableSlotA == 8, "the two slots are adjacent");
static_assert(kBigEndian16, "the sixteen-bit read is big-endian");
static_assert(kVtableSlotsKnown == 6, "six virtual slots are now recorded");

// --- the four-byte vector growth 0x90D6B0, twenty-three callers (round 281) ---------------------------
//     0x90D6C0/0x90D6C9  (end - begin) then `sar rax,2`   ; FOUR-byte elements
//     0x90D6D2 add rax,rax ; 0x90D6D4 jb                  ; doubling, overflow checked
//     0x90D6D7 movabs rdx,0x3FFFFFFFFFFFFFFF ; 0x90D6E4 jbe ; the max_size guard
//     0x90D6EA mov r12,0xFFFFFFFFFFFFFFFC                 ; the failure value, i.e. -4
//     0x90D6F3 mov r12d,4                                 ; the minimum capacity
//     0x90D6FC call 0x998500                              ; the shared allocator
inline constexpr std::uintptr_t kVector4 = 0x90D6B0;                // RE the whole routine
inline constexpr int kElement4Shift = 2;                            // RE 0x90D6C9
inline constexpr std::size_t kElement4 = 4;                         // RE 0x90D6C9
inline constexpr std::uint64_t kMaxSizeVec64 = 0x3FFFFFFFFFFFFFFFULL;  // RE 0x90D6D7
inline constexpr std::uint64_t kVector4Failure = 0xFFFFFFFFFFFFFFFCULL;  // RE 0x90D6EA
inline constexpr std::size_t kVector4MinCapacity = 4;               // RE 0x90D6F3
inline constexpr int kVector4Callers = 23;
static_assert((1u << kElement4Shift) == kElement4, "the shift is the element size");
static_assert(kVector4Failure == static_cast<std::uint64_t>(-4), "the failure value is minus the element size");
// The max_size here equals the two-byte string's guard. Equal VALUES, recorded as equal rather than merged.
static_assert(kMaxSizeVec64 == kMaxSizeWide, "the same max_size constant as the two-byte string");
static_assert(kVector4 != kVector32, "two distinct vector growth routines");


// --- the chain walk inside the BER reader 0x11A780 (round 282) ------------------------------------------
//     0x11A7F5/0x11A80A/0x11A829/0x11A859  call qword [rax+0x158]   ; the STEP, four call sites from unrolling
//     0x11A7FB/0x11A832/0x11A862           test rax,rax ; je       ; a null step ends the walk
//     0x11A816/0x11A84A                    r8 = [rax+0xC0] ; cmp r8,rsi ; jne
//     0x11A792 (round 281)                 rsi came from [vtable+0xC0] at entry
inline constexpr std::size_t kVtableSlotStep = 0x158;        // RE 0x11A7F5
inline constexpr std::size_t kChainTypeField = 0xC0;         // RE 0x11A816, compared per node
inline constexpr int kChainUnroll = 3;                       // RE the three repeated blocks
inline constexpr int kVtableSlotsKnown2 = 7;                 // 0x08, 0x18, 0x30, 0x68, 0xB8, 0xC0 and 0x158
inline constexpr std::uintptr_t kChainMismatchBranch = 0x11A8B0;   // RE 0x11A820/0x11A854
inline constexpr std::uintptr_t kChainNullBranch = 0x11A932;       // RE 0x11A7FE
inline constexpr int kBerLengthCallers2 = 9;
static_assert(kChainUnroll == 3, "the compiler unrolled the walk three times");
static_assert(kVtableSlotsKnown2 == kVtableSlotsKnown + 1, "one more slot than round 281 recorded");
static_assert(kChainTypeField == kBerVtableSlotB, "the compared field is the slot loaded at entry");


// --- the branch bodies of 0x11A780, and a correction (round 283) ---------------------------------------
//     0x11A8B0/0x11A8D0  both branches are `mov rdx,rbp ; mov rcx,rbx ; call r8` / `call rsi`, i.e. a TAIL CALL with
//                        the object and the value as its two arguments
//     0x11A8D6 call rsi  ; rsi is what round 281 read from [vtable+0xC0]
//     0x11A8E5 movzx eax,byte [rip+0xA06744] ; test ; je   ; a GLOBAL flag gates the next call
//     0x11A91A call qword [rax+0x110] with a stack out-parameter, 1, and two addresses
inline constexpr bool kSlotIsCalled = true;                  // RE 0x11A8D6
inline constexpr int kChainBranchArgs = 2;                   // RE rcx and rdx before the call
inline constexpr std::size_t kVtableSlotE = 0x110;           // RE 0x11A91A -- an eighth slot
inline constexpr int kVtableSlotsKnown3 = 8;                 // 0x08, 0x18, 0x30, 0x68, 0xB8, 0xC0, 0x110, 0x158
inline constexpr std::uintptr_t kGlobalGateRva = 0xA06744;   // RE 0x11A8E5, a byte in the data section
inline constexpr std::uintptr_t kGateArgA = 0xA066ED;        // RE 0x11A90C
inline constexpr std::uintptr_t kGateArgB = 0xA06726;        // RE 0x11A913
inline constexpr int kGateConstant = 1;                      // RE 0x11A904 (dword 1 on the stack)
// CORRECTION: round 282 described +0xC0 as "a compared field". It is compared per node AND it is CALLED here, so the
// slot holds a function pointer. The earlier wording was true but incomplete and is corrected rather than left.
inline constexpr bool kSlotBothComparedAndCalled = true;
static_assert(kVtableSlotsKnown3 == kVtableSlotsKnown2 + 1, "one more slot than round 282");
static_assert(kChainBranchArgs == 2, "two arguments precede the tail call");


// --- the guarded call pattern inside 0x11A780, at FOUR sites (round 284) --------------------------------
//     0x11A8E5/0x11A932/0x11A980  each site reads its OWN global byte and skips the call when it is clear
//     0x11A91A/0x11A965/0x11A9B5  call qword [rax+0x110], the same slot from every site
//     0x11A9CC call 0x998DA0 with an address, then re-enters the guarded call when it succeeds
// Each guarded call passes the value, a register or stack out-parameter, the constant 1, and TWO data addresses.
inline constexpr std::size_t kGateCallSlot = 0x110;          // RE the four call sites
inline constexpr int kGateSites = 4;                         // RE the four guards
inline constexpr int kGateBytesRead = 3;                     // the fourth branch was not dumped
inline constexpr std::uintptr_t kGateByteA = 0xA06744;       // RE 0x11A8E5
inline constexpr std::uintptr_t kGateByteB = 0xA066F7;       // RE 0x11A932
inline constexpr std::uintptr_t kGateByteC = 0xA066A9;       // RE 0x11A980
inline constexpr std::uintptr_t kGateInitAddress = 0xA06664;  // RE 0x11A9C5
inline constexpr std::uintptr_t kGateInit = 0x998DA0;        // RE 0x11A9CC
inline constexpr int kGateArgsPerSite = 2;                   // RE the r9/rdx pair at every site
inline constexpr int kGateConstant2 = 1;                     // RE the dword 1 pushed at every site
// The FOURTH gate byte's address is NOT recorded: its branch (0x11AA20 and 0x11AA80) was not dumped, so it stays
// unread rather than guessed. That is why kGateBytesRead is three and not four.
inline constexpr bool kFourthGateByteUnread = true;
static_assert(kGateBytesRead == 3 && kGateSites == 4, "three of four gate bytes are read");
static_assert(kGateCallSlot == kVtableSlotE, "the guarded slot is the eighth one");
static_assert(kGateConstant2 == kGateConstant, "the same constant at every site");


// --- the second status reader 0x111A50, and the BER reader's caller profile (round 285) -----------------
//     0x111A54/0x111A58  the flags at +0x29 and +0x28, exactly as 0x10F770 uses them
//     0x111A5E           the pointer at +0x30
//     0x111A70           the source at +0x20
//     0x111A74/0x111A79/0x111A7F  the out buffer at rsp+0x2E, r8d = 1, and the call to the BER reader
//     0x111A84/0x111A8A/0x111A90  status 2, the BER formatter, and the retry while the word is non-zero
inline constexpr std::uintptr_t kStatusReaderB = 0x111A50;   // RE the whole routine
inline constexpr int kStatusReaderBbytes = 74;               // RE the function size
inline constexpr int kStatusReaderFamily = 2;                // 0x10F770 and 0x111A50
inline constexpr std::size_t kStatusOutOffset = 0x2E;        // RE 0x111A74 and 0x10F7B4 alike
inline constexpr std::int32_t kStatusExpected2 = 2;          // RE 0x111A84
inline constexpr std::uintptr_t kBerReaderCaller = 0x11A780; // RE 0x111A7F
inline constexpr int kBerReaderCallers = 9;                  // RE the profile
inline constexpr int kStatusReadersAmongCallers = 2;         // two of the nine carry this shape
static_assert(kStatusReaderFamily == kStatusReadersAmongCallers, "the family is what the callers show");
static_assert(kStatusExpected2 == kStatusExpected, "the same status as round 280");
static_assert(kStatusOutOffset == 0x2E, "the out buffer is a sixteen-bit word");
// The two readers share every field offset, which is what makes them a family rather than a coincidence.
static_assert(kFinaliseFlagA == 0x28 && kFinaliseFlagB == 0x29 && kFinalisePointer == 0x30,
              "round 280's offsets for the same object");


// --- the third status reader, which is also the destructor, 0x10F810 (round 286) -----------------------
//     0x10F81C cmp byte [rcx+0x28],0 ; je        ; the family's flag
//     0x10F836 call 0x9984B0                     ; SET: the object is deallocated here
//     0x10F846 byte [rcx+0x28] = 1 ; 0x10F842 cmp byte [rcx+0x29],0
//     0x10F84C/0x10F853  the +0x30 pointer and the BER formatter
//     0x10F860/0x10F869/0x10F86F  +0x20, rsp+0x2E, r8d = 1 and the call to the BER reader
inline constexpr std::uintptr_t kStatusReaderC = 0x10F810;   // RE the whole routine
inline constexpr int kStatusReaderCbytes = 153;              // RE the function size
inline constexpr int kStatusReaderFamily2 = 3;               // 0x10F770, 0x111A50 and this
inline constexpr bool kFinalisedFlagFrees = true;            // RE 0x10F81C/0x10F836
inline constexpr bool kReaderIsDestructor = true;            // RE the two vtables at 0x10F820/0x10F82D
inline constexpr int kStatusReaderCDirectCallers = 0;        // reached through a vtable
static_assert(kStatusReaderFamily2 == 3, "three members share the four offsets");
static_assert(kFinalisedFlagFrees, "a set flag means the object is freed");

// --- the bit-to-byte conversion 0xF7B90 (round 286) -----------------------------------------------------
//     0xF7BAA call 0x11A780 with the out word at rsp+0x2E
//     0xF7BEC movzx r8d,word [rsp+0x2E] ; 0xF7BF2 add r8,7 ; 0xF7BF6 shr r8,3
//     `(v + 7) >> 3` is ceil(v / 8): the bits of the BER value expressed in bytes.
inline constexpr std::uintptr_t kBerByteCount = 0xF7B90;     // RE the whole routine
inline constexpr int kBitToByteAddend = 7;                   // RE 0xF7BF2
inline constexpr int kBitToByteShift = 3;                    // RE 0xF7BF6
inline constexpr std::uintptr_t kBitToByteCtor = 0x7B0160;   // RE 0xF7BC5
inline constexpr std::size_t kBitToByteAlloc = 0x30;         // RE 0xF7BB5
inline constexpr std::size_t kVtableSlotF = 0x90;            // RE 0xF7BE6 -- a NINTH slot
inline constexpr int kVtableSlotsKnown4 = 9;                 // with 0x90 added to the eight of round 284
inline constexpr std::uintptr_t kThrowSite = 0x999030;       // RE 0xF7BDB, the shared throw helper
static_assert((1 << kBitToByteShift) == 8, "the shift is the byte size");
static_assert(kVtableSlotsKnown4 == kVtableSlotsKnown3 + 1, "one more slot than round 284");
static_assert(kBitToByteAddend == 7, "ceil is add-seven");


// --- the second bit-to-byte site, used as a length check, 0xF7470 (round 287) --------------------------
//     0xF7481 call 0x77A460       ; a temporary is built at rsp+0x30
//     0xF7494 call 0x11A780       ; the sixteen-bit value, into rsp+0x2E
//     0xF74D3 call 0x1186C0       ; a size comes back in rax
//     0xF74DE/0xF74E2 (v + 7) >> 3 ; the SAME ceiling as 0xF7B90
//     0xF74E6 cmp rax,r8 ; jb 0xF749F   ; the size must be at least that, or the throw path runs
inline constexpr std::uintptr_t kBerValidate = 0xF7470;      // RE the whole routine
inline constexpr int kBitToByteSites = 2;                    // 0xF7B90 and 0xF7470
inline constexpr std::uintptr_t kValidateHelper = 0x77A460;  // RE 0xF7481
inline constexpr std::uintptr_t kSizeCall = 0x1186C0;        // RE 0xF74D3
inline constexpr bool kLengthCheckThrows = true;             // RE 0xF74E6/0xF74E9
inline constexpr int kBerValidateCallers = 0;                // reached through a vtable
static_assert(kBitToByteSites == 2, "the ceiling has two sites");
static_assert(kLengthCheckThrows, "the check diverts to the throw path");

// --- the constructor with an inline buffer 0x6DE430, twenty-three callers (round 287) -------------------
//     0x6DE456 [rsi+0x20] = rsi+0x30   ; the inline buffer and what it points at
//     0x6DE44E dword [rsi+0x10] = edi  ; a 32-bit field
//     0x6DE461 [rsi+0x18] = rbx        ; a pointer or length taken from the argument struct
//     0x6DE471 [rsi] = a vtable (rva 0x35D94F)
//     0x6DE484 mov ecx,0x60 ; call 0x998500   ; a ninety-six byte allocation
inline constexpr std::uintptr_t kCtor96 = 0x6DE430;          // RE the whole routine
inline constexpr std::uintptr_t kCtor96VtableRva = 0x35D94F; // RE 0x6DE45A
inline constexpr std::size_t kCtor96Dword = 0x10;            // RE 0x6DE44E
inline constexpr std::size_t kCtor96Pointer = 0x18;          // RE 0x6DE461
inline constexpr std::size_t kCtor96Inline = 0x20;           // RE 0x6DE456
inline constexpr std::size_t kCtor96InlineTarget = 0x30;     // RE 0x6DE44A
inline constexpr std::size_t kAlloc60 = 0x60;                // RE 0x6DE451 (96)
inline constexpr int kCtor96Callers = 23;
inline constexpr int kAllocatorSightings = 5;                // rounds 252, 256, 271, and the two here
inline constexpr std::uintptr_t kCtor96Helper = 0x888FA0;    // RE 0x6DE445
static_assert(kAlloc60 == 96, "ninety-six bytes");
static_assert(kCtor96InlineTarget > kCtor96Inline, "the inline buffer points forward");
static_assert(kAlloc60 > kGetOrCreateBytes, "larger than the forty-eight byte object");


// --- the InputBuffer object constructor 0x77A460, six callers (round 288) ------------------------------
//     0x77A488 dword [rbx+0x14] = 0xFFFFFFFF   ; a -1 marker
//     0x77A498 byte [rbx+0x18] = 0
//     0x77A4B5 [rbx]   = rax + 0x10            ; one pointer from a global descriptor
//     0x77A4BF [rbx+8] = rax + 0x1A0           ; another, 0x190 further into it
//     0x77A4B8 lea rdx,[rip+0x23C577]          ; the literal 'InputBuffer'
inline constexpr std::uintptr_t kInputBufferCtor = 0x77A460;  // RE the whole routine
inline constexpr std::uintptr_t kInputBufferRva = 0x23C577;   // RE the literal
inline constexpr std::size_t kInputBufferMarker = 0x14;       // RE 0x77A488
inline constexpr std::uint32_t kInputBufferMarkerValue = 0xFFFFFFFFu;  // RE the -1 marker
inline constexpr std::size_t kInputBufferByte = 0x18;         // RE 0x77A498
inline constexpr std::size_t kInputBufferPtrA = 0x00;         // RE 0x77A4B5
inline constexpr std::size_t kInputBufferPtrB = 0x08;         // RE 0x77A4BF
inline constexpr std::uintptr_t kInputBufferDescriptorRva = 0x28DF88;  // RE 0x77A481
inline constexpr int kInputBufferPtrOffsets = 2;              // the two descriptor offsets
inline constexpr int kInputBufferCallers = 6;
inline constexpr std::uintptr_t kInputBufferHelper = 0x118260;  // RE 0x77A472
static_assert(kInputBufferMarkerValue == 0xFFFFFFFFu, "the marker is -1");
static_assert(kInputBufferPtrB > kInputBufferPtrA, "the second pointer follows the first");

// --- the size accessor 0x1186C0 and a tenth vtable slot (round 288) -------------------------------------
//     0x1186CB/0x1186DC call qword [rax+0x160]   ; slot 0x160, called twice
//     0x1186E8 call qword [rdx+0x90]             ; then the slot of round 286
//     0x1186F4/0x1186FB  a global gate byte and r9 = -1 with dword 1 -- the guarded shape again
inline constexpr std::uintptr_t kSizeAccessor = 0x1186C0;     // RE the whole routine
inline constexpr std::size_t kVtableSlotG = 0x160;            // RE 0x1186CB
inline constexpr int kVtableSlotsKnown5 = 10;                 // the nine of round 286 plus 0x160
inline constexpr std::uintptr_t kSizeAccessorGateRva = 0xA08935;  // RE 0x1186F4
inline constexpr std::int64_t kSizeAccessorSentinel = -1;     // RE 0x118722
inline constexpr int kGuardPatternSightings = 3;              // rounds 283/284 and this one
inline constexpr int kSizeAccessorCallers = 6;
// OPEN QUESTION, recorded rather than settled: 0x77A460 calls 0x118260, which an earlier round registered as a
// CryptoPP self-test. A routine that builds an object carrying 'InputBuffer' is domain code, so either that
// registration is wrong in this context or 0x118260 is a general helper. NOT decided here.
inline constexpr bool kHelperClassificationOpen = false;   // CLOSED in round 289: it is CryptoPP
// Round 288 left this open because domain code calls 0x118260. Reading that function settles it: it references
// CryptoPP's own power-up self-test text, so the library registration stands. What the case actually teaches is
// recorded as a rule below: a domain caller does not reclassify its library callee.
static_assert(kVtableSlotsKnown5 == kVtableSlotsKnown4 + 1, "one more slot than round 286");
static_assert(kGuardPatternSightings == 3, "three sightings of the guarded shape");


// --- the CryptoPP self-test, whose classification is now settled (round 289) ---------------------------
//     0x118267/0x118270  a vtable-ish pointer at [rcx]
//     0x11826E test dl,dl ; jne          ; the flag argument
//     0x118280 call 0xD5970 ; test al    ; a probe
//     0x118289/0x118292 call 0xD5990 ; cmp eax,1   ; the status, where ONE means disabled
//     0x1182A6 call 0x9988C0 with ecx = 0x30 and 0x1171F0, then a throw with the messages below
//     0x1182AB/... the two literals are CryptoPP's power-up self-test text
inline constexpr std::uintptr_t kCryptoPpSelfTest = 0x118260;   // RE the whole routine
inline constexpr std::uintptr_t kSelfTestProbe = 0xD5970;       // RE 0x118280
inline constexpr std::uintptr_t kSelfTestStatus = 0xD5990;      // RE 0x118289
inline constexpr std::int32_t kSelfTestStatusDisabled = 1;      // RE 0x118297
inline constexpr std::uintptr_t kSelfTestTextA = 0x89F8E6;      // RE 0x1182AB, 'after a power-up self test failed'
inline constexpr std::uintptr_t kSelfTestCtor = 0x1171F0;       // RE 0x1182B8
inline constexpr std::size_t kSelfTestAlloc = 0x30;             // RE 0x1182A1
inline constexpr int kSelfTestCallers = 169;                    // RE the profile
// THE RULE this case produced, which governs how the exclusion lists must be read:
// a DOMAIN function calling a LIBRARY function does not make the library function domain code, and it does not make
// the caller library code either. The two classifications are independent.
inline constexpr bool kDomainCallingLibraryStaysDomain = true;
static_assert(kSelfTestStatusDisabled == 1, "the disabled status is one");
static_assert(!kHelperClassificationOpen, "the classification is settled");
static_assert(kSelfTestCallers > kBerReaderCallers, "the self-test is called far more widely");


// --- the triple-buffer record 0x6DE430 allocates (round 290) -------------------------------------------
//     0x6DE49F [rbx] = rbx+0x10 ; 0x6DE4AC [rbx+0x20] = rbx+0x30 ; 0x6DE4C0 [rbx+0x40] = rbx+0x50
//     0x6DE4A4/0x6DE4BC/0x6DE4CC  a zero word at each buffer's start
//     0x6DE4D9/0x6DE4E7/0x6DE4EE  the record's own links, with two dwords set to ONE
//     0x6DE4E0 a vtable from rva 0x35E739 at +0x00
inline constexpr std::size_t kInlineBufferA = 0x10;          // RE 0x6DE49F
inline constexpr std::size_t kInlineBufferB = 0x20;          // RE 0x6DE4AC
inline constexpr std::size_t kInlineBufferC = 0x40;          // RE 0x6DE4C0
inline constexpr std::size_t kInlineTargetA = 0x20;          // RE 0x6DE49F's target
inline constexpr std::size_t kInlineTargetB = 0x30;          // RE 0x6DE4AC's target
inline constexpr std::size_t kInlineTargetC = 0x50;          // RE 0x6DE4C0's target
inline constexpr int kInlineBufferPairs = 3;                 // RE the three pairs
inline constexpr std::size_t kRecordVtable = 0x00;           // RE 0x6DE4F5
inline constexpr std::size_t kRecordWordA = 0x08;            // RE 0x6DE4E7
inline constexpr std::size_t kRecordWordB = 0x0C;            // RE 0x6DE4EE
inline constexpr std::uintptr_t kRecordVtableRva = 0x35E739; // RE 0x6DE4E0
inline constexpr std::size_t kRecordBytes = 0x60;            // RE 0x6DE4D0
static_assert(kInlineBufferPairs == 3, "three inline buffers");
static_assert(kInlineBufferB - kInlineBufferA == 0x10, "the first pair is sixteen bytes apart");
static_assert(kInlineTargetC - kInlineTargetB == 0x20, "the third target follows the second by 0x20");
static_assert(kRecordWordB - kRecordWordA == 4, "the two one-valued dwords are adjacent");

// --- the copy assignment 0x418BD0, twenty-five callers (round 290) -------------------------------------
//     0x418BDE cmp rcx,rdx ; je 0x418C97   ; a self-check, as an assignment should have
//     0x418BED/0x418BF8  the 32-bit field at +0x04 copied
//     0x418BFB call 0x63F258                ; a helper 0x20 above the length helper of round 251
//     0x418C00 edx = [rbx+0x14]             ; the field round 249 recorded
inline constexpr std::uintptr_t kCopyAssign = 0x418BD0;      // RE the whole routine
inline constexpr std::size_t kCopyField = 0x04;              // RE 0x418BED
inline constexpr std::size_t kCopyCapacity = 0x14;           // RE 0x418C00
inline constexpr std::uintptr_t kCopyHelper = 0x63F258;      // RE 0x418BFB
inline constexpr std::size_t kHelperClusterStep = 0x20;      // RE 0x63F258 - 0x63F238
inline constexpr int kCopyAssignCallers = 25;
inline constexpr std::uintptr_t kHelperClusterBase = 0x63F238;  // the length helper of round 251
static_assert(kCopyHelper == kHelperClusterBase + kHelperClusterStep, "the helper sits one step into the cluster");
static_assert(kCopyCapacity == kSsoCapacity, "the field round 249 recorded as the capacity");


// --- the small-object layout PROVEN by the copy assignment 0x418BD0 (round 291) -------------------------
//     0x418C00/0x418C0B  the field at +0x14 is tested with `js`: it is SIGNED, which is what a capacity is
//     0x418C2D  the source's +0x14 is copied into it
//     0x418C43/0x418C49  that capacity is passed to the allocator 0x9984E0
//     0x418C11/0x418C1D  the old buffer at +0x18 is released with 0x9984A0
//     0x418C31  a sign-extended dword from the source goes to +0x00
inline constexpr bool kSsoConfirmed = true;                  // the round-249 layout, now on evidence
inline constexpr std::size_t kSsoField00 = 0x00;             // RE 0x418C31, a signed dword
inline constexpr std::size_t kSsoField04 = 0x04;             // RE 0x418BF8
inline constexpr std::size_t kSsoField10 = 0x10;             // RE 0x418C08
inline constexpr std::size_t kSsoField14 = 0x14;             // RE 0x418C2D, the signed capacity
inline constexpr std::size_t kSsoField18 = 0x18;             // RE 0x418C11, the buffer
inline constexpr std::uintptr_t kSsoAlloc = 0x9984E0;        // RE 0x418C49
inline constexpr int kReleaserAltSightings = 3;              // UPDATED in round 321: rounds 260, 291 and the
// destructor at 0x4B32F0, which tail calls 0x9984A0 with the field at +0x18
inline constexpr int kCopyAssignCallers2 = 25;
static_assert(kSsoField14 == kSsoCapacity, "the capacity round 249 inferred");
static_assert(kSsoField18 == kSsoData, "the data pointer round 249 inferred");
static_assert(kSsoConfirmed && !kSsoInference, "the layout moved from inference to evidence");

// --- the record's dual counters and an eleventh vtable slot (round 291) ---------------------------------
//     0x6DE505 lock sub dword [rdi+8],1   ; one counter, decremented atomically
//     0x6DE52B lock sub dword [rdi+0xC],1 ; and a second, four bytes later
//     0x6DE528 call qword [rax+0x10]      ; the release path goes through vtable slot +0x10
//     0x6DE4FB/0x6DE4FF  the record is linked into the outer object at +0x40 and +0x48
inline constexpr std::size_t kRecordCounterA = 0x08;         // RE 0x6DE505
inline constexpr std::size_t kRecordCounterB = 0x0C;         // RE 0x6DE52B
inline constexpr int kRecordCounters = 2;                    // RE the two atomic decrements
inline constexpr std::size_t kRecordLinkA = 0x40;            // RE 0x6DE4FB
inline constexpr std::size_t kRecordLinkB = 0x48;            // RE 0x6DE4FF
inline constexpr std::size_t kVtableSlotH = 0x10;            // RE 0x6DE528 -- an ELEVENTH slot
inline constexpr int kVtableSlotsKnown6 = 11;                // with 0x10 added to the ten of round 288
inline constexpr std::uintptr_t kRecordFinalCall = 0x9135D0; // RE 0x6DE513
inline constexpr bool kRecordCountedTwice = true;            // RE the 1/1 pair and the two decrements
static_assert(kRecordCounters == 2, "two counters");
static_assert(kRecordCounterB - kRecordCounterA == 4, "the counters are adjacent dwords");
static_assert(kVtableSlotsKnown6 == kVtableSlotsKnown5 + 1, "one more slot than round 288");
static_assert(kRecordCountedTwice, "the record is counted twice over");


// --- the deep copy of a pointer array 0x418BD0, and the 408-byte record (round 292) ---------------------
//     0x418CB9 movabs rax,0xFFFFFFFFFFFFFFF ; 0x418CC6 ja   ; the max_size guard, 2**60 - 1
//     0x418CCC lea rcx,[r10*8]      ; the count times EIGHT: an array of POINTERS
//     0x418CD4 call 0x9984E0        ; allocated, and stored at +0x18 (where round 291 found the buffer)
//     0x418CF3 mov ecx,0x198        ; each pointed-to record is 408 bytes
//     0x418D19 [rdi] = [r12]        ; the dword at +0x00
//     0x418D1B call 0x63F258 from +6 ; the payload
//     0x418D26/0x418D29             ; the bytes at +0x05 and +0x04
inline constexpr std::size_t kElementBytes198 = 0x198;       // RE 0x418CF3 (408)
inline constexpr std::uint64_t kPointerMaxCount = 0xFFFFFFFFFFFFFFFULL;  // RE 0x418CB9, 2**60 - 1
inline constexpr bool kVectorOfPointers = true;              // RE the `*8` scaling
inline constexpr std::size_t kRecordHeaderBytes = 6;         // RE the payload offset used by 0x63F258
inline constexpr std::size_t kRecordDword = 0x00;            // RE 0x418D19
inline constexpr std::size_t kRecordByteA = 0x04;            // RE 0x418D29
inline constexpr std::size_t kRecordByteB = 0x05;            // RE 0x418D26
inline constexpr std::size_t kRecordPayload = 0x06;          // RE 0x418D1B
inline constexpr std::uintptr_t kPayloadCopier = 0x63F258;   // RE 0x418D1B, also round 290
inline constexpr int kPayloadCopierSightings = 2;            // rounds 290 and this one
inline constexpr std::size_t kOuterCount = 0x00;             // RE 0x418CDD
inline constexpr std::size_t kOuterArray = 0x18;             // RE 0x418CD9
static_assert(kPointerMaxCount == (1ULL << 60) - 1, "the max count is 2**60 - 1");
static_assert(kRecordByteB - kRecordByteA == 1, "the two header bytes are adjacent");
static_assert(kRecordPayload == kRecordByteB + 1, "the payload starts right after the header");
static_assert(kElementBytes198 == 408, "four hundred and eight bytes per record");
static_assert(kPayloadCopierSightings == 2, "the payload copier has two sightings");


// --- the array teardown inside 0x418BD0, which confirms the pointer array (round 293) ------------------
//     0x418D7A rax = [rbx+0x18]                     ; the array
//     0x418D8B call 0x9984B0                        ; each non-null element is freed
//     0x418D99 add rdi,8                            ; EIGHT-byte stride
//     0x418DA1 jmp 0x418C15                         ; then the assignment carries on
inline constexpr std::size_t kArrayStride = 8;               // RE 0x418D99
inline constexpr bool kArrayElementsFreed = true;            // RE 0x418D8B
inline constexpr std::uintptr_t kArrayFreeCallee = 0x9984B0; // RE 0x418D8B, the shared deallocator
inline constexpr int kSharedDeallocSightings5 = 7;           // rounds 248, 252, 254, 256, 261, 275 and this
inline constexpr int kArrayFreeLoopCallers = 25;
static_assert(kArrayStride == 8, "the pointers are eight bytes");
static_assert(kArrayFreeCallee == kSharedDealloc, "the widely shared deallocator");
static_assert(kSharedDeallocSightings5 == kSharedDeallocSightings4 + 1, "one more sighting");

// --- the string assignment 0x9135D0, thirty-two callers (round 293) -------------------------------------
//     0x9135DA cmp rcx,rdx ; je       ; a self-check
//     0x9135E5 rdi = [rcx]            ; the data pointer
//     0x9135E8 r12 = rcx+0x10         ; the inline buffer
//     0x9135F0 cmp r12,rdi ; je       ; THE SSO CHECK
//     0x9135F9 r8 = [rcx+0x10]        ; the capacity
inline constexpr std::uintptr_t kStringAssign = 0x9135D0;    // RE the whole routine
inline constexpr std::size_t kStringAssignData = 0x00;       // RE 0x9135E5
inline constexpr std::size_t kStringAssignSize = 0x08;       // RE 0x9135EC
inline constexpr std::size_t kStringAssignCapacity = 0x10;   // RE 0x9135F9
inline constexpr int kStringAssignCallers = 32;
inline constexpr bool kStringAssignSsoCheck = true;          // RE 0x9135F0
inline constexpr std::uintptr_t kStringAssignInlineBranch = 0x913684;  // RE 0x9135F3
static_assert(kStringAssignData == kWideData && kStringAssignSize == kWideSize &&
              kStringAssignCapacity == kWideCapacity, "the trio round 262 recorded");
static_assert(kStringAssignSsoCheck, "the assignment compares the inline address with the data pointer");


// --- the small capacity of the string type, and the release rule (round 294) ---------------------------
//     0x913684 mov r8d,7 ; 0x91368A jmp   ; the capacity used when the source is inline
//     0x913600 jb                          ; capacity < size therefore reallocate
//     0x913658/0x91365B  the old data pointer against the inline address, and `je` skips the free
//     0x91365D call 0x9984B0               ; freed only when it is NOT the inline buffer
//     0x913670 lea r12,[rsi+rsi]           ; growth doubles
inline constexpr std::size_t kSmallCapacity = 7;             // RE 0x913684
inline constexpr std::uintptr_t kStringRealloc = 0x913640;   // RE the reallocation branch
inline constexpr std::uintptr_t kStringAllocBySize = 0x913690;  // RE 0x91364D
inline constexpr bool kFreeOnlyIfHeap = true;                // RE 0x913658/0x91365B
inline constexpr bool kGrowthDoubling = true;                // RE 0x913670
inline constexpr std::size_t kStringInlineCapacity = 7;      // the same number, named for the rule
inline constexpr int kSharedDeallocSightings6 = 8;           // rounds 248, 252, 254, 256, 261, 275, 293 and this
inline constexpr int kStringAssignDouble = 2;                // the factor from `lea r12,[rsi+rsi]`
static_assert(kSmallCapacity == kStringInlineCapacity, "one capacity, one name for the rule");
static_assert(kSmallCapacity == 7, "seven bytes inline");
static_assert(kStringAssignDouble == 2, "the growth factor is two");
static_assert(kSharedDeallocSightings6 == kSharedDeallocSightings5 + 1, "one more sighting");
static_assert(kSmallCapacity < kSsoInline, "the capacity is smaller than the inline buffer offset");


// --- the growth-policy helper 0x913690, forty-eight callers (round 295) ---------------------------------
//     0x913694 movabs rax,0x3FFFFFFFFFFFFFFF   ; the max_size, the same 2**62 - 1 as rounds 262 and 281
//     0x91369E rcx = [rdx]                     ; the capacity is passed in AND out through the pointer
//     0x9136AB/0x9136AF  add rcx,1 then a sign check
//     0x9136B1 add rcx,rcx                     ; the new capacity is 2 * (capacity + 1)
//     0x9136C0/0x9136C3  or twice the REQUEST when the capacity is at or below it
//     0x9136CD movabs rcx,0x8000000000000000   ; the clamp sentinel
//     0x9136B8/0x9136DE jmp 0x998500           ; the shared allocator performs the allocation
//     0x9136EB call 0x979E70                   ; the overflow path
inline constexpr std::uintptr_t kGrowthHelper = 0x913690;    // RE the whole routine
inline constexpr std::uint64_t kMaxSizeShared = 0x3FFFFFFFFFFFFFFFULL;  // RE 0x913694
inline constexpr std::uint64_t kCapacitySentinel = 0x8000000000000000ULL;  // RE 0x9136CD
inline constexpr int kGrowthHelperCallers = 48;
inline constexpr bool kGrowthRulePlusOneDouble = true;       // RE 0x9136AB/0x9136B1
inline constexpr bool kGrowthPrefersDoublingCapacity = true; // RE the branch order
inline constexpr std::uintptr_t kOverflowHelper = 0x979E70;  // RE 0x9136EB
inline constexpr std::uintptr_t kGrowthAllocator = 0x998500; // RE 0x9136B8
inline constexpr int kAllocatorSightings2 = 6;               // rounds 252, 256, 271, 287 and the two here
static_assert(kMaxSizeShared == kMaxSizeWide, "the same max_size as the two-byte string");
static_assert(kMaxSizeShared == kMaxSizeVec64, "and as the four-byte vector");
static_assert(kGrowthRulePlusOneDouble, "the rule adds one and doubles");
static_assert(kGrowthHelperCallers == 48, "forty-eight callers");


// --- the length-error thrower 0x979E70, six hundred and seventy-six callers (round 296) -----------------
//     0x979E74 mov ecx,8 ; 0x979E79 call 0x9988C0   ; an eight byte object: ONE POINTER to the type
//     0x979E8C/0x979E93  the global's +0x10 installed on it as a vtable
//     0x979E85 lea r8,[rip-0x34B5C]                 ; a type descriptor
//     0x979E9D call 0x999030                        ; the shared throw helper
inline constexpr std::uintptr_t kThrowLengthError = 0x979E70;      // RE the whole routine
inline constexpr std::size_t kLengthErrorObjectBytes = 8;          // RE 0x979E74
inline constexpr std::uintptr_t kLengthErrorTypeRva = 0x8EF3B;     // RE 0x979E7E, the global holding the type
inline constexpr std::size_t kLengthErrorTypeOffset = 0x10;        // RE 0x979E8C
inline constexpr std::uintptr_t kLengthErrorArgumentRva = 0xA7003; // RE 0x979E96
inline constexpr std::uintptr_t kLengthErrorDescriptor = 0x979E85; // RE the lea at that address
inline constexpr int kThrowLengthErrorCallers = 676;               // RE the profile
inline constexpr int kThrowHelperSightings = 5;                    // rounds 271, 280, 286, 287 and this
inline constexpr int kAllocatorSightings3 = 4;                     // 0x9988C0 through this path as well
// The identification above rests on the SHAPE (one size_t carried, a type out of a global, a bare throw) and not on
// any string. That is weaker than the CryptoPP case of round 289, which had its own text, and the flag says so.
inline constexpr bool kLengthErrorShapeOnly = true;
static_assert(kLengthErrorObjectBytes == sizeof(void*), "the object holds one pointer, the type");
static_assert(kThrowHelperSightings == 5, "the shared throw helper again");
static_assert(kLengthErrorShapeOnly, "the identification is shape-based, and recorded as such");


// --- the C++ runtime's throw entry point 0x999030, four hundred and seventy-six callers (round 297) ------
//     0x99906E movabs rax,0x474E5543432B2B00   ; 'G','N','U','C','C','+','+',NUL -- the GCC C++ ABI string
//     0x999078 mov qword [rbx],rax             ; written at the exception's head
//     0x999040 call 0x998CB0                   ; the per-thread globals
//     0x999049 add dword [rax+8],1             ; the uncaught counter, incremented
//     0x999045 sub rbx,0x40                    ; the header sits forty bytes before the object pointer
//     0x99905C/0x999065 call 0x963560, 0x962F10  ; type lookups
inline constexpr std::uintptr_t kCxaThrow = 0x999030;        // RE the whole routine
inline constexpr std::uint64_t kCxaMagic = 0x474E5543432B2B00ULL;  // RE 0x99906E
inline constexpr std::size_t kCxaHeaderOffset = 0x40;        // RE 0x999045
inline constexpr std::size_t kUncaughtOffset = 0x08;         // RE 0x999049
inline constexpr std::uintptr_t kCxaGlobals = 0x998CB0;      // RE 0x999040
inline constexpr std::uintptr_t kCxaTypeLookupA = 0x963560;  // RE 0x99905C
inline constexpr std::uintptr_t kCxaTypeLookupB = 0x962F10;  // RE 0x999065
inline constexpr int kCxaThrowCallers = 476;                 // RE the profile
inline constexpr std::size_t kCxaFieldOffset = 0x60;         // RE 0x99904D (rbx - 0x60)
inline constexpr bool kCxaIdentifiedByString = true;         // the ABI string, not a shape
static_assert(kCxaMagic == 0x474E5543432B2B00ULL, "the ABI magic as the immediate spells it");
static_assert(kCxaHeaderOffset == 0x40, "the header is forty bytes before the object");
static_assert(kCxaIdentifiedByString, "identified by its own ABI text");
static_assert(kCxaThrowCallers == 476, "four hundred and seventy-six throw sites");


// --- the in-place InputBuffer and the self-test gate, from 0x10FD40 (round 298) -------------------------
//     0x10FD61 rsi = rsp+0x60                   ; the object, built on the stack
//     0x10FD8C call 0x118260 with edx = 0       ; the CryptoPP self-test, called FIRST
//     0x10FD9C/0x10FD94/0x10FDB1  the fields at 0x74, 0x78 and 0x80
//     0x10FDC1 call qword [rax+0xA0]            ; a twelfth vtable slot
inline constexpr std::size_t kInputBufferLocal = 0x60;       // RE 0x10FD61
inline constexpr std::size_t kInputBufferLocalMarker = 0x74; // RE 0x10FD9C -- 0x14 relative
inline constexpr std::size_t kInputBufferLocalByte = 0x78;   // RE 0x10FD94 -- 0x18 relative
inline constexpr std::size_t kInputBufferLocalLink = 0x80;   // RE 0x10FDB1 -- 0x20 relative
inline constexpr bool kInputBufferInPlace = true;            // the same object, three constructions
inline constexpr bool kSelfTestFirst = true;                 // RE 0x10FD8C, before any other work
inline constexpr std::int32_t kSelfTestArgument = 0;         // RE 0x10FD7B (edx zero)
inline constexpr std::uintptr_t kFlagProbe = 0x1170B0;       // RE 0x10FD71, writes a byte
inline constexpr std::size_t kVtableSlotI = 0xA0;            // RE 0x10FDC1 -- a TWELFTH slot
inline constexpr int kVtableSlotsKnown7 = 12;                // with 0xA0 added to the eleven of round 291
inline constexpr int kDriverCallers = 1;
static_assert(kInputBufferLocalMarker - kInputBufferLocal == kInputBufferMarker, "the marker offset agrees");
static_assert(kInputBufferLocalByte - kInputBufferLocal == kInputBufferByte, "the byte offset agrees");
static_assert(kInputBufferLocalLink - kInputBufferLocal == 0x20, "the link offset agrees");
static_assert(kVtableSlotsKnown7 == kVtableSlotsKnown6 + 1, "one more slot than round 291");
static_assert(kSelfTestFirst, "the self-test runs before the operation");


// --- the driver 0x10FD40's control flow (round 299) -----------------------------------------------------
//     0x10FDC1/0x10FDF2  call qword [rax+0xA0], twice, the second time on the link at rsp+0x80
//     0x10FDFD/0x10FE09  the result's FIRST BYTE is read and sign tested; negative goes to 0x10FF07
//     0x10FDCC cmp r15b, byte [rsp+0x58]   ; the probe's byte against a field at +0x58
//     0x10FDCA/0x10FDFB/0x10FDD3  three failure sites, all reaching 0x77F2D0
//     0x10FE2A call 0xC33F0 with the local object and a zero
inline constexpr std::size_t kVtableSlotA0CallSites = 2;     // RE 0x10FDC1 and 0x10FDF2
inline constexpr bool kSlotA0ReturnsPointer = true;          // RE 0x10FDFD
inline constexpr bool kStatusByteSignTest = true;            // RE 0x10FE09
inline constexpr std::uintptr_t kNegativeStatusBranch = 0x10FF07;  // RE 0x10FE09
inline constexpr std::size_t kStatusComparedField = 0x58;    // RE 0x10FDCC
inline constexpr int kDriverFailureSites = 3;                // RE 0x10FDCA, 0x10FDFB and 0x10FDD3
inline constexpr std::uintptr_t kDriverReportsVia = 0x77F2D0;  // the BER formatter of round 280
inline constexpr std::uintptr_t kLocalConstruct = 0xC33F0;   // RE 0x10FE2A
inline constexpr std::uintptr_t kResultObject = 0xA0;        // RE 0x10FDFD, the local frame offset
static_assert(kVtableSlotA0CallSites == 2, "the slot is called twice");
static_assert(kStatusByteSignTest, "the first byte is treated as signed");
static_assert(kDriverFailureSites == 3, "three ways this driver fails");
static_assert(kDriverReportsVia == 0x77F2D0, "and all of them report through the BER formatter");


// --- the decoding loop of 0x10FD40, and the MEANING of round 299's sign test (round 300) ----------------
//     0x10FF07 and r15d,0x7F        ; the first byte's 0x80 bit is dropped, leaving a byte COUNT
//     0x10FF1D qword [rsp+0x90] = 0 ; the accumulator
//     0x10FF40 shl rax,8            ; shifted up
//     0x10FF44 or rax,rdx           ; and the next byte OR-ed in: BIG-ENDIAN
//     0x10FF47/0x10FF53  the last byte ends the loop
//     0x10FF59 shr rax,0x38 ; 0x10FF64 jne 0x10FDD3   ; more than eight bytes is an error
//     0x10FF74 call qword [rax+0xA0] ; each further byte comes from slot +0xA0
inline constexpr std::uint8_t kContinuationBit = 0x80;       // RE 0x10FE09, the 0x80 bit of the first byte
inline constexpr std::uint8_t kContinuationMask = 0x7F;      // RE 0x10FF07
inline constexpr std::size_t kAccumulatorOffset = 0x90;      // RE 0x10FF1D
inline constexpr std::size_t kAccumulatorShift = 8;          // RE 0x10FF40
inline constexpr std::size_t kAccumulatorMaxBytes = 8;       // RE 0x10FF59 (the top byte at 0x38 = 56)
inline constexpr std::size_t kAccumulatorTopShift = 0x38;    // RE 0x10FF59
inline constexpr std::uintptr_t kAccumulatorDone = 0x110105; // RE 0x10FF53
inline constexpr bool kBigEndianAccumulate = true;           // RE 0x10FF40/0x10FF44
inline constexpr bool kContinuationBitIsSignBit = true;      // what round 299's sign test was for
inline constexpr std::size_t kAccumulatorSource = 0xA0;      // RE 0x10FF38, the local object's byte
// the cast matters: ~promotes a std::uint8_t to int, so the complement would be 0xFFFFFF7F without it
static_assert(kContinuationMask == static_cast<std::uint8_t>(~kContinuationBit),
              "the mask is the complement of the bit");
static_assert(kAccumulatorTopShift == kAccumulatorMaxBytes * 8 - 8, "the top byte of an eight-byte value");
static_assert(kBigEndianAccumulate, "the bytes are assembled big-endian");
static_assert(kContinuationBitIsSignBit, "the sign test of round 299 is the continuation test");


// --- the sibling driver 0x110B00, and the one difference that matters (round 301) -----------------------
//     0x110B0C sub rsp,0x108             ; the same frame as 0x10FD40
//     0x110B24 lea rsi,[rsp+0x60]        ; the same in-place InputBuffer
//     0x110B50 call 0x118260 with edx = 0  ; the same self-test, again first
//     0x110B60 dword [rsp+0x74] = 0xFFFFFFFF and 0x110B58 byte [rsp+0x78] = 0
//     0x110B34 call qword [rax+0xB0]     ; but the leading byte comes through slot 0xB0
inline constexpr std::uintptr_t kDriverSibling = 0x110B00;   // RE the whole routine
inline constexpr int kDriverSiblingCallers = 2;              // RE the profile
inline constexpr std::size_t kDriverFrameBytes = 0x108;      // RE 0x10FD4C and 0x110B0C alike
inline constexpr std::size_t kVtableSlotJ = 0xB0;            // RE 0x110B34 -- a THIRTEENTH slot
inline constexpr int kVtableSlotsKnown8 = 13;                // with 0xB0 added to the twelve of round 298
inline constexpr int kDriverPair = 2;                        // the two 1134-byte drivers
inline constexpr bool kDriversDifferInSource = true;         // RE 0xB0 against the helper 0x1170B0
inline constexpr std::uintptr_t kDriverByteSourceA = 0xB0;   // the slot this one uses
inline constexpr std::uintptr_t kDriverByteSourceB = 0x1170B0;  // the helper the other uses
inline constexpr std::size_t kDriverLocal = 0x60;            // RE 0x110B24
inline constexpr std::size_t kDriverMarker = 0x74;           // RE 0x110B60
inline constexpr std::size_t kDriverByte = 0x78;             // RE 0x110B58
inline constexpr std::size_t kDriverProbe = 0x4A;            // RE 0x110B2F
static_assert(kDriverFrameBytes == 0x108, "both drivers frame the same way");
static_assert(kDriverPair == 2, "a pair of drivers");
static_assert(kDriversDifferInSource, "and they differ in where the bytes come from");
static_assert(kVtableSlotsKnown8 == kVtableSlotsKnown7 + 1, "one more slot than round 298");
static_assert(kDriverLocal - 0x14 == kDriverMarker - 0x28 || kDriverMarker - kDriverLocal == kInputBufferMarker,
              "the marker sits where round 288 put it");


// --- how far the two drivers' sameness goes, measured rather than asserted (round 302) -----------------
//     the negative-status branch:  0x110CC7 - 0x110B00 = 0x1C7  ==  0x10FF07 - 0x10FD40 = 0x1C7
//     the first shared instruction: 0x110B85 - 0x110B00 = 0x85  against  0x10FDC1 - 0x10FD40 = 0x81
// So the prologue is four bytes longer in the sibling while a later branch lands on the SAME offset, which requires a
// compensating four-byte difference between them. "Structurally the same with compensating differences" is what the
// two measurements support; "identical byte for byte" is NOT supported and is not claimed.
inline constexpr std::size_t kDriverTwinOffset = 0x1C7;      // RE both functions, the js target
inline constexpr std::uintptr_t kSiblingNegativeBranch = 0x110CC7;  // RE 0x110BCD
inline constexpr std::size_t kSiblingSharedAt = 0x85;        // RE 0x110B85
inline constexpr std::size_t kFirstDriverSharedAt = 0x81;    // RE 0x10FDC1
inline constexpr std::size_t kPrologueDelta = 4;             // RE 0x85 - 0x81
inline constexpr bool kDriversStructurallySame = true;       // what the offsets support
inline constexpr bool kDriversByteIdentical = false;         // NOT supported: a compensating difference exists
inline constexpr bool kDriversShareBody = true;              // the body repeats instruction for instruction
static_assert(kDriverTwinOffset == 0x1C7, "the shared relative offset of the negative branch");
static_assert(kSiblingSharedAt - kFirstDriverSharedAt == kPrologueDelta, "the prologue is four bytes longer");
static_assert(kSiblingNegativeBranch - kDriverSibling == kDriverTwinOffset, "and the branch is at the same place");
static_assert(kDriversStructurallySame && !kDriversByteIdentical, "the weaker claim only");


// --- where the two drivers actually differ, now localised (round 303) -----------------------------------
// Fourteen instructions of the negative branch were compared and every relative offset agrees:
//     0x1C7 (and r15d,0x7f), 0x1CB (je), 0x1D1, 0x1D5, 0x1DD, 0x1E9, 0x1F0, 0x1F8, 0x200 (shl), 0x204 (or),
//     0x207 (cmp), 0x20B, 0x213 (je) -- identical in both functions.
// Round 302 measured the FIRST shared instruction at 0x85 in the sibling against 0x81 in the first driver. So the
// compensating four bytes lie between relative 0x85 and 0x1C7, and from 0x1C7 on the bodies agree instruction for
// instruction. The difference is localised rather than spread over the routine.
inline constexpr std::size_t kDifferenceRegionStart = 0x85;   // RE 0x110B85 against 0x10FDC1
inline constexpr std::size_t kDifferenceRegionEnd = 0x1C7;    // RE the first offset that agrees again
inline constexpr bool kDifferenceLocalized = true;            // the four bytes sit inside that window
inline constexpr bool kBranchOffsetsIdentical = true;         // RE the fourteen comparisons
inline constexpr int kOffsetsCompared = 14;                   // RE the list above
inline constexpr std::size_t kBranchOffset0 = 0x1C7;          // RE and r15d,0x7f
inline constexpr std::size_t kBranchOffset1 = 0x1CB;          // RE the je after it
inline constexpr std::size_t kBranchOffset2 = 0x200;          // RE shl rax,8
inline constexpr std::size_t kBranchOffset3 = 0x213;          // RE the je that ends the loop
static_assert(kDifferenceRegionStart < kDifferenceRegionEnd, "the window is not empty");
static_assert(kDifferenceLocalized && kBranchOffsetsIdentical, "both findings hold together");
static_assert(kBranchOffset0 == kDriverTwinOffset, "the first is the offset round 302 measured");
static_assert(kOffsetsCompared == 14, "fourteen offsets were compared");


// --- the third driver 0x112150, reached through a vtable (round 304) ------------------------------------
//     0x11215C sub rsp,0x128                    ; a larger frame than the pair's 0x108
//     0x112163..0x112178 four vtable pointers    ; against the pair's two
//     0x11217F lea rbp,[rsp+0x60]                ; the same in-place object base
//     0x11218A lea r13,[rsp+0xa0]                ; its own second local
//     0x112197 call 0x118260 with edx = 0        ; the self-test, again first
//     0x1121A4/0x1121AC  the marker and the byte at the same offsets
//     0x1121CB call 0x111890 with edx = 0x30     ; a helper given forty-eight as a size
inline constexpr std::uintptr_t kDriverThird = 0x112150;     // RE the whole routine
inline constexpr std::size_t kDriverThirdFrame = 0x128;      // RE 0x11215C (296)
inline constexpr int kDriverVtables3 = 4;                    // RE the four lea instructions
inline constexpr int kDriverVtablesPair = 2;                 // RE the pair of rounds 298/301
inline constexpr std::size_t kThirdLocal = 0xA0;             // RE 0x11218A
inline constexpr std::uintptr_t kHelper111890 = 0x111890;    // RE 0x1121CB
inline constexpr std::size_t kHelper111890Size = 0x30;       // RE 0x11219C
inline constexpr int kDriverThirdCallers = 0;                // reached through a vtable
inline constexpr int kInPlaceConfirmations = 4;              // rounds 288, 291, 298 and 301/304
static_assert(kDriverThirdFrame > kDriverFrameBytes, "the third driver frames larger");
static_assert(kDriverVtables3 > kDriverVtablesPair, "and carries more vtable pointers");
static_assert(kHelper111890Size == kGetOrCreateBytes, "the same forty-eight as the get-or-create object");
static_assert(kThirdLocal == kResultObject, "its second local sits where the pair's result object does");


// --- a second in-place object in the third driver, and the fields it sets (round 305) -------------------
//     0x1121DF call 0x118260 again        ; the self-test is consulted once per object
//     0x1121EC/0x1121F7/0x11220F/0x112217  the second object's fields at 0xB4, 0xB8, 0xC0 and 0xC8
//     0x11221F call 0x111890 with 0x30    ; the same helper and size as the first object
//     0x112224/0x112237 a THIRD local at rsp+0x40
//     0x11224A call qword [rax+0x38]      ; a FOURTEENTH vtable slot
inline constexpr std::size_t kLocalBase1 = 0x60;             // RE 0x11217F
inline constexpr std::size_t kLocalBase2 = 0xA0;             // RE 0x11218A
inline constexpr std::size_t kLocalBase3 = 0x40;             // RE 0x112224
inline constexpr int kInPlaceConfirmations2 = 5;             // rounds 288, 291, 298, 301/304 and this
inline constexpr int kSelfTestCallsHere = 2;                 // RE 0x112197 and 0x1121DF
inline constexpr std::size_t kInputBufferByte2 = 0x28;       // RE 0x112217 -- observed here, not generalised
inline constexpr std::size_t kVtableSlotK = 0x38;            // RE 0x11224A -- a FOURTEENTH slot
inline constexpr int kVtableSlotsKnown9 = 14;                // with 0x38 added to the thirteen of round 301
inline constexpr std::uintptr_t kHelper111E90 = 0x111E90;    // RE 0x112253
inline constexpr int kHelper111890Calls = 2;                 // RE 0x1121CB and 0x11221F
static_assert(kLocalBase2 - kLocalBase1 == 0x40, "the two local objects are sixty-four bytes apart");
static_assert(kSelfTestCallsHere == 2, "the self-test is consulted once per object");
static_assert(kVtableSlotsKnown9 == kVtableSlotsKnown8 + 1, "one more slot than round 301");
static_assert(kInputBufferByte2 == kInputBufferByte + 0x10, "the extra byte sits sixteen past the first");


// --- a strict sweep that found nothing, recorded with its criterion (round 306) -------------------------
// The test, applied to 0x63F000-0x640000 and 0x998000-0x99A000 with a thirty-two byte cap: every instruction must be
// preparatory register work or ONE transfer to an address ALREADY registered as library code, and the body must
// reference no string and write no memory of its own. Result: zero found, and not even a one-transfer candidate.
// The result matters because it localises round 277's thunk class rather than generalising it, and because a zero is
// exactly the answer that is tempting to dress up. It is landed as it came out.
inline constexpr int kStrictThunkFound = 0;                  // RE the sweep
inline constexpr int kSweepClusters = 2;                     // RE the two ranges
inline constexpr std::size_t kSweepSizeCap = 32;             // RE the cap used
inline constexpr int kLibraryAddressesRegistered = 548;      // RE the registry at the time of the sweep
inline constexpr bool kThunkClassLocalised = true;           // the class lives where round 277 found it
inline constexpr bool kSweepCriterionRelaxed = false;        // it was NOT loosened to manufacture exclusions
static_assert(kStrictThunkFound == 0, "the sweep found nothing, and says so");
static_assert(kSweepClusters == 2 && kSweepSizeCap == 32, "two clusters under a thirty-two byte cap");
static_assert(!kSweepCriterionRelaxed, "the criterion was not relaxed to produce a result");
static_assert(kLibraryAddressesRegistered > 500, "the registry was already substantial");


// --- the parser of 0x111E90, which requires tag 6 (round 307) -------------------------------------------
//     0x111ECA/0x111EEB call 0x117050   ; a helper that fills ONE BYTE, called against adjacent stack slots
//     0x111ECF/0x111ED2  a null answer goes to the BER formatter
//     0x111ED4 cmp byte [rsp+0x29],6 ; je    ; THE FIRST TAG MUST BE SIX
//     0x111EDB call 0x77F2D0                  ; otherwise the BER error formatter runs
//     0x111EF9 movzx ebp, byte [rsp+0x2A]     ; and the next byte follows
inline constexpr std::uint8_t kRequiredTag = 6;              // RE 0x111ED4
inline constexpr bool kTag6IsOid = true;                     // the ASN.1 standard: universal tag 6 is OBJECT IDENTIFIER
inline constexpr std::uintptr_t kByteReader = 0x117050;      // RE 0x111ECA and 0x111EEB
inline constexpr int kByteReaderSites = 2;                   // RE the two calls
inline constexpr std::size_t kTagSlot = 0x29;                // RE 0x111ED4
inline constexpr std::size_t kSecondSlot = 0x2A;             // RE 0x111EF9
inline constexpr int kZeroedFields = 3;                      // RE 0x111EB2/0x111EBE/0x111EC1
inline constexpr std::size_t kZeroedBase = 0x30;             // RE the three stores
inline constexpr int kParserCallers = 2;
inline constexpr int kParserBytes = 692;
static_assert(kRequiredTag == 6, "the parser requires the OID tag");
static_assert(kSecondSlot == kTagSlot + 1, "the two slots are adjacent, a byte cursor");
static_assert(kByteReaderSites == 2, "the reader is called twice here");
static_assert(kTag6IsOid, "and tag six is OBJECT IDENTIFIER in ASN.1");


// --- the twin accessors 0x117050 and 0x1170B0, which explain the driver pair (round 308) ----------------
//     0x11705F/0x117070 call qword [rax+0x158] twice ; 0x11707C r8 = [rdx+0xA0] ; 0x11708C jmp r8
//     0x117090 the null path takes [rax+0xA8]
//     0x1170BF/0x1170D0 call qword [rax+0x160] twice ; 0x1170DC r8 = [rdx+0xB0]
// The two are the same ninety-two byte routine over different slot numbers, and their tails land on +0xA0 and +0xB0:
// exactly the difference rounds 301 and 302 measured from the outside between the two drivers.
inline constexpr std::uintptr_t kByteReaderTwin = 0x1170B0;  // RE the second of the pair
inline constexpr std::size_t kTwinDelta = 0x60;              // RE 0x1170B0 - 0x117050
inline constexpr int kTwinBytes = 92;                        // RE both function sizes
inline constexpr std::size_t kByteReaderStep = 0x158;        // RE 0x11705F
inline constexpr std::size_t kTwinStep = 0x160;              // RE 0x1170BF
inline constexpr std::size_t kByteReaderTail = 0xA0;         // RE 0x11707C
inline constexpr std::size_t kTwinTail = 0xB0;               // RE 0x1170DC
inline constexpr std::size_t kByteReaderNull = 0xA8;         // RE 0x117090 -- a FIFTEENTH slot
inline constexpr int kVtableSlotsKnown10 = 15;               // with 0xA8 added to the fourteen of round 305
inline constexpr bool kTailCallsThroughSlot = true;          // RE 0x11708C (jmp r8)
inline constexpr bool kHelpersMirrorDrivers = true;          // the pair's difference is this pair's difference
static_assert(kByteReaderTwin - kByteReader == kTwinDelta, "sixty bytes apart");
static_assert(kTwinTail == kDriverByteSourceA, "the twin's tail is the slot the sibling driver calls");
static_assert(kByteReaderTail != kTwinTail, "the two tails differ, which is the whole point");
static_assert(kVtableSlotsKnown10 == kVtableSlotsKnown9 + 1, "one more slot than round 305");
static_assert(kTailCallsThroughSlot && kHelpersMirrorDrivers, "both findings hold");


// --- the OID sub-identifier loop of 0x111E90 (round 309) -------------------------------------------------
//     0x111EFE/0x111F01 test bpl,bpl ; js    ; the continuation bit again, a second independent site
//     0x111F07/0x111F0A test rbp,rbp ; je    ; the byte count runs out
//     0x111F35 sar rax,2                     ; a container of FOUR-byte elements
//     0x111F49 lea rax,[rbx+8]               ; and a walk with an EIGHT-byte stride
//     0x111F52..0x111F65  ecx*4 + ecx then ecx + 8*that  -- forty-one times the byte
inline constexpr bool kOidContinuationTest = true;           // RE 0x111F01, second site of the same test
inline constexpr std::size_t kParserElementShift = 2;        // RE 0x111F35 (divide by four)
inline constexpr std::size_t kParserElementBytes = 4;        // RE the shift
inline constexpr std::size_t kParserStride = 8;              // RE 0x111F49
inline constexpr std::uint8_t kAsn1FirstArcBase = 40;        // the standard's base for the first two arcs
inline constexpr std::uint8_t kOidArithmeticFactor = 41;     // RE what the instructions actually compute
// The factor is recorded because it is what the instructions do, and the interpretation is LEFT OPEN: forty would be
// the standard's base and forty-one is not, so the arithmetic is not claimed to be the first-arc rule.
inline constexpr bool kOidArithmeticUninterpreted = true;
inline constexpr bool kFactorEqualsTagSlotOffset = true;     // 41 == 0x29, noted and not explained
static_assert(kParserElementBytes == (1u << kParserElementShift), "the shift is the element size");
static_assert(kOidArithmeticFactor == 1 + 8 * 5, "the factor the instructions compute");
static_assert(kOidArithmeticFactor != kAsn1FirstArcBase, "and it is NOT the standard's base, hence left open");
static_assert(kOidArithmeticUninterpreted, "so it is recorded as uninterpreted");


// --- the OID's continuation loop, second site of the same assembler (round 310) -------------------------
//     0x11208E and eax,0x7f        ; the SAME mask as round 300's length loop
//     0x112093 movzx ebx,al        ; the masked value is the byte COUNT
//     0x1120A5 shl rbp,8           ; the SAME shift
//     0x1120A9 or rbp,rax          ; the SAME big-endian assembly
//     0x1120B8/0x1120BB sub ebx,1 ; shr rax,0x38   ; the SAME eight-byte overflow check
//     0x112098/0x1120C2  the done and overflow branches
inline constexpr std::uint8_t kOidMask = 0x7F;               // RE 0x11208E
inline constexpr std::size_t kOidShift = 8;                  // RE 0x1120A5
inline constexpr std::size_t kOidOverflowShift = 0x38;       // RE 0x1120BB
inline constexpr std::uintptr_t kOidDoneBranch = 0x11212E;   // RE 0x112098
inline constexpr std::uintptr_t kOidOverflowBranch = 0x11213D;  // RE 0x1120C2
inline constexpr int kAssemblerSites = 4;                    // UPDATED in round 316: 0x10FD40, 0x110B00,
// 0x111E90 and now the INTEGER reader all assemble big-endian with the same mask, shift and overflow test
inline constexpr bool kAssemblerShapeShared = true;           // the same three constants at both
inline constexpr int kAccumulatorRegisters = 2;              // rbp accumulates, ebx counts
// The three equalities that make this a second site rather than a similar-looking one:
static_assert(kOidMask == kContinuationMask, "the mask is the same 0x7f");
static_assert(kOidShift == kAccumulatorShift, "the shift is the same eight");
static_assert(kOidOverflowShift == kAccumulatorTopShift, "the overflow test is the same 0x38");
static_assert(kAssemblerSites == 4 && kAssemblerShapeShared, "four sites, one shape");


// --- the parser's four error entries, its minimum of two elements, and a compare helper (round 311) ------
//     0x11212E/0x112133/0x112138/0x11213D  call 0x77F2D0, five bytes apart: the whole error surface
//     0x1120DE/0x1120E3/0x1120E6  edx = 2, rdx = 2 - count, call 0x90D560 -- grow to at least two
//     0x112102 call 0x63F300, eight bytes past the copy helper of round 251
inline constexpr int kParserErrorSites = 4;                  // RE the four adjacent calls
inline constexpr std::size_t kErrorSiteStride = 5;           // RE 0x112133 - 0x11212E
inline constexpr std::uintptr_t kParserErrorFirst = 0x11212E;  // RE the first of them
inline constexpr std::uintptr_t kParserErrorLast = 0x11213D;   // RE the last
inline constexpr std::size_t kParserMinElements = 2;         // RE 0x1120DE
inline constexpr std::uintptr_t kParserGrow = 0x90D560;      // RE 0x1120E6
inline constexpr bool kGrowArgumentIsDifference = true;      // RE 0x1120E3 (2 - count)
inline constexpr std::uintptr_t kCompareHelper = 0x63F300;   // RE 0x112102
inline constexpr std::size_t kCompareHelperDelta = 8;        // RE 0x63F300 - 0x63F2F8
inline constexpr int kHelperClusterMembers = 5;              // 0x63F238, 0x63F258, 0x63F2E8, 0x63F2F8, 0x63F300
inline constexpr std::uintptr_t kReadNullBranch = 0x112138;  // RE the null branch of round 309
static_assert(kParserErrorSites == 4, "four error entries");
static_assert(kErrorSiteStride == 5, "and they are five bytes apart");
static_assert(kParserErrorLast - kParserErrorFirst == 3 * kErrorSiteStride, "the four are consecutive");
static_assert(kCompareHelper == kMemcpyHelper + kCompareHelperDelta, "the compare helper follows the copy helper");
static_assert(kHelperClusterMembers == 5, "five members of the cluster are now known");


// --- the fourth driver 0x112740, and the family's varying vtable counts (round 312) ---------------------
//     0x11274C sub rsp,0x128           ; the same frame as the third
//     0x112753/0x11275A/0x112761       ; three vtable pointers
//     0x112768 lea rsi,[rsp+0x60]      ; the same in-place object
//     0x112778 call 0x118260           ; the same self-test, first
//     0x112785/0x11278D/0x11279C/0x1127A4  the same fields at the same relative offsets
//     0x1127AC call 0x111890 with 0x30 ; the same helper and size
inline constexpr std::uintptr_t kDriverFourth = 0x112740;    // RE the whole routine
inline constexpr int kDriverFourthCallers = 9;               // RE the profile
inline constexpr int kDriverFamily = 4;                      // rounds 298, 301, 304 and this
inline constexpr int kDriverVtables4 = 3;                    // RE the three lea instructions
inline constexpr int kDriverVtableCountsDiffer = 1;          // they are 2, 2, 4 and 3
inline constexpr int kInPlaceConfirmations3 = 6;             // rounds 288, 291, 298, 301, 304/305 and this
inline constexpr bool kDriverFamilyHelperShared = true;      // all four call 0x111890 with 0x30
inline constexpr bool kFamilyReadingIsTemplate = true;       // offered as the reading, nothing stronger
static_assert(kDriverFamily == 4, "four members");
static_assert(kDriverVtables4 == 3, "the fourth carries three");
static_assert(kDriverVtables4 != kDriverVtablesPair && kDriverVtables4 != kDriverVtables3,
              "and that differs from the other members");
static_assert(kInPlaceConfirmations3 == 6, "six confirmations of the in-place offsets");
static_assert(kDriverFamilyHelperShared, "one helper serves the whole family");


// --- the second type reader: the same shape, requiring tag 2 (round 313) ---------------------------------
//     0x1127CA call 0x117050                 ; a byte
//     0x1127D4 cmp byte [rsp+0x34],2 ; je    ; the tag must be TWO -- INTEGER
//     0x1127DB call 0x77F2D0                 ; the same formatter otherwise
//     0x1127EB call 0x117050                 ; the next byte, in the adjacent slot 0x35
//     0x1127F9/0x112800 movzx ebx,byte [...] ; test bl,bl ; js   ; the continuation bit, third site
//     0x11281B call 0x118470                 ; a helper given the length
inline constexpr std::uintptr_t kIntegerReader = 0x112740;   // RE the whole routine
inline constexpr std::uint8_t kRequiredTagInteger = 2;       // RE 0x1127D4
inline constexpr std::size_t kTagSlot2 = 0x34;               // RE 0x1127D4
inline constexpr std::size_t kSecondSlot2 = 0x35;            // RE 0x1127F9
inline constexpr int kTypeReaderFamily = 2;                  // the OID reader and the INTEGER reader
inline constexpr bool kTypeReadersShareShape = true;         // instruction for instruction but for the tag
inline constexpr int kContinuationTestSites = 3;             // rounds 300, 309/310 and this
inline constexpr std::uintptr_t kIntegerHelper = 0x118470;   // RE 0x11281B
inline constexpr int kIntegerReaderCallers = 9;
static_assert(kRequiredTagInteger == 2, "the INTEGER tag is two");
static_assert(kRequiredTagInteger != kRequiredTag, "and it differs from the OID reader's six");
static_assert(kSecondSlot2 == kTagSlot2 + 1, "the slots are adjacent here too");
static_assert(kSecondSlot2 - kTagSlot2 == kSecondSlot - kTagSlot, "the same adjacency as the OID reader");
static_assert(kTypeReadersShareShape && kTypeReaderFamily == 2, "two readers, one shape");
static_assert(kContinuationTestSites == 3, "a third site for the continuation test");


// --- the family splits by evidence: two type readers, two flag-driven drivers (round 314) ---------------
// In 0x10FD40 and 0x110B00 the sweep found no fixed-tag comparison, only:
//     0x10FD94/0x10FDB9/0x10FFB9  flag bytes at +0x78, +0x88, +0x89 and +0xF0 set to 0 or 1
//     0x10FEC2/0x110137/0x110180  two SIXTEEN-bit fields at +0x4C and +0x4E compared against zero
//     0x10FFAB/0x11003F/0x110061  a dword 1 at rsp+0x20 -- the constant and offset of rounds 283/284
// while 0x111E90 demands tag 6 and 0x112740 demands tag 2. So the four are two kinds, not four of one.
inline constexpr bool kFirstTwoDriversTagless = true;        // asserted for the two the sweep printed
inline constexpr bool kDriverFamilySplits = true;            // type readers against flag-driven drivers
inline constexpr std::size_t kDriverFlagA = 0x88;            // RE 0x10FDB9
inline constexpr std::size_t kDriverFlagB = 0x89;            // RE 0x10FE0F
inline constexpr std::size_t kDriverFlagC = 0xF0;            // RE 0x10FE6A
inline constexpr std::size_t kDriverWordA = 0x4C;            // RE 0x10FEC2, sixteen bits
inline constexpr std::size_t kDriverWordB = 0x4E;            // RE 0x110137, sixteen bits
inline constexpr std::uintptr_t kDriverGateConstantOffset = 0x20;  // RE 0x10FFAB, as in round 283
inline constexpr bool kThirdMemberListUnread = false;        // CLOSED in round 315: the list was read, and
// it holds thirty-four small-immediate operations with no non-zero comparison among them
static_assert(kDriverWordB - kDriverWordA == 2, "the two words are adjacent");
static_assert(kDriverGateConstantOffset == 0x20, "the gate constant sits where round 283 found it");
static_assert(kFirstTwoDriversTagless && kDriverFamilySplits, "the split is asserted, not assumed");
static_assert(!kThirdMemberListUnread,
              "the third member was read in round 315, so the flag is closed");
// The tagless claim for the third member is asserted in its own block below, where the constant is declared:
// a static_assert cannot refer to a name declared later in the same namespace.


// --- the third member is tagless too, and the accounting that follows (round 315) -----------------------
// 0x112150 has thirty-four small-immediate stack operations and NOT ONE comparison against a non-zero immediate:
//     0x112267/0x1122A9/0x112340/0x112386/0x1123AB/0x1123C5/0x1123E3/0x112410/0x112440/0x112470  flags vs zero
//     0x1124F2/0x112600/0x112611/0x112622/0x1126B4/0x1126C5/0x1126E0  seven SIXTEEN-bit fields vs zero
// So among the four drivers, three are tagless and one is the INTEGER reader. Round 314 had counted both type readers
// as drivers, which was wrong: the OID reader is CALLED BY a driver rather than being one. Corrected here.
inline constexpr int kTaglessDrivers = 3;                    // 0x10FD40, 0x110B00 and 0x112150
inline constexpr int kDriversWithTag = 1;                    // 0x112740, the INTEGER reader
inline constexpr int kSetOverlap = 1;                        // the drivers and the type readers share one member
inline constexpr bool kThirdMemberTagless = true;            // RE the sweep of this round
inline constexpr int kThirdMemberSmallImmediates = 34;       // RE the count
inline constexpr int kThirdMemberNonZeroCompare = 0;         // RE the count that decides it
inline constexpr int kThirdMemberWordFields = 7;             // RE the seven sixteen-bit comparisons
static_assert(kTaglessDrivers + kDriversWithTag == kDriverFamily, "three and one make the four");
static_assert(kThirdMemberNonZeroCompare == 0, "the third member has no tag comparison");
static_assert(kThirdMemberTagless, "so it is tagless, as the first two were");
static_assert(kSetOverlap == 1 && kTypeReaderFamily - kSetOverlap == 1,
              "one type reader is a driver and one is not");


// --- DER's minimal encoding and the four-byte fast path, in the INTEGER reader (round 316) --------------
//     0x112823 jne 0x112EEE        ; the length must match
//     0x11282D jbe 0x112E70        ; four bytes or fewer take a separate path
//     0x112833 cmp byte [r15],0 ; jne 0x112B45  ; the first byte must not be zero
//     0x112848 cmp byte [rcx],0 ; jne 0x112B45  ; nor any of the bytes before the last four
//     0x112869/0x11286C shl eax,8 ; or eax,r9d  ; the same assembly, in a THIRTY-TWO bit accumulator
inline constexpr bool kLeadingZeroCheck = true;              // RE 0x112833 and 0x112848
inline constexpr bool kMinimalEncodingRequired = true;       // DER's rule for INTEGER, which is what that check is
inline constexpr std::uintptr_t kLeadingZeroViolation = 0x112B45;  // RE where the check diverts
inline constexpr std::size_t kIntegerFastPathBytes = 4;      // RE 0x11282D
inline constexpr std::uintptr_t kIntegerFastPath = 0x112E70; // RE the branch it takes
inline constexpr bool kLengthMustMatch = true;               // RE 0x112823
inline constexpr std::uintptr_t kLengthMismatch = 0x112EEE;  // RE the branch it takes
inline constexpr int kSite4AccumulatorBits = 32;             // RE eax, against 64 bits at the other sites
inline constexpr std::uint8_t kIntegerZeroByte = 0;          // the byte the check rejects
static_assert(kLeadingZeroCheck && kMinimalEncodingRequired, "the minimal-encoding check is the DER rule");
static_assert(kIntegerFastPathBytes == 4, "four bytes or fewer");
static_assert(kLengthMustMatch, "and the length is compared with the value's count");
static_assert(kSite4AccumulatorBits == 32, "this site accumulates in thirty-two bits");


// --- the short-integer path reuses the loop, and a second error surface (round 317) ---------------------
//     0x112E73 je 0x112883          ; a ZERO length goes elsewhere
//     0x112E7F jmp 0x11285C         ; and 1..4 bytes enter the SAME assembly loop, past the zero scan
//     0x112EEE/0x112EF3/0x112EF8/0x112EFD  call 0x77F2D0, five bytes apart
//     0x112E84/0x112E95/0x112EA6    three SIXTEEN-bit fields at +0x3C, +0x3E and +0x40 against zero
inline constexpr bool kFastPathJumpsToLoop = true;           // RE 0x112E7F
inline constexpr std::uintptr_t kIntegerLoopEntry = 0x11285C;  // RE the target it jumps to
inline constexpr std::uintptr_t kZeroLengthBranch = 0x112883;  // RE 0x112E73
inline constexpr int kIntegerErrorSites = 4;                 // RE the four adjacent calls
inline constexpr int kErrorSurfacePatternSites = 2;          // rounds 311 and this
inline constexpr int kIntegerWordFields = 5;                 // CORRECTED in round 318: five, not three --
// rounds 316/317 had only seen +0x3C, +0x3E and +0x40; the chain at 0x112D83/0x112D94/0x112DA5 adds +0x38 and +0x3A
inline constexpr std::size_t kIntegerWordBase = 0x3C;        // RE the lowest of the three
inline constexpr std::uintptr_t kIntegerSource = 0x112EFD;   // RE the last error entry
// NARROWING my round-316 claim: the zero scan is skipped for values of four bytes or fewer, so what I called "DER's
// minimal-encoding rule" is a CONDITIONAL check, not a blanket one. The evidence has not changed; the scope of the
// sentence has, and it is corrected here rather than left standing.
inline constexpr bool kMinimalEncodingReadingNarrowed = true;
inline constexpr bool kZeroScanSkippedUnder4Bytes = true;
static_assert(kFastPathJumpsToLoop, "the short case reuses the loop rather than replacing it");
static_assert(kIntegerErrorSites == 4, "four error entries, as in the OID reader");
static_assert(kMinimalEncodingReadingNarrowed && kZeroScanSkippedUnder4Bytes,
              "the claim is narrowed to match the instruction");
static_assert(kIntegerWordFields == 5, "five sixteen-bit fields, two bytes apart");


// --- the five sixteen-bit fields and the indirect calls (round 318) --------------------------------------
//     0x112D60 call 0x77F2D0                       ; an error entry, and the head of the chain
//     0x112D6B/0x112D78 call rax                   ; TWO indirect calls through a register
//     0x112D83/0x112D89 cmp word [rsp+0x38],0 ; jne 0x112CD2
//     0x112D94/0x112D9A cmp word [rsp+0x3A],0 ; jne 0x112CA2
//     0x112DA5/0x112DAB cmp word [rsp+0x3E],0 ; jne 0x112C32
inline constexpr bool kIntegerWordFieldsUpdated = true;      // the count moved from three to five
inline constexpr std::size_t kIntegerWordStride = 2;         // RE the spacing of the five words
inline constexpr std::size_t kIntegerWordFirst = 0x38;       // RE 0x112D83
inline constexpr std::size_t kIntegerWordLast = 0x40;        // RE 0x112E84 (round 317)
inline constexpr int kIndirectCallSites = 2;                 // RE 0x112D6B and 0x112D78
inline constexpr bool kIndirectViaRegister = true;           // RE `call rax`
inline constexpr int kWordDispatchTargets = 3;               // RE 0x112CD2, 0x112CA2 and 0x112C32
inline constexpr std::uintptr_t kWordDispatchA = 0x112CD2;   // RE 0x112D89
inline constexpr std::uintptr_t kWordDispatchB = 0x112CA2;   // RE 0x112D9A
inline constexpr std::uintptr_t kWordDispatchC = 0x112C32;   // RE 0x112DAB
static_assert(kIntegerWordFields == 5, "five fields, and the count was corrected to say so");
static_assert((kIntegerWordLast - kIntegerWordFirst) / kIntegerWordStride + 1 == kIntegerWordFields,
              "they are contiguous at a stride of two");
static_assert(kIndirectCallSites == 2 && kIndirectViaRegister, "two indirect calls through a register");
static_assert(kWordDispatchTargets == 3, "three dispatch targets were read");


// --- the sixteen-bit fields hold BER lengths, written by the length reader (round 319) ------------------
//     0x112CB8/0x112CC3  rdx = rsp+0x38 and call 0x11A780   ; the reader fills the first of the five words
//     0x112CE8/0x112CF3  rdx = rsp+0x3C and call 0x11A780   ; and the word at +0x3C
//     0x112CC8/0x112CF8  cmp rax,2                          ; the same acceptance code as rounds 280/285/299
//     0x112CB0/0x112CE0  the objects at [rsp+0xC0] and [rsp+0x100], i.e. links of locals at 0xA0 and 0xE0
inline constexpr bool kWordFieldsAreLengths = true;          // RE the two calls and their destinations
inline constexpr int kLengthReaderSites2 = 2;                // RE 0x112CC3 and 0x112CF3
inline constexpr std::size_t kLengthDestA = 0x38;            // RE 0x112CB8
inline constexpr std::size_t kLengthDestB = 0x3C;            // RE 0x112CE8
inline constexpr int kStatusAcceptanceSites = 4;             // rounds 280, 285, 299 and this
inline constexpr std::size_t kObjectLinkA = 0xC0;            // RE 0x112CB0
inline constexpr std::size_t kObjectLinkB = 0x100;           // RE 0x112CE0
inline constexpr std::size_t kLocalBase4 = 0xE0;             // inferred from the +0x20 link offset
inline constexpr bool kLocalBase4Inferred = true;            // said so rather than presented as read
inline constexpr bool kIntegerIsALengthCaller = true;        // which is why round 285 listed it
static_assert(kWordFieldsAreLengths && kLengthReaderSites2 == 2, "two calls into the length reader");
static_assert(kObjectLinkA - 0x20 == kLocalBase2, "the first link belongs to the local at 0xA0");
static_assert(kObjectLinkB - 0x20 == kLocalBase4, "the second implies a local at 0xE0");
static_assert(kStatusAcceptanceSites == 4, "four sites accept status two");
static_assert(kLocalBase4Inferred, "and that base is marked as inferred");


// --- the narrow string's constructor, and its inline capacity (round 320) --------------------------------
//     0x9A0488 lea rax,[rcx+0x10]      ; the inline buffer at +0x10, as in rounds 262, 293 and 294
//     0x9A0498 je 0x9A050B             ; a null C string takes the empty case
//     0x9A04A3 repne scasb al,[rdi]    ; strlen, by scanning for the zero and complementing
//     0x9A04AC cmp rbx,0xF ; 0x9A04B5 jbe 0x9A04D4   ; FIFTEEN or fewer stay inline
//     0x9A04C2 call 0x910BA0           ; otherwise the allocation helper of round 275
inline constexpr std::uintptr_t kNarrowStringCtor = 0x9A0480;  // RE the whole routine
inline constexpr int kNarrowStringCallers = 34;              // RE the profile
inline constexpr std::size_t kNarrowSsoCapacity = 15;        // RE 0x9A04AC (0xF)
inline constexpr std::size_t kWideSsoChars = 7;              // round 294, for the other type
inline constexpr bool kStrlenViaScasb = true;                // RE 0x9A04A3
inline constexpr std::uintptr_t kEmptyCase = 0x9A050B;       // RE 0x9A0498
inline constexpr std::uintptr_t kInlineCase = 0x9A04D4;      // RE 0x9A04B5 -- the target when it fits
inline constexpr int kStringAllocHelperSightings = 2;        // rounds 275 and this
inline constexpr bool kSsoRelationHolds = true;              // 7*2+1 == 15, an OBSERVED equality
inline constexpr std::size_t kScasbElementBytes = 1;         // RE the byte scan
static_assert(kNarrowSsoCapacity == 15, "the narrow capacity is fifteen");
static_assert(kWideSsoChars * 2 + kScasbElementBytes == kNarrowSsoCapacity,
              "and seven wide characters plus one byte is fifteen -- observed, not designed");
static_assert(kStringAllocHelperSightings == 2, "the allocation helper has a second sighting");
static_assert(kStrlenViaScasb, "the length comes from a scasb scan");


// --- two small destructors, and the alternate releaser's third sighting (round 321) ---------------------
//     0x4B32F0/0x4B32F7 lea rax,[rip+0x585231] ; [rcx] = rax   ; a vtable
//     0x4B32FA/0x4B3301 rcx = [rcx+0x18] ; je                   ; the sub-object
//     0x4B3303 jmp 0x9984A0                                     ; tail called into the alternate releaser
//     0x656008/0x656011 rcx = [rcx+0x58] ; call 0x891B40        ; one field, by call
//     0x656016/0x656024 rcx = [rbx+0x10] ; jmp 0x891B40         ; the other, by tail call
inline constexpr std::uintptr_t kDtorSmall = 0x4B32F0;       // RE the whole routine
inline constexpr std::uintptr_t kDtorSmallVtableRva = 0x585231;  // RE 0x4B32F0
inline constexpr std::size_t kDtorSmallField = 0x18;         // RE 0x4B32FA
inline constexpr int kDtorSmallCallers = 23;
inline constexpr std::uintptr_t kTwoFieldDtor = 0x656000;    // RE the second routine
inline constexpr std::size_t kTwoFieldA = 0x58;              // RE 0x656008
inline constexpr std::size_t kTwoFieldB = 0x10;              // RE 0x656016
inline constexpr std::uintptr_t kTwoFieldHelper = 0x891B40;  // RE both release sites
inline constexpr int kTwoFieldSites = 2;                     // RE 0x656011 and 0x656024
inline constexpr int kTwoFieldCallers = 22;
inline constexpr bool kTwoFieldRelease = true;               // two fields, one helper
inline constexpr bool kCallThenTailCall = true;              // the first by call, the last by tail call
static_assert(kReleaserAltSightings == 3, "the alternate releaser has a third sighting now");
static_assert(kDtorSmallField == kSsoField18, "the sub-object sits where the string layout has its buffer");
static_assert(kTwoFieldSites == 2, "two release sites in the second routine");
static_assert(kTwoFieldA != kTwoFieldB, "and they release different fields");


// --- a third nested-container layout, and a constructor that forwards (round 322) ------------------------
//     0x8F7DD7/0x8F7DDB begin at +0x00, end at +0x08   ; round 254's outer pair
//     0x8F7DF9 call 0x891B40 for each element's +0x8   ; the helper round 321 found, second sighting
//     0x8F7DFE add rbx,0x10                            ; an inner stride of sixteen
//     0x8F7E19 jmp 0x9984B0                            ; the outer buffer, tail called
//     0x888FF7 lea-style descriptor plus 0x10 ; 0x888FFB [rcx] = rax
//     0x889002/0x889006  both pointers advance by eight, then a tail call to 0x86B750
inline constexpr std::size_t kNested3Begin = 0x00;            // RE 0x8F7DDB
inline constexpr std::size_t kNested3End = 0x08;              // RE 0x8F7DD7
inline constexpr std::size_t kNested3InnerStride = 0x10;      // RE 0x8F7DFE
inline constexpr std::size_t kNested3InnerField = 0x08;       // RE 0x8F7DF0
inline constexpr int kNested3Callers = 22;
inline constexpr std::uintptr_t kNested3Releaser = 0x891B40;  // RE 0x8F7DF9
inline constexpr int kReleaseHelperSightings = 2;             // rounds 321 and 322
inline constexpr int kNestedLayouts = 3;                      // rounds 254, 279 and this
inline constexpr int kSharedDeallocSightings7 = 8;            // rounds 248, 252, 254, 256, 261, 275, 293 and this
inline constexpr std::uintptr_t kCtorForward = 0x888FF0;      // RE the second routine
inline constexpr std::uintptr_t kCtorForwardTarget = 0x86B750;  // RE 0x889006
inline constexpr std::uintptr_t kDescriptorRva2 = 0x17FB39;   // RE 0x888FF0
inline constexpr std::size_t kDescriptorOffset2 = 0x10;       // RE 0x888FF7
inline constexpr int kCtorForwardCallers = 21;
inline constexpr bool kDescriptorOffsetRepeats = true;        // observed repetition, not identity
static_assert(kNested3InnerStride == 0x10, "the third layout's inner stride");
static_assert(kNested3InnerStride != kNested2InnerStride, "and it differs from the second layout's");
static_assert(kNestedLayouts == 3, "three nested layouts are now recorded separately");
static_assert(kSharedDeallocSightings7 == kSharedDeallocSightings5 + 1, "the deallocator again");
static_assert(kCtorForwardTarget == 0x86B750, "the constructor it forwards to");


// --- the wide string's append, third confirmation of the trio (round 323) --------------------------------
//     0x91354D/0x913550  data = [rbx] ; inline = rbx+0x10
//     0x913554 lea rsi,[rcx+r8]                 ; the new size
//     0x91355B cmp rax,r10 ; je 0x9135C0         ; the SSO check, a THIRD site
//     0x91356B lea rcx,[rax + rcx*2]             ; an element is two bytes
//     0x913581 mov word [rax + rsi*2], dx        ; the sixteen-bit terminator at the new end
//     0x9135B3 call 0x63F2F8                     ; the memcpy helper
//     0x9135A1 call 0x913710                     ; the grow helper
inline constexpr std::uintptr_t kWideAppend = 0x913540;      // RE the whole routine
inline constexpr int kWideAppendCallers = 23;
inline constexpr int kElementBytesWide = 2;                  // RE the *2 scaling
inline constexpr int kWideSsoChecks = 3;                     // rounds 293, 294 and this
inline constexpr std::size_t kTerminatorBytes = 2;           // RE the sixteen-bit store
inline constexpr std::uint8_t kTerminatorValue = 0;          // RE edx zeroed before the store
inline constexpr std::uintptr_t kWideAppendGrow = 0x913710;  // RE 0x9135A1
inline constexpr int kSingleElementPath = 1;                 // RE 0x913573 (cmp r8,1)
inline constexpr int kMemcpySightingsAtAppend = 1;           // RE 0x9135B3
static_assert(kElementBytesWide == 2, "the element is two bytes");
static_assert(kWideData == 0x00 && kWideSize == 0x08 && kWideCapacity == 0x10,
              "the same trio for the third time");
static_assert(kTerminatorBytes == kElementBytesWide, "the terminator is one element");
static_assert(kWideSsoChecks == 3, "a third SSO check site");

}  // namespace lcns
LCNS_RECOVERED(layout.record_sizes);   // strides and block sizes, rounds 218-241
LCNS_RECOVERED(layout.sentinel_convention);   // three -1 qwords beside one -1.0 double
LCNS_STRUCTURAL(model.ctor_family);   // rva 0x9C1BF0 unit literal, callee 0x1FD6C0
LCNS_STRUCTURAL(model.hash_table);   // 128 buckets of 24-byte entries, +0x48 key
