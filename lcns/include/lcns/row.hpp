// lcns/row.hpp -- Row::Distancer / Row::BasicDistancer / Row::Squeezer.
//
// Recovered from libcns_dump_64.dll (all RVAs):
//   typeinfo 0xA17E20 = Row::Distancer (abstract root, derives from Prc::PriceComputer's root
//                       0xA3ADA0); 0xA17DE0 = Row::BasicDistancer; 0xA17E00 = Row::Squeezer.
//   vtable address points (vptr = vtable+16, this is the layout the code actually references):
//     0xA3B1C0 = Row::BasicDistancer   (slots: 0x679060 dtor, 0x679050 dtor, 0x7CA810)
//     0xA3B1F0 = Row::Squeezer        (slots: 0x138BE0 dtor, 0x138CA0 dtor, 0x13A360)
//   Row::Squeezer::slot2 = 0x13A360: an address-keyed interval memo over two red-black maps at
//     [this+8][+0x240] and [this+8][+0x248]; on a miss it calls the cost routine 0x1380D0, stores
//     the result in the +0x240 map and returns the node's double at +0x30.
//   The cost routine 0x1380D0 (2375 B / 476 instructions) -- fully recovered here:
//     * entry   : `cmp byte [obj+8], 0` gate (feature flag)
//     * 0x134FA0: `optional<Interval> pick(src, bool)`: bool != 0 selects src+0x48, bool == 0
//                 selects src+0x70; the slot has a PRESENCE BYTE at +0 and FOUR DOUBLES at
//                 +8/+0x10/+0x18/+0x20 (0x28 bytes apart).
//     * 0x134FF0: `IntervalList* pick2(obj, bool)`: bool != 0 -> obj+0xA8, bool == 0 -> obj+0xC0.
//                 Each list is a {begin,end} pair of 32 byte Interval elements; the two lists must
//                 have EQUAL LENGTH (0x13860E..0x13861C) and, element by element, their v0 and v2
//                 must agree within 0.005 (0x13863B..0x1386C3) or the cost is not applicable.
//     * 1e-6 gate (0x1385A1..0x1385C9): the cross product of the two unit directions; when it is
//                 NOT zero the code takes the angle path at 0x1386F3 (i.e. it computes the row
//                 direction angle), otherwise the directions are parallel and it skips it.
//     * cost    (0x13879E..0x1387E9):
//                   cost = obj[+0x10] / sin(directionAngle) - max(|A.v0-A.v2|, |B.v0-B.v2|)
//               where A = pick(lo,1) (+0x48) and B = pick(hi,0) (+0x70), and the sine comes from
//               angleToFixedDegrees (0x5C22D0) fed through the exact 0/90/180/270 cases of the
//               sin block (0x138771..0x13878F).
//     * the two lengths are asserted non zero (0x13821C / 0x1383EF, message contains "distance");
//       here a zero length yields `present = false` instead of aborting -- see the note below.
#pragma once

#include <cstddef>
#include "lcns/recovery.hpp"
#include <cstdint>
#include <vector>

#include "lcns/geom.hpp"

namespace lcns {
namespace row {

// RE: the value type copied by 0x134FA0 -- four doubles, 0x20 bytes.
struct Interval {
    double v[4] = {0.0, 0.0, 0.0, 0.0};
};

// RE: one of the two slots a row carries (+0x48 / +0x70): a presence byte plus an Interval.
struct Slot {
    bool present = false;
    Interval value;
};

// RE: 0x134FF0 returns obj+0xA8 or obj+0xC0; each is a vector of 32 byte Interval elements.
struct IntervalList {
    std::vector<Interval> items;

