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
inline constexpr int kRatioFamilyTag = 6;                  // RE 0x724EB4
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
inline constexpr int kRatioFamilyRuleCases = 3;             // equal by tie test, ordered, or margin

}  // namespace lcns