    std::size_t size() const { return items.size(); }
    bool empty() const { return items.empty(); }
};

// The object 0x1380D0 reads: flag at +0x8, threshold at +0x10, the two row slots at +0x48/+0x70
// and the two interval lists at +0xA8/+0xC0.
struct SqueezeContext {
    bool enabled = true;        // [+0x8]   `cmp byte [obj+8], 0`
    double threshold = 0.0;     // [+0x10]  divided by the sine
    Slot loSlot;                // [+0x48]  pick(lo, /*bool=*/1)
    Slot hiSlot;                // [+0x70]  pick(hi, /*bool=*/0)
    IntervalList loList;        // [+0xA8]
    IntervalList hiList;        // [+0xC0]
};

// RE: 0x9BCFD8 = 0.005 (the element-wise alignment gate) and 0x9BCFC0 = 1e-06 (the parallelism
// gate on the cross product of the two unit directions).
inline constexpr double kSqueezeAlignmentTolerance = 0.005;
inline constexpr double kSqueezeParallelTolerance = 1e-06;

// RE: 0x9BCEB0 = 20.0, the scale the PER-CANDIDATE construction path applies to the candidate's
// height before handing it to the Row::Squeezer constructor. From 0x133DE0 (the routine 0x134470
// calls in its min-over-candidates loop):
//     133E3E  call 0x5CD800(rsp+0xE0, container)   ; the candidate's bounding box
//     133E43  if ([rsp+0xE0] != 0) goto 0x133E81   ; flag set => the height drops out as 0/0
//     133E55  xmm6 = [rsp+0xF8] - [rsp+0xE8]       ; maxY - minY  ==  height
//     133E67  xmm6 *= [0x9BCEB0] = 20.0            ; ★ height * 20.0
//     133E6F  xmm7 = [rsp+0x100] - [rsp+0xF0]      ; maxX - minX  ==  width (used elsewhere)
//     133EF7  call 0x136B80(&squeezer, xmm1 = xmm6, xmm2 = cfg[+0x18], xmm3 = cfg[+0x10])
// so this path builds a Squeezer whose first argument is 20 * height, whereas 0x13C380 builds one
// whose first argument is 2 * max(height, width). Both are the same constructor parameter.
inline constexpr double kCandidateHeightScale = 20.0;   // RE 0x9BCEB0

// The per-candidate first argument, exactly as 0x133E55..0x133E67 computes it.
inline double candidateSqueezerArg(double height) { return kCandidateHeightScale * height; }

// ---------------------------------------------------------------------------
// The per-candidate SCORE (RE: 0x136C00 layout, 0x134F30, 0x136CB0)
// ---------------------------------------------------------------------------
// 0x136C00 (75 B) initialises the object 0x133DE0 builds at rsp+0x110:
//     136C00  xmm0 = [0x9BCF48] = -1.0        <-- the "not computed" sentinel (NOT NaN)
//     136C0C  obj[+0x00] = xmm1               ; a double
//     136C10  obj[+0x08] = xmm2               ; a double
//     136C15  obj[+0x10] = 1                  ; flag A
//     136C19  obj[+0x11] = 1                  ; flag B
//     136C1D  obj[+0x18] = obj[+0x20] = obj[+0x28] = 0     ; a vector<16-byte element>
//     136C35  obj[+0x30] = obj + 0x40 ; obj[+0x38] = 0 ; byte obj[+0x40] = 0
//     136C45  obj[+0x50] = -1.0               ; the score cache
// 0x134F30 (22 B) is applied to an element's first pointer:
//     134F30  if (byte [rcx+0x18] != 0) return 0.0 ; else return [rcx+0x30] - [rcx+0x20]
// 0x136CB0 (78 B) is the lazy score of the whole object:
//     136CBA  xmm0 = obj[+0x50]
//     136CBF  ucomisd xmm0, -1.0 ; jp/jne -> return the cache untouched
//     136CCE  rax = obj[+0x20]                       ; the vector's end
//     136CD2  xmm0 = 0
//     136CD6  if (obj[+0x18] == rax) -> store 0      ; empty container
//     136CDC  rcx = [rax-0x10] ; xmm6 = [rax-8]      ; the LAST element {ptr, double}
//     136CE5  call 0x134F30(rcx)
//     136CEA  xmm0 += xmm6                           ; score = len(last.ptr) + last.value
//     136CEE  obj[+0x50] = xmm0                      ; memoise
inline constexpr double kScoreUnset = -1.0;   // RE 0x9BCF48

// The node 0x134F30 is applied to. Its layout is fully covered by the accessor family
// (all addresses verified):
//     0x134F30  degenerate ? 0 : ([+0x30] - [+0x20])      <-- the X extent
//     0x134F50  degenerate ? 0 : ([+0x38] - [+0x28])      <-- the Y extent
//     0x134F90  dl ? byte[+0x41] : byte[+0x40]
//     0x134FA0  picks [+0x48] or [+0x70] (bool) and copies its 4 doubles
//     0x134FF0  dl ? (this+0xa8) : (this+0xc0)
//     0x135010  dl ? byte[+0x99] : byte[+0x98]
//     0x135030  double [+0xa0]
// so the node is a boxed geometric object (with a degenerate flag), two optional 4-double
// intervals, two containers, two flag pairs and one extra double.
struct ScoreNode {
    std::uintptr_t owner = 0;      // [+0x00]  RE 136371 `[rcx] = rdx`  (the Item pointer)
    // [+0x08] / [+0x10]: CORRECTED. These are NOT a container's begin/end -- they are a copy of
    // the 16 byte candidate record `{u8 tag, ..., int64 angle}` that produced this element:
    //     136363  rax = [r8] ; 136374 rdx = [r8+8]      ; r8 = a 16 byte candidate element
    //     13637B  [element+0x08] = rax ; 136388 [element+0x10] = rdx
    // and 0x1355C0 then reads them back as exactly that record:
    //     1355DA  rdx = element + 8
    //     1355E1  call 0x5CEE50(transform, element + 8)   ; which reads byte[x] and [x+8]
    // (0x5CEE50 reads the tag with 0x5C4CD0(x) = byte[x] and the angle with 0x5C4CE0(x) = [x+8].)
    std::uint64_t sourceTagQword = 0;    // [+0x08]  the tag byte is its low byte
    std::int64_t sourceAngle = 0;        // [+0x10]  the fixed-degree angle at scale 1e10
    bool degenerate = false;   // [+0x18]  RE 13637F `byte [rcx+0x18] = 1` (initially SET)
    double minX = 0.0;         // [+0x20]
    double minY = 0.0;         // [+0x28]
    double maxX = 0.0;         // [+0x30]
    double maxY = 0.0;         // [+0x38]
    unsigned char flag40 = 0;  // [+0x40]
    unsigned char flag41 = 0;  // [+0x41]
    Slot slotAt48;             // [+0x48]
    Slot slotAt70;             // [+0x70]
    unsigned char flag98 = 0;  // [+0x98]
    unsigned char flag99 = 0;  // [+0x99]
    double valueAtA0 = 0.0;    // [+0xa0]
    IntervalList listAtA8;     // [+0xa8]
    IntervalList listAtC0;     // [+0xc0]
};

// RE 0x134F30 / 0x134F50: the node's two extents (0 when the degenerate flag is set).
inline double nodeLength(const ScoreNode& n) {
    return n.degenerate ? 0.0 : (n.maxX - n.minX);
}
inline double nodeLengthY(const ScoreNode& n) {
    return n.degenerate ? 0.0 : (n.maxY - n.minY);
}

// RE 0x134F90 / 0x135010: the two flag pairs, selected by a bool.
inline unsigned char nodeFlag40(const ScoreNode& n, bool second) {
    return second ? n.flag41 : n.flag40;
}
inline unsigned char nodeFlag98(const ScoreNode& n, bool second) {
    return second ? n.flag99 : n.flag98;
}

// ---------------------------------------------------------------------------
// RE 0x1355C0: the element's own geometry step
// ---------------------------------------------------------------------------
//     1355D4  rbp = rcx                     ; the output container
//     1355D7  rsi = rdx                     ; the element
//     1355DA  rdx = element + 8
//     1355E1  call 0x5CEE50(transform, element + 8)     ; the transform of ITS OWN angle
//     1355E6  rcx = [element]               ; the Item pointer
//     1355E9  call 0x133190                 ; = `lea rax,[rcx+8]`, i.e. Item+0x08
//     1355F7  call 0x5D38C0(out, Item+0x08, transform)  ; transform-copy the part's geometry
//     135602  call 0x5CD800(transform..., out)          ; its bounding box
// so the element's box comes from rotating the Item's 0x08 container by the element's own angle.
inline constexpr std::size_t kItemGeometry = 0x08;   // RE 0x133190 = `lea rax,[rcx+8]`

// RE 0x5C4CD0 applied to `element + 8` (which is what 0x5CEE50 receives).
inline unsigned char nodeSourceTag(const ScoreNode& n) {
    return static_cast<unsigned char>(n.sourceTagQword & 0xFFu);   // RE: byte [element+0x08]
}
// RE 0x5C4CE0 applied to `element + 8`.
inline std::int64_t nodeSourceAngle(const ScoreNode& n) {
    return n.sourceAngle;                                          // RE: qword [element+0x10]
}
// nodeAngleTransform() is defined below, after AngleTransform (RE 0x5CEE50).

// ---------------------------------------------------------------------------
// The element's layout, locked to the binary at COMPILE TIME
// ---------------------------------------------------------------------------
// 0x136350 (1920 B) is the constructor of the 216 byte element stored in Item+0x58 / Item+0x70,
// and its prologue writes exactly these offsets:
//     136371  [rcx+0x00] = rdx               ; a pointer (the Item)
//     13637B  [rcx+0x08] = [r8]              ; the source container's begin
//     136388  [rcx+0x10] = [r8+8]            ; ... and its end
//     13637F  byte [rcx+0x18] = 1            ; the degenerate flag, initially SET
//     136383  [rcx+0x20] = [rcx+0x28] = [rcx+0x30] = [rcx+0x38] = 0.0
//     136403..13642F  0x5CD800's five qwords (flag + 4 doubles) -> element +0x18 .. +0x38
//     13644B  byte [rcx+0x40] = 0x134D70(container, Item+0x20)
//     136489  byte [rcx+0x41] = 0x134D70(transformed container, Item+0x20)
//     13639B  byte [rcx+0x48] = 0 ; 13639F byte [rcx+0x70] = 0     ; the optional slots
//     1363A3..1363DA  +0xa8/+0xc8 (begin) and +0xb8/+0xd0 (cap) cleared
//     13645B  call 0x5CE7F0(rsp+0x150, 0x1A3185C5000)   ; a transform for 180 DEGREES
// so ScoreNode's field order is the binary's field order -- these assertions fail to compile if
// anyone reorders or resizes it.
inline constexpr std::size_t kScoreNodeSize = 0xd8;   // 216 bytes, the stride 0x137A90 walks
static_assert(sizeof(ScoreNode) == kScoreNodeSize, "ScoreNode must be the 216 byte element");
static_assert(offsetof(ScoreNode, degenerate) == 0x18, "degenerate flag is at +0x18");
static_assert(offsetof(ScoreNode, minX) == 0x20, "minX is at +0x20");
static_assert(offsetof(ScoreNode, minY) == 0x28, "minY is at +0x28");
static_assert(offsetof(ScoreNode, maxX) == 0x30, "maxX is at +0x30");
static_assert(offsetof(ScoreNode, maxY) == 0x38, "maxY is at +0x38");
static_assert(offsetof(ScoreNode, flag40) == 0x40, "flag40 is at +0x40");
static_assert(offsetof(ScoreNode, flag41) == 0x41, "flag41 is at +0x41");
static_assert(offsetof(ScoreNode, slotAt48) == 0x48, "the first optional slot is at +0x48");
static_assert(offsetof(ScoreNode, slotAt70) == 0x70, "the second optional slot is at +0x70");
static_assert(offsetof(ScoreNode, flag98) == 0x98, "flag98 is at +0x98");
static_assert(offsetof(ScoreNode, flag99) == 0x99, "flag99 is at +0x99");
static_assert(offsetof(ScoreNode, valueAtA0) == 0xa0, "the extra double is at +0xa0");
static_assert(offsetof(ScoreNode, listAtA8) == 0xa8, "the first container is at +0xa8");
static_assert(offsetof(ScoreNode, listAtC0) == 0xc0, "the second container is at +0xc0");

// RE the Item (0x90 bytes, constructor 0x1333D0): 1336F8..133724 clears two containers'
// begin/end/cap at +0x58/+0x60/+0x68 and +0x70/+0x78/+0x80, and 13372F clears a byte at +0x88.
// 0x1331A0(Item, dl) then returns `dl ? Item+0x70 : Item+0x58`, i.e. one of those two.
inline constexpr std::size_t kItemSize = 0x90;
inline constexpr std::size_t kItemContainerA = 0x58;
inline constexpr std::size_t kItemContainerB = 0x70;
inline constexpr std::size_t kItemSubObject = 0x20;   // RE 0x1333C0 = `lea rax,[rcx+0x20]`

// RE 0x1331A0: `lea rax,[rcx+0x70] ; add rcx,0x58 ; test dl,dl ; cmove rax,rcx`.
inline std::size_t itemContainerOffset(bool second) {
    return second ? kItemContainerB : kItemContainerA;
}

// ---------------------------------------------------------------------------
// The end of the score assembly: 0x137BF0 .. 0x137C83
// ---------------------------------------------------------------------------
// The virtual call 0x137A90 makes on its 4th argument is resolved: the argument is the
// Row::Squeezer, and the slot is 1 (at vptr+0x10), whose target is 0x13A360 -- the memoised
// squeeze cost, i.e. exactly what row::Squeezer::cost implements here.
//     137BF5  if (rbp == 0) goto 0x137DA0      ; rbp = the last stored record (or 0)
//     137BFE  rax = [r12]                      ; the vptr
//     137C05  rcx = r12                        ; this
//     137C08  rdx = [rbp]                      ; arg2 = that record's node pointer
//     137C02  r8  = rbx                        ; arg3 = the current 216 byte element
//     137C0C  call [rax+0x10]                  ; ★ slot 1 = 0x13A360 = Squeezer::cost(lo, hi)
//     137C0F  xmm8 = xmm0                      ; the squeeze cost
//     137C19  call 0x136CB0(obj)               ; the object's lazy score
//     137C21  xmm6 = [rdi+8] ; 137C32 call 0x134F30([rdi])   ; a record value and an X extent
//     137C3B  xmm6 += xmm10                    ; xmm10 = [P+0x38]
//     137C37  xmm7 = lazy + cost
//     137C40  ucomisd xmm6, xmm7 ; jbe -> skip
//     137C46  xmm6 -= xmm7 ; 137C4A cost += xmm6            ; absorb the excess
//     137C57  call 0x135030(element)           ; element[+0xa0]
//     137C63  call 0x136D10(obj)               ; obj[+0x08]
//     137C76  divsd                            ; the ratio
//     137C83  subsd                            ; ★ score = cost - ratio
inline double elementScore(double squeezeCost, double lazyScore, double recordValue,
                           double prevExtent, double axis, double elementAtA0, double objAt0x08) {
    double cost = squeezeCost;                                    // xmm8
    const double a = recordValue + prevExtent + axis;             // xmm6 (137C21..137C3B)
    const double b = lazyScore + cost;                            // xmm7 (137C29..137C2D)
    if (a > b) cost += (a - b);                                   // 137C40 jbe / 137C46 / 137C4A
    return cost - elementAtA0 / objAt0x08;                        // 137C76 / 137C83
}

// One 16-byte element of the object's vector (RE: [rax-0x10] is the pointer, [rax-8] the double).
struct ScoreRecord {
    const ScoreNode* node = nullptr;
    double value = 0.0;
};

// RE 0x136CB0's arithmetic. An empty container scores 0; otherwise the LAST element decides.
inline double candidateScore(const std::vector<ScoreRecord>& records) {
    if (records.empty()) return 0.0;                       // RE: 0x136CD6
    const ScoreRecord& last = records.back();              // RE: 0x136CDC
    return (last.node ? nodeLength(*last.node) : 0.0) + last.value;   // RE: 0x136CEA
}

// The memoising wrapper. NOTE the recovered semantics: the cache is only recomputed when it is
// exactly kScoreUnset. The invalidation point is NOT a caller convention -- it is the appender
// 0x137800 itself:
//     137830  rax = [O+0x20]                    ; the vector's end
//     137834  cmp rax, [O+0x28]                  ; vs the capacity
//     137838  je 0x137A11                        ; needs growth
//     137854  [rax] = rdx                        ; the 16 byte record's pointer
//     137857  [rax+8] = xmm0                     ; ... and its double
//     13785C  add rax, 0x10                      ; stride 0x10 -- exactly ScoreRecord
//     137860  [O+0x20] = rax                     ; commit the new end
//     ...
//     137877  movsd [rbx+0x50], -1.0             ; ★ resets the cache on every insertion
// The function's own inlined assertion string decodes to "orderedAddElement", i.e. the container is
// kept ORDERED -- and candidateScore() reads the LAST element, so the score is the container's
// extreme element. Which end that is (ascending or descending) is [推断] from the name plus the
// "last element" read; it is not asserted here.
class LazyScorer {
public:
    double score(const std::vector<ScoreRecord>& records) {
        if (cached_ != kScoreUnset) return cached_;        // RE: 0x136CCA jp/jne
        cached_ = candidateScore(records);                 // RE: 0x136CEE
        return cached_;
    }
    void invalidate() { cached_ = kScoreUnset; }
    double cached() const { return cached_; }
    bool computed() const { return cached_ != kScoreUnset; }

private:
    double cached_ = kScoreUnset;   // RE: obj[+0x50] initialised to -1.0
};

// RE 0x137800, whose inlined assertion names it "orderedAddElement": append one 16 byte
// {pointer, double} record and reset the score cache.
inline void orderedAddElement(std::vector<ScoreRecord>& records, LazyScorer& scorer,
                             const ScoreNode* node, double value) {
    ScoreRecord r;
    r.node = node;
    r.value = value;
    records.push_back(r);   // RE: 0x137854 / 0x137857 (growth path at 0x137838 -> 0x137A11)
    scorer.invalidate();    // RE: 0x137877
}

// ---------------------------------------------------------------------------
// The candidate loop: 0x134470 and the three primitives it drives
// ---------------------------------------------------------------------------
// Recovered argument flow:
//     0x6AABC0: call 0x134470(rcx = rsp+0x190, rdx = rsp+0x1b0, r8 = rsp+0x1d0, r9 = core+8)
//               rsp+0x1b0 is the copy of 0x4F7600(part), a container of 0x30 byte elements
//     0x134470: rbp = rcx (out) ; rdi = rdx (that buffer) ; rsi = r8 ; r12 = r9 (config)
//               for each element rbx of a 16 byte element vector:
//                   rbx = [rbx]            ; the element's first qword is a POINTER
//                   call 0x5C2E40(rsi, rbx)   ; ★ the authorisation predicate (records in rsi)
//                   if (!ok) skip
//                   call 0x133DE0(rcx = rdi, rdx = rsi, r8 = rbx, r9 = r12)
//                   keep the MINIMUM (ucomisd xmm6, xmm0 ; jbe -> next)
//     0x133DE0: 0x5CEE50(rsp+0x170, element)  ; angle -> the transform below
//               0x5D38C0(rsp+0x40, buffer, rsp+0x170)   ; the transformed copy
//               0x5CD800(rsp+0xE0, rsp+0x40)            ; its bounding box
//               20.0 * height -> 0x1333D0 (Item) + 0x136B80 (Squeezer) -> the score
//
// 0x5C2E40 (138 B, fully decoded in findings section 21.1): the records are 24 bytes
//     0x5C2E69  tag = 0x5C4CD0(element) ; cmp tag, byte [rec+0]      ; must match
//     0x5C2E7D  a = [rec+8] ; b = [rec+0x10]
//     0x5C2E8A  in range  <=>  (v >= a && v <= b)   when a <= b
//     0x5C2EA2  in range  <=>  (v <= b || v >= a)   when a >  b     (the reversed interval)
struct AuthRecord {
    unsigned char tag = 0;      // [+0x00]  RE: 0x1366BE style reads / 0x5C4CD0(element)
    std::int64_t lo = 0;        // [+0x08]  RE 0x5C4A45: a fixed-degree ANGLE (0x5C4CE0 value)
    std::int64_t hi = 0;        // [+0x10]  RE 0x5C4A4D: another fixed-degree angle
};

// RE 0x5C4950 (730 B): the record table 0x134470's arg2 is built by this. It walks the part's
// element list with a 0x18 stride (0x5C4A97 `add rbx, 0x18`) and, per element, emits
//     5C4A20/5C4A2E  call 0x5C4CE0 twice   ; two ANGLES -> r15 / r14
//     5C4A39         call 0x5C4CD0         ; the tag byte
//     5C4A3E/45/4D   [rsp+0xb0/b8/c0] = {tag, angle, angle}
//     5C4A70..5C4A8F append those three qwords (24 bytes) with `add rax, 0x18`
// so an AuthRecord's lo/hi are ANGLE bounds, i.e. the table says which angle ranges are allowed
// for each tag -- and 0x5C2E40 is the membership test over those ranges.
inline AuthRecord makeAuthRecord(unsigned char tag, std::int64_t lo, std::int64_t hi) {
    AuthRecord r;
    r.tag = tag;   // RE: 0x5C4A3E
    r.lo = lo;     // RE: 0x5C4A45
    r.hi = hi;     // RE: 0x5C4A4D
    return r;
}

// RE 0x4F7600 (nine bytes): the accessor that yields the part's geometry container --
//     4F7600  mov rcx, [rcx+0x70]
//     4F7604  jmp 0x547610
// i.e. a tail call on Part+0x70. Its result is a reference, which is why 0x6AABC0 copies it into
// the loop-local buffer at rsp+0x1b0 before handing it to 0x134470 as arg1.
inline constexpr std::size_t kPartGeometryVia = 0x70;   // RE: 0x4F7600

// RE 0x5C3F00: the angle wrap constant it uses is 0x34630B89FFF = 360e10 - 1 (0x5C3F0A/0x5C3F66).
inline constexpr geom::fixed_t kAngleWrapMax = 0x34630B89FFFll;

// RE 0x5C2E40. `tag` and `value` are what the element yields through 0x5C4CD0 / 0x5C4CE0.
inline bool authorized(const std::vector<AuthRecord>& records, unsigned char tag,
                       std::int64_t value) {
    for (const AuthRecord& r : records) {
        if (r.tag != tag) continue;                       // RE: 0x5C2E71 jne
        if (r.lo <= r.hi) {                               // RE: 0x5C2E85 jg -> the other form
            if (value >= r.lo && value <= r.hi) return true;   // RE: 0x5C2E8A/0x5C2E93
        } else {
            if (value <= r.hi || value >= r.lo) return true;   // RE: 0x5C2EA2/0x5C2EAB
        }
    }
    return false;                                         // RE: 0x5C2EC0 xor eax,eax
}

// RE 0x5CEE50, the tag == 0 path: an angle index (fixed degrees, scale 1e10) becomes the six
// doubles {cos, -sin, sin, cos, 0, 0}. Constants, all verified:
//     5CEE7A  the modulo magic 0x9C5FFF26ED75ED55   (the same one the 0x1380D0 sin block uses)
//     5CEE9B  the turn 0x34630B8A000 = 360e10
//     5CEEB8/5CEEC5/5CEED8/5CEEEB  compare against 0xD18C2E2800 / 0x1A3185C5000 / 0x274A48A7800
//     5CEEFA  general path: deg / [0x9DE950] = 3.6e12 * [0x9DE958] = 2*pi
//     5CEF2E  -sin is produced with xorpd against [0x9DE960] = -0.0, so its sign is exact
//     5CEFE0  angle 0    : cos = [0x9DE930] = 1.0,  -sin = [0x9DE948] = -0.0, sin = 0
//     5CF000  angle 90e10: cos = 0,                 -sin = [0x9DE940] = -1.0, sin = 1.0
//     5CF020  angle180e10: cos = -1.0,              -sin = -0.0,             sin = 0
//     5CF040  angle270e10: cos = 0,                 -sin = 1.0,              sin = -1.0
// The tag != 0 path (from 0x5CEF5E) applies additional scaling; it is NOT reproduced here.
struct AngleTransform {
    double cos = 0.0;      // [out+0x00]
    double negSin = 0.0;   // [out+0x08]
    double sin = 0.0;      // [out+0x10]
    double cos2 = 0.0;     // [out+0x18]
    double zero20 = 0.0;   // [out+0x20]
    double zero28 = 0.0;   // [out+0x28]
};

inline AngleTransform angleTransform(geom::fixed_t deg) {
    constexpr geom::fixed_t kFullTurn = 3600000000000ll;   // RE 0x34630B8A000
    constexpr double kTwoPi = 6.283185307179586;           // RE 0x9DE958
    const geom::fixed_t a = deg % kFullTurn;               // RE: 0x5CEE7A..0x5CEEAF
    AngleTransform t;
    switch (a) {
        case 0:                                                  // RE: 0x5CEFE0
            t.cos = 1.0; t.negSin = -0.0; t.sin = 0.0; break;
        case 0xD18C2E2800ll:                                     // RE: 0x5CF000 (90)
            t.cos = 0.0; t.negSin = -1.0; t.sin = 1.0; break;
        case 0x1A3185C5000ll:                                    // RE: 0x5CF020 (180)
            t.cos = -1.0; t.negSin = -0.0; t.sin = 0.0; break;
        case 0x274A48A7800ll:                                    // RE: 0x5CF040 (270)
            t.cos = 0.0; t.negSin = 1.0; t.sin = -1.0; break;
        default: {                                               // RE: 0x5CEEF1 general path
            const double r = static_cast<double>(a) / kFullTurn * kTwoPi;
            t.sin = std::sin(r);
            t.cos = std::cos(r);
            t.negSin = -t.sin;
            break;
        }
    }
    t.cos2 = t.cos;
    return t;   // zero20 / zero28 stay 0.0 (RE: 0x5CEF4F / 0x5CEF54 write xmm6 = 0)
}

// RE 0x5CEE50's tag != 0 path: 0x5CEF62 .. 0x5CEFB9. xmm6 is ZERO by then (every path does
// `pxor xmm6, xmm6`: 0x5CEF1C on the general path, and each cardinal branch), so every `* xmm6`
// term vanishes and the six stores become:
//     5CEF7D  addsd xmm2, xmm7     ; xmm7 = -sin*0 = 0
//     5CEF8A  [out+0x00] = cos + 0            = cos
//     5CEF85  addsd xmm8, xmm1     ; xmm1 = cos*0 = 0
//     5CEF9F  [out+0x08] = sin + 0            = sin
//     5CEFA9  [out+0x10] = sin                = sin      (the same value, not -sin)
//     5CEF96  subsd xmm2, xmm9     ; xmm2 = sin*0
//     5CEFAF  [out+0x18] = 0 - cos            = -cos
//     5CEFB4  [out+0x20] = 0 ; 5CEFB9 [out+0x28] = 0
// i.e. {cos, +sin, sin, -cos, 0, 0}, whose determinant is -1: a REFLECTION. So the element's tag
// selects between a rotation and a mirror -- which is exactly what a `tag` on a candidate element
// would be for.
inline AngleTransform mirroredAngleTransform(geom::fixed_t deg) {
    const AngleTransform r = angleTransform(deg);
    AngleTransform m;
    m.cos = r.cos;        // RE: 0x5CEF8A
    m.negSin = r.sin;     // RE: 0x5CEF9F  (+0x08 holds +sin here)
    m.sin = r.sin;        // RE: 0x5CEFA9  (+0x10 holds +sin too)
    m.cos2 = -r.cos;      // RE: 0x5CEFAF
    m.zero20 = 0.0;       // RE: 0x5CEFB4
    m.zero28 = 0.0;       // RE: 0x5CEFB9
    return m;
}


struct CandidateElement {
    std::uintptr_t identity = 0;   // RE: the element's pointer, used as the loop's rbx
    unsigned char tag = 0;         // RE: 0x5C4CD0(element) = `movzx eax, byte [rcx]`   (element+0)
    std::int64_t angle = 0;        // RE: 0x5C4CE0(element) = `mov rax, [rcx+8]`        (element+8)
};

// ---------------------------------------------------------------------------
// RE 0x5D38C0: the affine transform it applies to the source points
// ---------------------------------------------------------------------------
// Two identical blocks (0x5D3BA8 and 0x5D3C90) do, with the six doubles of an AngleTransform at
// rdi = {+0x00 cos, +0x08 -sin, +0x10 sin, +0x18 cos, +0x20 tx, +0x28 ty}:
//     5D3BC0  xmm0 = [rcx+8]        ; y
//     5D3BD2  xmm1 = [rcx-0x10]     ; x
//     5D3BD7  xmm2 = xmm9 * xmm0    ; cos * y      (xmm9 = [rdi+0x18] = cos)
//     5D3BDB  xmm3 = xmm5 * xmm1    ; sin * x      (xmm5 = [rdi+0x10] = sin)
//     5D3BE8  xmm2 += xmm3 ; 5D3BEC xmm2 += [rdi+0x28]
//     5D3BFA  [rcx-8] = xmm2                        ; y' = sin*x + cos*y + ty
//     5D3BDF  xmm0 *= xmm8          ; -sin * y     (xmm8 = [rdi+0x08] = -sin)
//     5D3BE4  xmm1 *= xmm4          ; cos * x      (xmm4 = [rdi+0x00] = cos)
//     5D3BF1  xmm0 += xmm1 ; 5D3BF5 xmm0 += [rdi+0x20]
//     5D3BFF  [rcx-0x10] = xmm0                     ; x' = cos*x - sin*y + tx
//     5D3C09  xmm4 = cos*cos ; 5D3C0E xmm5 = sin*(-sin) ; 5D3C13 xmm4 -= xmm5
//     5D3C17  ucomisd 0, xmm4                       ; the determinant cos^2 + sin^2 is checked
// NOTE the exact fields 0x5D38C0 uses: [rdi+0x00] = cos, [rdi+0x08] = negSin, [rdi+0x10] = sin,
// [rdi+0x18] = cos2. Using -sin and cos instead of negSin and cos2 happens to be equivalent for a
// pure rotation (where negSin == -sin and cos2 == cos) but is WRONG for the reflection that
// 0x5CEE50's tag != 0 path builds; the tests caught exactly that.
inline double transformX(const AngleTransform& t, double x, double y) {
    return t.cos * x + t.negSin * y + t.zero20;   // RE: 0x5D3BFF
}
inline double transformY(const AngleTransform& t, double x, double y) {
    return t.sin * x + t.cos2 * y + t.zero28;     // RE: 0x5D3BFA
}
inline double transformDet(const AngleTransform& t) {
    // computed at 0x5D3C09 / 0x5D3C0E / 0x5D3C13, then checked against 0 at 0x5D3C17
    return t.cos * t.cos2 - t.sin * t.negSin;
}

// The candidate's height, which is what 0x133DE0 feeds to the Squeezer as 20 * height:
// the transform above moves every point, and the height is the span of the resulting Y range.
// 0x5C8C50 (decoded in findings section 14.2) is the min/max accumulation that produces the box.
inline double transformedHeight(const std::vector<geom::FPoint>& points, const AngleTransform& t) {
    if (points.empty()) return 0.0;
    geom::FPoint p0 = points.front();
    double minY = transformY(t, geom::toDouble(p0.x), geom::toDouble(p0.y));
    double maxY = minY;
    for (const geom::FPoint& p : points) {
        const double y = transformY(t, geom::toDouble(p.x), geom::toDouble(p.y));
        if (y < minY) minY = y;    // RE: 0x5C8C69 style min/max updates
        if (y > maxY) maxY = y;
    }
    return maxY - minY;
}

// The candidate's width as well, since 0x13C380's path needs max(height, width).
inline double transformedWidth(const std::vector<geom::FPoint>& points, const AngleTransform& t) {
    if (points.empty()) return 0.0;
    geom::FPoint p0 = points.front();
    double minX = transformX(t, geom::toDouble(p0.x), geom::toDouble(p0.y));
    double maxX = minX;
    for (const geom::FPoint& p : points) {
        const double x = transformX(t, geom::toDouble(p.x), geom::toDouble(p.y));
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
    }
    return maxX - minX;
}

// RE 0x137FE0: the drain loop that turns source records into candidate records
// ---------------------------------------------------------------------------
// 0x133DE0 builds a one-element container for it:
//     133EBB  operator new(0x10)
//     133EC9  [rax+0x00] = rdi                     ; the angle transform from 0x5CEE50
//     133EDF  rbx = 0x271000000000
//     133EE9  [rax+0x08] = rbx
// The immediate splits by byte offset as  byte[+0x08] = 0x00  and  u32[+0x0c] = 0x00002710 = 10000,
// so a source record is 16 bytes: { void* source @0x00 ; u8 tag @0x08 ; u32 count @0x0c }.
// 0x137FE0 then does, per record:
//     137FF8  call 0x136C00(rcx)                 ; initialise the target object
//     137FFD  rbx = [rsi] ; 138000 rdi = [rsi+8] ; 138004 if (begin == end) return
//     138010  esi = dword [rbx+0x0c]             ; the record's count
//     138013  if (esi == 0) -> next record       ; a zero count skips the record
//     138040  edx = byte [rbx+0x08]              ; the tag
//     138052  rcx = [rbx]                        ; the source pointer
//     138055  al = 0x137A90(rcx, edx, rbp, r12)  ; the merge
//     13805A  if (al == 0) -> next record
//     13805E  --esi ; if (esi == 0) -> next record
//     138063  jmp 0x138040                       ; otherwise retry the SAME record
inline constexpr std::uint32_t kSourceRecordCap = 10000;   // RE 0x271000000000, u32 at +0x0c

struct SourceRecord {
    std::uintptr_t source = 0;      // [+0x00]
    unsigned char tag = 0;          // [+0x08]
    std::uint32_t count = 0;        // [+0x0c]
};

// The recovered loop. `merge(source, tag)` returns true while it produced another candidate.
template <class MergeFn>
void drainSources(const std::vector<SourceRecord>& records, MergeFn merge) {
    for (const SourceRecord& r : records) {
        std::uint32_t n = r.count;
        if (n == 0) continue;            // RE: 0x138013
        while (merge(r.source, r.tag)) { // RE: 0x138055 / 0x13805A
            if (--n == 0) break;         // RE: 0x13805E
        }
    }
}

// ---------------------------------------------------------------------------
// Where the candidate angles come from (RE 0x5C4C50 / 0x8BEFC0 / 0x134470's own setup)
// ---------------------------------------------------------------------------
// 0x5C4C50 is four instructions:
//     5C4C50  mov rax, [r8]        ; arg3 points at the angle
//     5C4C53  mov byte [rcx], dl   ; element[+0x00] = the tag
//     5C4C55  mov [rcx+8], rax     ; element[+0x08] = that angle
// so it writes exactly one CandidateElement, not a set.
//
// 0x8BEFC0 (308 B) then builds the vector: it allocates, calls 0x5C4C50 once for the appended
// element, copies the source container's 16 byte elements, and stores
//     8BF092  [vec+0x00] = the new buffer
//     8BF098  [vec+0x08] = buffer + copiedBytes + 0x10 + 0x10   ; source elements + 1 appended
//     8BF09C  [vec+0x10] = buffer + the allocation size
inline void writeCandidateAngle(CandidateElement& e, unsigned char tag, std::int64_t angle) {
    e.tag = tag;      // RE: 0x5C4C53
    e.angle = angle;  // RE: 0x5C4C55
}

// RE 0x8BEFC0: the source elements followed by one {tag, angle} element.
inline std::vector<CandidateElement> candidateAngles(const std::vector<CandidateElement>& source,
                                                     unsigned char tag, std::int64_t angle) {
    std::vector<CandidateElement> out = source;   // RE: the copy loop at 0x8BF051..0x8BF06F
    CandidateElement appended;                    // RE: the 0x5C4C50 call at 0x8BF03A
    writeCandidateAngle(appended, tag, angle);
    out.push_back(appended);
    return out;
}

// RE 0x13450B: the axis angle 90 degrees (the same magic the sin block uses).
inline constexpr geom::fixed_t kAxisAngle90 = 0xD18C2E2800ll;

// RE: 0x134470's own setup before its loop
//     1344E2  byte [rsp+0x3f] = 0 ; 1344F3 [rsp+0x40] = 0
//     1344FC  call 0x8BEFC0(vec, tag = 0, angle = 0)        ; source + the 0 degree element
//     134506  byte [rsp+0x3f] = 0 ; 13450B rax = 0xD18C2E2800 ; 13451D [rsp+0x40] = rax
//     134532  call 0x5C4C50(end, tag = 0, angle = 90 degrees) ; append the 90 degree element
//     13453C  end += 0x10 ; 134540 [rsp+0x78] = end
// so the set the search walks is: the source's own angles, then 0 degrees, then 90 degrees --
// every one of them with tag 0.
inline std::vector<CandidateElement> axisAlignedCandidates(
    const std::vector<CandidateElement>& source) {
    std::vector<CandidateElement> out = candidateAngles(source, 0, 0);   // RE: 0x1344FC
    CandidateElement ninety;                                            // RE: 0x134532
    writeCandidateAngle(ninety, 0, kAxisAngle90);
    out.push_back(ninety);
    return out;
}

// RE 0x5CEE50(transform, element + 8): the transform built from the element's own angle, WITH the
// recovered dispatch on the element's tag. 0x5CEF5E tests `byte [element+8]` and, when it is
// non-zero, rewrites the six doubles into the reflection of mirroredAngleTransform.
inline AngleTransform nodeAngleTransform(const ScoreNode& n) {
    if (nodeSourceTag(n) != 0) return mirroredAngleTransform(nodeSourceAngle(n));  // RE: 0x5CEF60
    return angleTransform(nodeSourceAngle(n));
}

// RE 0x1366BE..0x1366E7 (inside 0x136350): the +0x99 flag is set from the FIRST optional slot --
//     1366BE  al = byte [rbx+0x48]                        ; that slot's presence byte
//     1366C6  xmm1 = 1e-06 ; 1366CE xmm0 = [rbx+0x60] ; 1366D3 xmm0 -= [rbx+0x50] ; fabs
//     1366E0  ucomisd xmm1, xmm0 ; 1366E4 setae al
//     1366E7  byte [rbx+0x99] = al
// i.e. "the first slot is present AND its two outer values are equal within 1e-06" (v[2] - v[0]).
inline bool nodeSlotFlag99(const ScoreNode& n) {
    if (!n.slotAt48.present) return false;                              // RE: 0x1366C2 je -> al = 0
    const double d = std::fabs(n.slotAt48.value.v[2] - n.slotAt48.value.v[0]);
    return 1e-06 >= d;                                                  // RE: 0x1366E0 setae
}

// RE 0x1366ED..0x1366F9 plus 0x1368A9: the +0x98 flag, the exact mirror of +0x99 on the SECOND
// optional slot. 0x1366ED reads that slot's presence byte and, when non-zero, jumps to 0x1368A9:
//     1368A9  xmm1 = [0x9BCEE0] = 1e-06
//     1368B1  xmm0 = [rbx+0x88] ; 1368B9 xmm0 -= [rbx+0x78] ; 1368BE andpd (fabs)
//     1368C6  ucomisd xmm1, xmm0 ; 1368CA setae al
//     1368CD  jmp 0x1366F9  ->  byte [rbx+0x98] = al
// so it is "present AND |v[2] - v[0]| <= 1e-06" over the slot at +0x70 (values at +0x78..+0x90),
// exactly like +0x99 over the slot at +0x48 (values at +0x50..+0x68). An earlier revision of this
// file only reproduced the presence test -- that was half right and is corrected here.
inline bool nodeSlotFlag98(const ScoreNode& n) {
    if (!n.slotAt70.present) return false;                              // RE: 0x1366ED jne -> 0x1368A9
    const double d = std::fabs(n.slotAt70.value.v[2] - n.slotAt70.value.v[0]);
    return 1e-06 >= d;                                                  // RE: 0x1368C6 setae
}

// RE 0x4F7600 / 0x4F7690: two nine-byte accessors into the same heap object reached through
// Part+0x70; their tail calls resolve to an identity and to a +0x90 offset:
//     4F7600  mov rcx,[rcx+0x70] ; jmp 0x547610     ; 547610 = mov rax,rcx ; ret
//     4F7690  mov rcx,[rcx+0x70] ; jmp 0x547670     ; 547670 = lea rax,[rcx+0x90] ; ret
// i.e. `*(Part+0x70)` and `*(Part+0x70) + 0x90`.
inline constexpr std::size_t kPartGeometryObject = 0x70;   // RE: both accessors
inline constexpr std::size_t kPartGeometryField = 0x90;    // RE: 0x547670

// RE 0x13670F: element+0xa0 is written from 0x135C70's return value; the chain that produces
// that double is implemented as dllArea()/nodeAreaValue() below (it ends in the shoelace area
// 0x5CC6A0). 0x135030 reads it as the numerator of the ratio at 0x137C76.


// ---------------------------------------------------------------------------
// RE 0x5CF6B0 (235 B): the same affine map, specialised to exactly two points
// ---------------------------------------------------------------------------
//     5CF6C9  xmm0 = [r8+0x10] ; 5CF6D5 xmm1 = [r8]      ; cos / sin
//     5CF6CF  xmm4 = [r8+0x18] ; 5CF6DA xmm6 = [r8+8]    ; cos / -sin
//     5CF6E6  xmm7 = [r8+0x20] ; 5CF6EC xmm5 = [r8+0x28] ; tx / ty
//     5CF6E3..5CF72E  copy the source's four qwords (two points) into the output
//     5CF70B  xmm3 = x * cos ; 5CF717 xmm9 = y * -sin ; 5CF732 xmm3 += xmm9
//     5CF748  xmm3 += tx ; 5CF750 [out] = x'
//     5CF70F  xmm2 = x * sin ; 5CF725 xmm8 = y * cos ; 5CF73D xmm2 += xmm8
//     5CF74C  xmm2 += ty ; 5CF759 [out+8] = y'
//     ... the identical arithmetic again for the second point at +0x10/+0x18
// which is exactly transformX/transformY -- an independent confirmation of them.
struct FPoint2 {
    double x = 0.0;
    double y = 0.0;
};

inline FPoint2 transformPoint(const AngleTransform& t, double x, double y) {
    FPoint2 p;
    p.x = transformX(t, x, y);   // RE: 0x5CF750 (and 0x5CF78C for the second point)
    p.y = transformY(t, x, y);   // RE: 0x5CF759 (and 0x5CF791 for the second point)
    return p;
}

// ---------------------------------------------------------------------------
// RE 0x8C4FF0 (147 B): the Elem48 container's destructor, which confirms the strides
// ---------------------------------------------------------------------------
//     8C5010  rsi = [rdi+0x20] ; rbx = [rdi+0x18]        ; a nested vector's end/begin
//     8C5020  free each nested element, `add rbx, 0x18`  ; ★ 24 byte records
//     8C5047  free [rdi]                                 ; the element's first pointer
//     8C5054  `add rdi, 0x30`                            ; ★ 48 byte elements
//     8C5073  jmp operator delete                        ; the outer buffer
inline constexpr std::size_t kElem48Stride = 0x30;     // RE: 0x8C5054 `add rdi, 0x30`
inline constexpr std::size_t kRecord18Stride = 0x18;   // RE: 0x8C502D `add rbx, 0x18`

// RE 0x5CE7F0 (381 B): a SECOND instantiation of the angle -> transform algorithm
// Its constants are identical to 0x5CEE50's: the modulo magic 0x9C5FFF26ED75ED55 (0x5CE801), the
// turn 0x34630B8A000 (0x5CE822) and the four cardinal comparisons 0xD18C2E2800 / 0x1A3185C5000 /
// 0x274A48A7800 (0x5CE83F / 0x5CE852 / 0x5CE865). 0x136350 calls it at 0x13645B with
// 0x1A3185C5000, i.e. to build the 180 degree transform under which it stores the element's
// mirrored copy of the container.
inline constexpr geom::fixed_t kHalfTurn180 = 0x1A3185C5000ll;   // RE: 0x13645B

inline AngleTransform halfTurn() {
    return angleTransform(kHalfTurn180);   // cos = -1, sin = 0 (and -sin = -0.0)
}

// ---------------------------------------------------------------------------
// Elem16 and RE 0x134D70: the flag computation for element +0x40 / +0x41
// ---------------------------------------------------------------------------
// 0x134D70 (437 B / 101 insns) scans the container at element +0x00 with a 0x10 stride
// (`0x134E57 add rax, 0x10`), so that container's records are 16 byte points: Elem16 is
// `{double x, double y}`. The chain is treated as CLOSED -- the scan starts with
//     134E27  xmm3 = [rdx-0x10] ; 134E2F xmm1 = [rdx-8]      ; the LAST point
// and the first iteration compares against it (0x134E2C `cmp rdx, rax` / `jne 0x134E68`).
// Constants: 1e-06 at 0x9BCEE0 (0x134DFF) and the fabs mask 0x9BCED0 (0x134DF1).
// The result is sticky: `esi` is initialised to 1 at 0x134DC0 and only ever cleared at 0x134EDD,
// so the per-element answers AND together -- which is why one chain can be handled at a time here.
LCNS_NOT_REVERSED(row.135040);
struct Elem16 {
    double x = 0.0;   // [+0x00]
    double y = 0.0;   // [+0x08]
};
inline constexpr std::size_t kElem16Stride = 0x10;      // RE: 0x134E57 `add rax, 0x10`
inline constexpr double kChainEpsilon = 1e-06;          // RE: 0x9BCEE0

// ---------------------------------------------------------------------------
// RE 0x5CC6A0 (135 B): the shoelace AREA, and 0x5C51A0 (178 B): a container copy
// ---------------------------------------------------------------------------
// This is what 0x135C70 returns, and 0x135C70's result is stored into element+0xa0 by 0x13670F --
// so the numerator of the ratio at 0x137C76 is an AREA. 0x5CC6A0 in full:
//     5CC6B2  call 0x5C5260 (identity) ; rax = [rax+8]     ; the container's end
//     5CC6BE  xmm6 = [rax-0x10]                            ; the LAST point's x
//     5CC6C3  xmm7 = [rax-8]                               ; ... and its y  (a CLOSED ring)
//     5CC6D1  rdx = [rax] (begin) ; 5CC6D4 rcx = [rax+8] (end) ; 5CC6DB je -> empty
//     5CC6E4  xmm1 = [rax+8] (curY) ; 5CC6ED xmm2 = [rax-0x10] (curX)
//     5CC6F5  xmm6 *= xmm1          ; prevX * curY
//     5CC6F9  xmm7 *= xmm2          ; prevY * curX
//     5CC6FD  xmm6 -= xmm7          ; prevX*curY - prevY*curX
//     5CC705  xmm0 += xmm6          ; accumulate
//     5CC70F  xmm0 *= [0x9DE910] = 0.5
// i.e. `area = 0.5 * sum(prev.x*cur.y - prev.y*cur.x)` with prev starting at the last point.
LCNS_NOT_REVERSED(row.135780);
inline constexpr double kAreaHalf = 0.5;   // RE 0x9DE910

inline double dllArea(const std::vector<Elem16>& ring) {
    if (ring.empty()) return 0.0;                       // RE: 0x5CC6DB je
    double prevX = ring.back().x;                       // RE: 0x5CC6BE
    double prevY = ring.back().y;                       // RE: 0x5CC6C3
    double sum = 0.0;                                   // RE: 0x5CC6CD pxor
    for (const Elem16& p : ring) {
        sum += prevX * p.y - prevY * p.x;               // RE: 0x5CC6F5..0x5CC705
        prevY = p.y;                                    // RE: 0x5CC701
        prevX = p.x;                                    // RE: 0x5CC709
    }
    return sum * kAreaHalf;                             // RE: 0x5CC70F
}

// RE 0x5C51A0 (178 B): a container copy -- it allocates `end - begin` bytes (0x5C51E9
// operator new), stores begin/end/cap (0x5C51F1/0x5C51F4/0x5C51F8) and copies the 16 byte
// elements (0x5C5215..0x5C522E). 0x135C70 calls it at 0x135FCE before 0x5CC6A0 at 0x135FD6.
inline std::vector<Elem16> copyRing(const std::vector<Elem16>& ring) {
    return ring;   // RE: 0x5C51A0
}

// The full chain that produces element+0xa0 (0x13670F), all hops verified:
//     0x13670F  [element+0xa0] = xmm0
//     0x135FD6  call 0x5CC6A0(copy)      ; <- the returned double
//     0x135FCE  call 0x5C51A0(copy, src) ; a container copy
//     0x135DB1  cmova min-scan on +0x08  ; find the bottom-most vertex
//     0x135F90..0x135FBE  an in-place reversal of a sub-range (vertex-order normalisation)
// so element+0xa0 is the (signed) AREA of a ring normalised to start at its bottom-most vertex.
// That names the numerator of the 0x137C76 ratio: `area / cfg[+0x08]`.
inline double nodeAreaValue(const std::vector<Elem16>& ring) {
    return dllArea(copyRing(ring));
}

// ---------------------------------------------------------------------------
// RE 0x5D3430 (1156 B): the translated copy of a point chain
// ---------------------------------------------------------------------------
// Zero rodata constants; only twelve floating point instructions, in two identical blocks:
//     5D3700  xmm0 = [rax]        ; 5D3708 xmm0 += [rbx]        ; 5D370C [rax-0x10] = xmm0
//     5D3711  xmm0 = [rax-8]      ; 5D3716 xmm0 += [rbx+8]      ; 5D371B [rax-8] = xmm0
// (repeated at 0x5D3750). `rbx` is arg3 and holds the displacement pair, so every 16 byte point
// is moved by it. The single ret at 0x5D37A3 returns rax = [rsp+0x90], which is arg1 (saved at
// 0x5D344A) -- an out-parameter style result, i.e. `0x5D3430(out, src, offset) -> out`.
// 0x1355C0 calls it at 0x13562D with the NEGATED pair from the bounding box (0x135620 xorpd -0.0),
// i.e. to normalise a ring to the origin.
inline std::vector<Elem16> translatedCopy(const std::vector<Elem16>& src, double dx, double dy) {
    std::vector<Elem16> out = src;              // RE: the four operator new sites
    for (Elem16& p : out) {
        p.x += dx;                              // RE: 0x5D3708 / 0x5D3758
        p.y += dy;                              // RE: 0x5D3716 / 0x5D3766
    }
    return out;                                 // RE: 0x5D378B `mov rax,[rsp+0x90]`
}

// ---------------------------------------------------------------------------
// The last two sub-calls, characterised with their constants (not transcribed in full)
// ---------------------------------------------------------------------------
// RE 0x135040 (1396 B): a tolerance matching routine. Constants: 0x9BCEE8 = 0.005 (a DIFFERENT
// rodata address from the squeezer's 0x9BCFD8, although the same value), the fabs mask 0x9BCED0
// and 0x9BCEE0 = 1e-06. Its floating point work is `addsd` with the 0.005 (0x13516A) and paired
// `subsd` + `andpd`(fabs) + `ucomisd` tolerance tests; it frees an Elem48 container (0x8C4FF0)
// and has a single ret at 0x135258.
inline constexpr double kMergeAlignTolerance = 0.005;   // RE: 0x9BCEE8 (not 0x9BCFD8)

// RE 0x135780 (1250 B): assembles a 32 byte two-point record from a point chain under 1e-06
// tolerance comparisons (0x13588A..0x1358CA against the fabs mask 0x9BCED0), writing four
// doubles at 0x135A37/0x135A3F/0x135A45/0x135A4B, and calling the row translation unit's own
// helpers 0x134890 and 0x134C10. Single ret at 0x135987.
inline constexpr std::size_t kTwoPointRecord = 0x20;    // RE: 0x135A37..0x135A4B

// Labels L40/L53/L57/L80/L95/Lb7 mirror the addresses 0x134E40/0x134E53/0x134E57/0x134E80/
// 0x134E95/0x134EB7. `node` holds the three doubles the caller passes in rdx ([rbx]/[rbx+0x10]/
// [rbx+0x18], combined with `maxsd` at 0x134DD0/0x134DD6) and bboxMaxX is [rsp+0x40] (0x134DC5).
inline bool chainMonotone(const std::vector<Elem16>& chain, const double node[3], double bboxMaxX) {
    if (chain.empty()) return true;                                     // RE: 0x134DEB je
    const double m10 = (node[0] > node[1]) ? node[0] : node[1];         // RE: 0x134DD0 maxsd
    const double m9 = (node[0] > node[2]) ? node[0] : node[2];          // RE: 0x134DD6 maxsd
    const double w = bboxMaxX;                                          // RE: 0x134DC5 [rsp+0x40]
    std::size_t i = 0;                                                  // rax
    double xmm3 = chain.back().x;                                       // RE: [rdx-0x10]
    double xmm1 = chain.back().y;                                       // RE: [rdx-8]
    double xmm2 = 0.0;
    double xmm0 = 0.0;
L68:
    xmm2 = chain[i].y;                                                  // RE: 0x134E68
    if (std::fabs(xmm2 - xmm1) <= kChainEpsilon) {                      // RE: 0x134E7E jae -> L40
        xmm0 = w - m10 + kChainEpsilon;                                 // RE: 0x134E40..0x134E49
        if (xmm0 < xmm1) goto L80;                                      // RE: 0x134E51 jb
        goto L53;
    }
    goto L80;
L53:
    xmm0 = chain[i].x;                                                  // RE: 0x134E53
L57:
    ++i; xmm1 = xmm2; xmm3 = xmm0;                                      // RE: 0x134E57..0x134E5F
    if (i == chain.size()) return true;                                 // RE: 0x134E66 je -> next element
    goto L68;
L80:
    xmm0 = w - m9;                                                      // RE: 0x134E80
    if (xmm1 >= xmm0) goto L95;                                         // RE: 0x134E8D jae
    if (xmm2 < xmm0) goto L53;                                          // RE: 0x134E93 jb
L95:
    xmm0 = std::fabs(xmm2 - w);                                         // RE: 0x134E95
    if (kChainEpsilon < xmm0) goto Lb7;                                 // RE: 0x134EA6 jb
    xmm1 = std::fabs(xmm1 - w);                                         // RE: 0x134EA8
    if (kChainEpsilon >= xmm1) goto L53;                                // RE: 0x134EB5 jae
Lb7:
    xmm0 = chain[i].x;                                                  // RE: 0x134EB7
    xmm1 = xmm0 - xmm3;                                                 // RE: 0x134EBB
    xmm3 = xmm1;                                                        // RE: 0x134EC3
    if (kChainEpsilon >= std::fabs(xmm1)) goto L57;                     // RE: 0x134ED0 jae
    if (0.0 <= xmm1) goto L57;                                          // RE: 0x134ED7 jbe
    return false;                                                       // RE: 0x134EDD xor esi,esi
}

// The caller side (0x136350): the two flags are this predicate applied to the element's own
// chain (0x13643E -> +0x40) and to its 180 degree transformed copy (0x136484 -> +0x41).
// Because `esi` is never reset to 1, ANDing the per-chain answers is equivalent.
inline bool chainFlags(const std::vector<std::vector<Elem16>>& chains, const double node[3],
                       double bboxMaxX) {
    for (const std::vector<Elem16>& c : chains) {
        if (!chainMonotone(c, node, bboxMaxX)) return false;
    }
    return true;
}

// RE 0x134470: walk the candidate elements, keep the one with the SMALLEST score, skipping the
// ones the authorisation predicate rejects, and report whether one was accepted.
template <class ScoreFn>
int bestCandidate(const std::vector<CandidateElement>& elements,
                  const std::vector<AuthRecord>& records, ScoreFn score, double* bestScore) {
    int best = -1;
    double bestValue = 0.0;
    for (std::size_t i = 0; i < elements.size(); ++i) {
        const CandidateElement& e = elements[i];
        if (!authorized(records, e.tag, e.angle)) continue;   // RE: 0x1345F4 test al,al
        const double v = score(e);                            // RE: 0x134604 call 0x133DE0
        if (best < 0 || v < bestValue) {                       // RE: 0x13460E ucomisd + jbe
            best = static_cast<int>(i);
            bestValue = v;
        }
    }
    if (bestScore) *bestScore = bestValue;
    return best;
}

struct SqueezeResult {
    bool present = false;   // RE: the presence byte the routine writes at [out+0]
    double value = 0.0;     // RE: the double at [out+8]
};

// The recovered cost. Returns present == false wherever the original bails out to the
// "not applicable" path (feature off, an absent slot, unequal list lengths, an element pair
// further apart than 0.005, or a zero length direction).
//
// NOTE: the original also ASSERTS `distance != 0` (0x13821C / 0x1383EF, building a message that
// contains the word "distance" and throwing through 0x60A620). A reconstruction cannot abort, so
// that case is reported as present == false; the assertion text is recorded in the RE document.
SqueezeResult squeezeCost(const SqueezeContext& ctx);

// RE: 0x5C22D0 is applied to the unit direction of A and the sine is taken from it.
// Exposed for tests; equals the sine of the direction angle.
double directionSine(double ux, double uy);

// ---------------------------------------------------------------------------
// RE: Row::Squeezer (vtable address point 0xA3B1F0, slot 2 = 0x13A360)
// ---------------------------------------------------------------------------
// The original keeps two std::map keyed by an address range; a query is answered from the cache
// when an entry covers it, otherwise 0x1380D0 is evaluated and the entry is inserted, and the
// value is read back from the node at +0x30.
//
// The recovered hit predicate (0x13A394..0x13A3A2) is
//     hit  <=>  lo <= entry.keyLo  &&  hi <= entry.keyHi
// which is implemented literally here. The original stores the entries in a red-black tree; this
// reconstruction scans a vector with the same predicate (the tree is only an index, so the
// hit/miss decision is unchanged). That substitution is structural, not semantic.
    /** The 0x270 byte object RE 0x138A20 allocates and stores at Squeezer + 8.
     *
     *      0x138A6B  mov byte [rax + 8], 1        ; enabled
     *      0x138A72  movsd [rax], xmm2           ; the coefficient, the constructor's second argument
     *      0x138A79  movsd [rax + 0x10], xmm3    ; the threshold, its third
     *      0x138A8F  addsd xmm7, xmm6            ; TWICE the first argument
     *      0x138A9A  call 0x2530D0               ; and 0x2530D0 is given (twiceMaxExtent, coefficient)
     *      0x138A7E  call 0x500710               ; the sub-object at +0x20
     *      0x138AAD  mov byte [rsp + 0x50], 0x73 ; the one character string "s"
     *      0x138ADA  mov [rbx + 0x258], rax      ; and two tree headers at +0x210 and +0x240
     *
     *  **THE SCALARS LIVE HERE AND NOT IN Squeezer**, which is why the class was reported as having unsupported members: nothing writes +0x08,
     *  +0x10 or +0x18 of the Squeezer object itself.
     */
    struct Impl {
        bool enabled = true;              // +0x08, RE 0x138A6B, and 0x1380D0 tests it with `cmp byte [rdx + 8], 0`
        double coeff = 0.0;               // +0x00, RE 0x138A72 -- the constructor's second argument
        double threshold = 0.0;           // +0x10, RE 0x138A79 -- its third
        double twiceMaxExtent = 0.0;      // RE 0x138A8F: addsd xmm7, xmm6, handed to 0x2530D0

        /** THE NODE OF BOTH TREES, RE 0x13A390 through 0x13A3A4: `{link @0x18, lowerKey @0x20, upperKey @0x28}`. **Two 64 bit keys per node**,
         *  which is a bounding box -- and it is the very `lo`/`hi` pair `cost` below already takes. */
        struct Node {
            Node* link = nullptr;         // +0x18, RE 0x13A3A4: mov rax, [rax + 0x18]
            std::uintptr_t lowerKey = 0;  // +0x20, RE 0x13A390: mov rdx, [rax + 0x20]
            std::uintptr_t upperKey = 0;  // +0x28, RE 0x13A399: cmp rsi, [rax + 0x28]
        };

        /** **TWO TREES, and the two instructions that read their heads are four bytes apart.**
         *  RE 0x13A379: `lea r8, [rdi + 0x248]` is the head a walk starts from, with the root at +0x250 by 0x13A36C.
         *  RE 0x13A3EB: `lea rdx, [rdi + 0x240]` is the tree the insert goes INTO. */
        Node* lookupHead = nullptr;       // +0x248, RE 0x13A379
        Node* lookupRoot = nullptr;       // +0x250, RE 0x13A36C
        Node* cacheTree = nullptr;        // +0x240, RE 0x13A3EB
    };

    /** RE 0xA3B1F0, three slots. **ITS OWN STATE IS ONE POINTER.** The constructor installs the vtable at +0, allocates the 0x270 byte Impl and
     *  stores it at +8, and touches nothing else of this object -- so `Impl` is where the fields are, and this class is the handle.
     *
     *  The cost path below the constructor reads the SCALARS through that pointer, which is why `enabled`, `threshold`, `coeff` and
     *  `twiceMaxExtent` are accessors here rather than members. */
    class Squeezer {
    public:
        Squeezer() = default;
        Squeezer(double twiceMaxExtent, double coeffAt0x18, double thresholdAt0x10);

        bool enabled() const { return impl_ != nullptr && impl_->enabled; }
        double threshold() const { return impl_ != nullptr ? impl_->threshold : 0.0; }
        double coeff() const { return impl_ != nullptr ? impl_->coeff : 0.0; }
        double twiceMaxExtent() const { return impl_ != nullptr ? impl_->twiceMaxExtent : 0.0; }

        /** RE 0x13A360, vtable slot 2: the insert into the tree at inner +0x240. */
        void insert(std::uintptr_t keyLo, std::uintptr_t keyHi, double value);
        std::size_t size() const { return cache_.size(); }
        void clear();

        std::size_t hits() const { return hits_; }
        std::size_t misses() const { return misses_; }

        /** The cost of a key, RE 0x13A360 and the routine around it: a cache hit returns the stored value, and a miss computes one. Its body is
         *  in lcns/src/row.cpp beside the instructions. */
        double cost(std::uintptr_t lo, std::uintptr_t hi, const SqueezeContext& ctx);

    private:
        // RE 0x138B5C: mov [rbp + 8], rbx -- THE ONLY MEMBER OF THIS OBJECT THE CONSTRUCTOR WRITES.
        Impl* impl_ = nullptr;             // +8, and the 0x270 byte object it points at holds the state

        // THE MODEL'S OWN CACHE, NOT THE MODULE'S. The module keeps a tree at inner +0x240; this keeps a vector, and says so, because the
        // tree's routines (0x13A360 and 0x13C380) have not been read.
        struct Entry {
            std::uintptr_t keyLo = 0;
            std::uintptr_t keyHi = 0;
            double value = 0.0;
        };
        std::vector<Entry> cache_;
        std::size_t hits_ = 0;
        std::size_t misses_ = 0;
    };

// ---------------------------------------------------------------------------
// RE: 0x13C380 (416 B) -- how a row set turns into a Squeezer
// ---------------------------------------------------------------------------
// Recovered instruction by instruction:
//     wrapper = operator new(0xA10)                  ; 2576 bytes
//     wrapper[+0x00] = <the row container>           ; rbp = rdx
//     copy 9 qwords from the config object (r8) to wrapper[+0x08 .. +0x38]
//     xmm9 = config[+0x10] ; xmm8 = config[+0x18]
//     xmm6 = 0
//     for (row = container.begin; row != container.end; ++row) {
//         call 0x133190 ; call 0x5CD800(scratch, that)   ; -> bool at [rsp+0x20], 4 doubles at
//                                                        ;    [rsp+0x28], [rsp+0x30], [rsp+0x38],
//                                                        ;    [rsp+0x40]
//         if (![rsp+0x20]) {
//             d0 = [rsp+0x40] - [rsp+0x30];          // |v3 - v1|
//             d1 = [rsp+0x38] - [rsp+0x28];          // |v2 - v0|
//             xmm6 = 2 * max(d0, d1);                // 0x13C456 compare, then `addsd x,x` doubling
//         }
//     }
//     call 0x136B80(&squeezer, xmm6, xmm8, xmm9)     ; Squeezer(2*maxExtent, cfg[+0x18], cfg[+0x10])
//     wrapper[+0x48 .. +0xA07] = int[0x270] filled with 1
//     *out = wrapper
//
// The output of 0x5CD800 is a BOUNDING BOX, which 0x5C8C50 proves by updating its fields with
// min/max against another box:
//     5C8C50  cmp byte [rdx],0 ; je 0x5C8C60 ; ret   -- a non zero flag on the SOURCE means
//                                                     "nothing to do", so it returns early
//     5C8C69  xmm0 = [rdx+0x08] ; xmm1 = [rcx+0x08] ; if (xmm1 > xmm0) [rcx+8] = xmm0
//     5C8C88  if ([rcx+0x18] < xmm0) [rcx+0x18] = xmm0
//     5C8C94  xmm0 = [rdx+0x10] ...
// so the layout is { bool @+0, minX @+8, minY @+0x10, maxX @+0x18, maxY @+0x20 } -- 0x28 = 40
// bytes, exactly the object 0x13C380 reads at [rsp+0x20].
//
// Consequently, in 0x13C380:
//     13C43E  xmm1 = [rsp+0x40] - [rsp+0x30]   ==  maxY - minY  == height
//     13C444  xmm0 = [rsp+0x38] - [rsp+0x28]   ==  maxX - minX  == width
//     13C460  doubles the larger one            ==  2 * max(width, height)
//
// The flag polarity recovered from both use sites (0x5C8C50's early return and 0x13C380's
// `jne 0x13C464` that skips the arithmetic) is: NON ZERO means "skip". It is therefore named
// skipExtent here rather than "valid", which would invert the meaning.
struct RowView {
    bool skipExtent = false;              // RE: [rsp+0x20] / [rdx+0]; != 0 means skip
    double v[4] = {0.0, 0.0, 0.0, 0.0};   // RE: minX @+8, minY @+0x10, maxX @+0x18, maxY @+0x20
};

// `configAt0x10` -> xmm9 (the threshold), `configAt0x18` -> xmm8.
Squeezer buildSqueezer(const std::vector<RowView>& rows, double configAt0x10,
                       double configAt0x18);

}  // namespace row
}  // namespace lcns
