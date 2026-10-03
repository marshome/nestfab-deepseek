// lcns/tiling.hpp -- repeated-pattern tiling.
//
// Mirrors the recovered `Tiling::` namespace (re/REPORT.md 7.0, findings_engine.md):
//   Tiling::BoxMultiTiler, Tiling::SqueezeMultiTiler  -- tilers
//   Tiling::BiModulePattern          (vtable 0xA3D1C0, 8 slots)
//   Tiling::MultiOrientedPartPattern (vtable 0xA3D370, 8 slots)
//   Tiling::DensityEvaluator / UnlimitedDensityEvaluator / UnlimitedXDensityEvaluator
//   Tiling::QuantityEvaluator / ReusableEvaluator / ObliqueEvaluator
//   Tiling::MultitorchEvaluator / OldMultitorchEvaluator
//   Tiling::PackerCache, Tiling::CompositePart, Tiling::Part, Tiling::WarpCanceller,
//   Tiling::BasicCandidater
// The original lays repeated modules over the sheet and then packs the pattern; this header
// provides the pattern generators and the evaluators that score them.
#pragma once

#include <memory>
#include <string>
#include <vector>

#include "lcns/geom.hpp"
#include "lcns/model.hpp"
#include "lcns/pattern.hpp"

namespace lcns {
namespace tiling {

// RE ..\tiling\packer_cache.cpp (276 functions / 278,386 bytes; re/findings_packer_cache.md) --
// the pattern catalogue the cache is keyed by. These are the literals the binary passes around,
// read out of the tiling functions (0x765460, 0x769410, 0x763ee0, 0x158810):
//   box, box_min_dist, cc_matrix, cc_mono, cc_specific, composite_bi, composite_box,
//   composite_dual_bi, composite_mono, min_box_bi, mono, oblique_bi, oblique_pentagon,
//   part, pentagon, windmill
// (the option key `enable_composite_tiling` and the guard `!shear` come from the same TU).
inline constexpr const char* kPatternKeys[] = {
    "box", "box_min_dist", "cc_matrix", "cc_mono", "cc_specific", "composite_bi", "composite_box",
    "composite_dual_bi", "composite_mono", "min_box_bi", "mono", "oblique_bi",
    "oblique_pentagon", "part", "pentagon", "windmill",
};
inline constexpr std::size_t kPatternKeyCount = sizeof(kPatternKeys) / sizeof(kPatternKeys[0]);

// The four tiling entry points of the same TU (names recovered from the assertion strings):
//   ComputeMonoTilings 0x158810, ComputeMinBoxBiTilings 0x765460,
//   ComputePartTilings 0x765460,  ComputeCommonCutMonoTilings 0x769410
// and the getters GetPart 0x768b80 / 0x76a010, GetCommonCutPart 0x764a80 / 0x769410,
// SetPartAuthorizations 0xc1a0, plus OppositePattern and the thread pool that logs
// "Packer Cache max threads: " / "Thread <n> ... updating part ... tilings." (0x763ee0, 0x76a130).

// One pre-computed placement inside a pattern (sheet coordinates).
struct PatternCell {
    int partIndex = -1;
    double x = 0.0;
    double y = 0.0;
    double angle = 0.0;   // radians
    bool flipped = false;
    geom::Box footprint;
    double area() const { return footprint.area(); }
};

// RE Tiling::PackerCache: memoises one computed pattern per (sheet, part, orientation) key.
/** RE 0xA3D0E0, two slots. **ITS OWN STATE IS ONE POINTER AT +8.** RE 0x159480, 98 bytes:
 *
 *      0x15948F  mov [rcx], rax                    ; the vtable at +0
 *      0x159495  mov ecx, 0x1E0 / call 0x998500     ; AN INNER OBJECT of 0x1E0 bytes
 *      0x1594BC  call 0x76A130                      ; constructed from (this, rdx, r8d, r9b)
 *      0x1594C1  mov [rsi + 8], rbx                 ; AND STORED AT PackerCache + 8
 *
 *  so this class is `{vptr @0, impl* @8}`, and the inner object at 0x76A130 is what actually caches. The two arguments the constructor
 *  forwards are an **int** and a **bool**: they are saved as `r8d` and `r9d` and reloaded as `r8d` and a zero-extended `r9b`.
 */
class PackerCache {
public:
    void clear();
    std::size_t size() const { return entries_; }
    void store(const std::string& key);
    bool contains(const std::string& key) const;

    /** RE 0x1594C1: the object at +8 that this handle owns and forwards to. */
    void* impl() const { return impl_; }

private:
    // RE 0x15948F: the vtable is at +0, so this is a polymorphic handle.
    void* impl_ = nullptr;             // +8, RE 0x1594C1: mov [rsi + 8], rbx

    // **THE MODEL'S OWN STORAGE, NOT THE MODULE'S.** The module caches inside the 0x1E0 byte object; this keeps a vector and says so, because
    // 0x76A130 -- the routine that fills that object -- has not been read.
    std::vector<std::string> keys_;
    std::size_t entries_ = 0;
};

// RE Tiling::BiModulePattern: two modules A and B alternate in a repeating cell.

// ---------------------------------------------------------------------------
// the two pattern classes -- **BOTH DERIVE FROM `Tiling::Pattern`**, by the typeinfo chains
// N6Tiling15BiModulePatternE -> N6Tiling7PatternE and N6Tiling21MultiOrientedPartPatternE -> N6Tiling7PatternE.
//
// **AND THAT DERIVATION WAS ABSENT FROM THIS TREE UNTIL `lcns/pattern.hpp` EXISTED**, because the base is abstract and therefore not a key in
// `re/vtables.json` -- so nothing here had noticed it. `Tiling::Pattern`'s own measured facts, including the copy constructor at 0x4E7E50 that SIX OF THE
// EIGHT EVALUATORS carry at vtable slot 3, are in that header.
//
// **WHAT IS STILL OPEN**: `sizeof(Tiling::Pattern)` measured ONE WORD while a derived instance's own first member landed at +8, so SOMETHING OCCUPIES
// +0x00 that the base does not have. The constructors write a `std::shared_ptr` into a CALLER-owned 2 word object, which is a fact about the CALL rather
// than about the layout, and the two do not yet agree on which object holds what. **Recorded, not resolved.**
// ---------------------------------------------------------------------------


class BiModulePattern : public Pattern {
public:
    BiModulePattern(double moduleW, double moduleH);
    void setModules(int partA, int partB);
    void setSpacing(double spacing) { spacing_ = spacing; }

    // Lay the pattern over a sheet of the given size, stopping after `budget` cells.
    std::vector<PatternCell> layout(double sheetW, double sheetH, int budget) const;

    double moduleWidth() const { return moduleW_; }
    double moduleHeight() const { return moduleH_; }

private:
    double moduleW_;
    double moduleH_;
    double spacing_ = 0.0;
    int partA_ = -1;
    int partB_ = -1;
};

// RE Tiling::MultiOrientedPartPattern: the same part repeated in several orientations
// inside one repeating cell.
/** RE 0xA3D370, five slots. **THE CLASS IS A 0x90 BYTE OBJECT AND ITS FIELDS ARE INLINE.**
 *
 *  RE 0x4F2910, 285 bytes:
 *
 *      0x4F2917  mov rdi, rcx                      ; the destination -- a 2 word handle the CALLER owns
 *      0x4F291A  mov ecx, 0x90 / call 0x998500      ; THE CLASS, 0x90 bytes
 *      0x4F292F  lea rax, [rip + 0x54aa4a]          ; = 0xA3D380, and 0xA3D370 is THIS class
 *      0x4F2940  mov [rbx], rax                     ; so rbx IS this object
 *      0x4F2936  mov dword [rbx + 0x80], 4          ; a count of 4
 *      0x4F2943  copies 0x70 bytes from rsi into [rbx + 8] .. [rbx + 0x78]
 *      0x4F29C4  mov qword [rbx + 0x88], 0xD18C2E2800   ; = 900000000000
 *      0x4F29CB  mov [rdi], rbx                     ; the caller's handle takes the object
 *      0x4F29D6  mov ecx, 0x18 / call 0x998500       ; A CONTROL BLOCK of 0x18 bytes
 *      0x4F29F0  mov [rax], rdx                     ; its vtable at 0xA56140
 *      0x4F29E2  mov dword [rax + 8], 1             ; TWO reference counts, both 1
 *      0x4F29E9  mov dword [rax + 0xc], 1
 *      0x4F29F3  mov [rax + 0x10], rbx              ; pointing back at the object
 *      0x4F29F7  mov [rdi + 8], rax                 ; the second word of the caller's handle
 *
 *  **SO THE `{object, control}` PAIR IS A REFERENCE-COUNTED HANDLE THAT BELONGS TO THE CALLER**, and the class itself is the 0x90 bytes. Three
 *  of the class's own slots place its offsets: slot 2 at 0x7EBB90 reads +0x88, slot 3 at 0x7EB5E0 reads +0x10, and slot 4 at 0x7EBC30 reads
 *  +0x80.
 */
class MultiOrientedPartPattern : public Pattern {
public:
    /** The 0x70 bytes RE 0x4F2943 copies in, at +8 through +0x78. **Its fields are not established one by one**, so it is carried as the byte
     *  block the instruction copies rather than given names that would be guesses. */
    struct Inline {
        std::byte bytes[0x70]{};
    };

    /** What the constructor copies FROM: the same 0x70 bytes, read at rsi. **THE ROUTINE TAKES A POINTER TO THIS AND MEMCPYS IT**, so the
     *  constructor's argument is not an index. Declared before the constructor because it is a parameter type. */
    struct PatternConfig {
        std::byte bytes[0x70]{};
    };

    /** RE 0x4F2910. */
    explicit MultiOrientedPartPattern(const PatternConfig& config);

    void addOrientation(double angleRadians, bool flipped);   // the model's own; NOT a slot of the module's class
    void setCellSize(double w, double h);                     // and this one likewise
    void setSpacing(double spacing) { spacing_ = spacing; }

    /** **THE MODEL'S PART INDEX, NOT A MODULE FIELD.** The module's own index is somewhere in the 0x70 bytes it copies; this is what the port
     *  uses, so it is settable and named as the port's. */
    void setPartIndex(int index) { partIndex_ = index; }

    std::vector<PatternCell> layout(double sheetW, double sheetH, int budget) const;
    std::size_t orientationCount() const { return orientations_.size(); }

    /** The state the module keeps INLINE, which is what its own slots read. */
    std::uint32_t capacity() const { return capacity_; }        // +0x80, RE 0x4F2936 and slot 4 at 0x7EBC30
    std::uint64_t limit() const { return limit_; }              // +0x88, RE 0x4F29C4 and slot 2 at 0x7EBB90

private:
    Inline inline_{};                      // +0x08 .. +0x78, RE 0x4F2943
    std::uint32_t capacity_ = 0;           // +0x80, RE 0x4F2936: mov dword [rbx + 0x80], 4
    std::uint32_t padding_ = 0;            // +0x84, so that +0x88 is 8 byte aligned
    std::uint64_t limit_ = 0;              // +0x88, RE 0x4F29C4: movabs rax, 0xD18C2E2800

    // **THE MODEL'S OWN STORAGE, NOT THE MODULE'S.** The module's orientation data is inside the 0x70 bytes at +8; this keeps a vector so the
    // port can place the same calls, because those bytes have not been read field by field.
    struct Orientation {
        double angle;
        bool flipped;
    };
    int partIndex_ = 0;
    std::vector<Orientation> orientations_;
    double cellW_ = 0.0;
    double cellH_ = 0.0;
    double spacing_ = 0.0;
};

// ---------------------------------------------------------------------------
// evaluators -- RE Tiling::*Evaluator (4 virtual slots each)
// ---------------------------------------------------------------------------
/** **RE the eight tables below, and EVERY ONE HAS FOUR SLOTS** -- which is TWO VIRTUALS beyond the destructor pair:
 *
 *      0x76E380..0x76FA00   the deleting destructor, 1 or 5 bytes, one per class
 *      0x76E390..0x76FA10   the destructor, one per class
 *      slot 2, POSITIVE IN EVERY CLASS, and which method it is has NOT been established
 *      slot 3, 0x4E7E50 in SIX of the eight       **SHARED, AND ITS NAME IS NOT ESTABLISHED EITHER**
 *
 *  `ObliqueEvaluator` uses 0x7E8970 at slot 3 and `QuantityEvaluator` 0x7E8DA0, so the address differs in two of the eight.
 *
 *  **AND THE SHARING DOES NOT SETTLE WHICH SLOT IS WHICH.** In six of the eight, slot 3 is a routine that copies 0x60 bytes from its argument and
 *  then DEEP COPIES a container of 0x90 byte elements, calling the allocator and a per-element copy -- **a copy constructor or a clone, and not a
 *  scoring function**. So neither slot is named here: `name()` and `evaluate()` are this project's own words for them, arrived at before these
 *  tables were measured, and an earlier note presented them as if the table had said so. **A name guessed from a shape is the placeholder this
 *  project removes.** */
class Evaluator {
public:
    virtual ~Evaluator() = default;
    virtual const char* name() const = 0;
    virtual double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const = 0;
};

/** RE vtable 0xA3D210, FOUR slots. Slot 0 is the deleting destructor 0x76E390, slot 1 the destructor, slot 2 is at 0x7E8910 (81 to 798 bytes) and
 *  slot 3 is at 0x4E7E50 -- SHARED with five other evaluators.
 *  **SLOT 3 IS NOT NAMED HERE ON PURPOSE.** In six of the eight evaluators it is the SAME address, 0x4E7E50, and reading that routine
 *  shows a 0x60 byte copy followed by a DEEP COPY of a container with 0x90 byte elements -- a copy constructor or a clone, NOT a
 *  scoring function. An earlier annotation called it `evaluate()`; **what slot 3 is has not been established**, and a name guessed at
 *  from a shape is the placeholder this project removes. */
class DensityEvaluator : public Evaluator {          // used area / sheet area
public:
    const char* name() const override { return "DensityEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;
};

/** RE vtable 0xA3D3C0, FOUR slots. Slot 0 is the deleting destructor 0x76F9F0, slot 1 the destructor, slot 2 is at 0x7EBFC0 (81 to 798 bytes) and
 *  slot 3 is at 0x4E7E50 -- SHARED with five other evaluators.
 *  **SLOT 3 IS NOT NAMED HERE ON PURPOSE.** In six of the eight evaluators it is the SAME address, 0x4E7E50, and reading that routine
 *  shows a 0x60 byte copy followed by a DEEP COPY of a container with 0x90 byte elements -- a copy constructor or a clone, NOT a
 *  scoring function. An earlier annotation called it `evaluate()`; **what slot 3 is has not been established**, and a name guessed at
 *  from a shape is the placeholder this project removes. */
class UnlimitedDensityEvaluator : public Evaluator {  // density, ignoring the sheet border
public:
    const char* name() const override { return "UnlimitedDensityEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;
};

/** RE vtable 0xA3D3F0, FOUR slots. Slot 0 is the deleting destructor 0x76FA10, slot 1 the destructor, slot 2 is at 0x7EC210 (81 to 798 bytes) and
 *  slot 3 is at 0x4E7E50 -- SHARED with five other evaluators.
 *  **SLOT 3 IS NOT NAMED HERE ON PURPOSE.** In six of the eight evaluators it is the SAME address, 0x4E7E50, and reading that routine
 *  shows a 0x60 byte copy followed by a DEEP COPY of a container with 0x90 byte elements -- a copy constructor or a clone, NOT a
 *  scoring function. An earlier annotation called it `evaluate()`; **what slot 3 is has not been established**, and a name guessed at
 *  from a shape is the placeholder this project removes. */
class UnlimitedXDensityEvaluator : public Evaluator {  // density along x only
public:
    const char* name() const override { return "UnlimitedXDensityEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;
};

/** RE vtable 0xA3D270, FOUR slots. Slot 0 is the deleting destructor 0x76E410, slot 1 the destructor, slot 2 is at 0x7E8DD0 (81 to 798 bytes) and
 *  slot 3 is at 0x7E8DA0 -- this class's own.
 *  **SLOT 3 IS NOT NAMED HERE ON PURPOSE.** In six of the eight evaluators it is the SAME address, 0x4E7E50, and reading that routine
 *  shows a 0x60 byte copy followed by a DEEP COPY of a container with 0x90 byte elements -- a copy constructor or a clone, NOT a
 *  scoring function. An earlier annotation called it `evaluate()`; **what slot 3 is has not been established**, and a name guessed at
 *  from a shape is the placeholder this project removes. */
class QuantityEvaluator : public Evaluator {           // number of cells
public:
    const char* name() const override { return "QuantityEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;
};

/** RE vtable 0xA3D2A0, FOUR slots. Slot 0 is the deleting destructor 0x76E430, slot 1 the destructor, slot 2 is at 0x7E8F60 (81 to 798 bytes) and
 *  slot 3 is at 0x4E7E50 -- SHARED with five other evaluators.
 *  **SLOT 3 IS NOT NAMED HERE ON PURPOSE.** In six of the eight evaluators it is the SAME address, 0x4E7E50, and reading that routine
 *  shows a 0x60 byte copy followed by a DEEP COPY of a container with 0x90 byte elements -- a copy constructor or a clone, NOT a
 *  scoring function. An earlier annotation called it `evaluate()`; **what slot 3 is has not been established**, and a name guessed at
 *  from a shape is the placeholder this project removes. */
class ReusableEvaluator : public Evaluator {           // cells whose footprint leaves a usable offcut
public:
    const char* name() const override { return "ReusableEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;
};

/** RE vtable 0xA3D240, FOUR slots. Slot 0 is the deleting destructor 0x76E3D0, slot 1 the destructor, slot 2 is at 0x7E8B30 (81 to 798 bytes) and
 *  slot 3 is at 0x7E8970 -- this class's own.
 *  **SLOT 3 IS NOT NAMED HERE ON PURPOSE.** In six of the eight evaluators it is the SAME address, 0x4E7E50, and reading that routine
 *  shows a 0x60 byte copy followed by a DEEP COPY of a container with 0x90 byte elements -- a copy constructor or a clone, NOT a
 *  scoring function. An earlier annotation called it `evaluate()`; **what slot 3 is has not been established**, and a name guessed at
 *  from a shape is the placeholder this project removes. */
class ObliqueEvaluator : public Evaluator {            // rewards non axis aligned cells
public:
    const char* name() const override { return "ObliqueEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;
};

/** RE 0xA3D310, four slots. **ITS OWN STATE IS ONE POINTER AT +0**, and the object it points at is 0x20 bytes with three members.
 *
 *  RE 0x4E8410, 81 bytes, nearly a declaration in assembly:
 *
 *      0x4E841B  mov rbx, rcx                     ; this
 *      0x4E8419  mov ecx, 0x20 / call 0x998500     ; AN OBJECT OF 0x20 BYTES
 *      0x4E8437  lea rdx, [rip + 0x554ee2]         ; its own vtable, which is NOT 0xA3D320
 *      0x4E8447  mov dword [rax + 8], esi          ; ITS int    -- the constructor's second argument
 *      0x4E844A  movsd [rax + 0x10], xmm2          ; ITS double -- the third
 *      0x4E844F  movsd [rax + 0x18], xmm3          ; ITS double -- the fourth
 *      0x4E8454  mov [rbx], rax                    ; stored at MultitorchEvaluator + 0
 *
 *  AND THE CALL SITE CONFIRMS IT: at 0x766DCF the class is constructed on the STACK -- `lea rbx, [rsp + 0xd0]` -- with the three values read
 *  out of an option, so the class is a stack handle whose whole state is the one allocated pointer.
 */
/** RE vtable 0xA3D310, FOUR slots. Slot 0 is the deleting destructor 0x76F260, slot 1 the destructor, slot 2 is at 0x7E9240 (81 to 798 bytes) and
 *  slot 3 is at 0x4E7E50 -- SHARED with five other evaluators.
 *  **SLOT 3 IS NOT NAMED HERE ON PURPOSE.** In six of the eight evaluators it is the SAME address, 0x4E7E50, and reading that routine
 *  shows a 0x60 byte copy followed by a DEEP COPY of a container with 0x90 byte elements -- a copy constructor or a clone, NOT a
 *  scoring function. An earlier annotation called it `evaluate()`; **what slot 3 is has not been established**, and a name guessed at
 *  from a shape is the placeholder this project removes. */
class MultitorchEvaluator : public Evaluator {
public:
    /** RE 0x4E8410. **THE DECLARATION HAD ONE PARAMETER AND THE ROUTINE TAKES THREE** -- an int and two doubles, all three written into the
     *  object this class allocates. */
    MultitorchEvaluator(int torches, double first, double second);

    const char* name() const override { return "MultitorchEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;

    int torches() const { return impl_.torches; }        // RE 0x4E8447: [impl + 8]
    double first() const { return impl_.first; }         // RE 0x4E844A: [impl + 0x10]
    double second() const { return impl_.second; }       // RE 0x4E844F: [impl + 0x18]

private:
    /** The 0x20 byte object RE 0x4E8419 allocates, with its OWN vtable at +0. */
    struct Impl {
        void** vtable = nullptr;       // +0x00, RE 0x4E8444
        int torches = 0;               // +0x08, RE 0x4E8447 -- the second argument
        double first = 0.0;            // +0x10, RE 0x4E844A -- the third
        double second = 0.0;           // +0x18, RE 0x4E844F -- the fourth
    };

    Impl impl_{};                      // +0x00, RE 0x4E8454: `mov [rbx], rax`, so this object holds the allocated Impl
};

// RE Tiling::SqueezeMultiTiler / BoxMultiTiler: pick the tiler whose pattern scores best.
/** **ITS OWN STATE IS ONE POINTER AT +0, AND IT IS NOT POLYMORPHIC.**
 *
 *  RE 0x4F4850, 883 bytes:
 *
 *      0x4F4864  mov r12, rcx                  ; this
 *      0x4F486A  mov qword [rcx], 0            ; ITS ONLY MEMBER, cleared -- a POINTER, not a vtable
 *      0x4F4B10  mov ecx, 0x188 / call 0x998500 ; THE INNER OBJECT, 0x188 bytes
 *      0x4F4887  lea rax, [rip + 0x548882]      ; the INNER object's vtable, installed at its +0
 *      0x4F4AE4  mov [r12], rsi                 ; the inner object replaces the old one
 *      0x4F4AED  mov rax, [rcx] / call [rax + 8] ; AND THE OLD ONE IS RELEASED THROUGH ITS OWN VTABLE
 *
 *  **THAT LAST PAIR IS THE PROOF**: a vtable would have been installed at `[r12]` if this class had one, and the only virtual call in the
 *  routine goes through the pointer at +0 instead. So the polymorphic object is the one this class allocates.
 *
 *  AND `[rbx]` -- the second argument -- IS COMPARED AGAINST `0xD18C2E2800` at 0x4F48A7, the same constant `MultiOrientedPartPattern` stores at
 *  its +0x88. **It is a TYPE TAG**, and the comparison is how the constructor recognises what it was handed. The `r9b` test at 0x4F4861 chooses
 *  between a 0x20 byte object and the 0x188 byte one.
 */
class BoxMultiTiler {
public:
    /** RE 0x4F4850. Its second argument is a pointer whose first qword is compared against the type tag, and it has a trailing bool. */
    /** RE 0x4F4850. Its second argument is a pointer whose first qword is compared against the type tag, and it has a trailing bool. */
    BoxMultiTiler(const void* tagged, bool flag);

    /** **THE MODEL'S DEFAULT, AND IT IS NOT A MODULE CONSTRUCTOR.** The module has no zero-argument form of this class that has been read, and
     *  the port's own use of it is what needs one. */
    BoxMultiTiler() = default;

    void add(const std::shared_ptr<Evaluator>& e) { evaluators_.push_back(e); }

    /** returns the best scoring pattern among the candidates */
    std::vector<PatternCell> best(const std::vector<std::vector<PatternCell>>& candidates,
                                 double sheetArea, double* score) const;

    /** RE 0x4F4AE4: the object at +0, whose vtable is the one the constructor installs. */
    void* inner() const { return inner_; }

private:
    /** The 0x188 byte object RE 0x4F4B10 allocates, whose own vtable is installed at its +0. **The evaluator vector lives in IT**, at +8, +0x10
     *  and +0x18 -- the three words a vector needs -- and each element is 0x78 bytes (0x4F4AA5 and 0x4F4AD6 both do `add rbx, 0x78`). */
    struct Inner {
        void** vtable = nullptr;      // +0x00, RE 0x4F4887 and 0x4F4896
        void* begin = nullptr;        // +0x08
        void* end = nullptr;          // +0x10, RE 0x4F4AB0: mov [rsi + 0x10], rax
        void* capacity = nullptr;     // +0x18
    };

    Inner* inner_ = nullptr;          // +0x00, RE 0x4F486A clears it and 0x4F4AE4 replaces it

    // **THE MODEL'S OWN EVALUATOR LIST, NOT A MODULE MEMBER.** The module's lives in the `Inner` object at +8, +0x10 and +0x18 as a vector of
    // 0x78 byte elements; this keeps a vector of shared_ptr so the port can place the same calls, because those elements have not been read.
    std::vector<std::shared_ptr<Evaluator>> evaluators_;
};

class SqueezeMultiTiler {
public:
    void add(const std::shared_ptr<Evaluator>& e) { evaluators_.push_back(e); }
    // squeeze the cells towards the origin until they touch, then score
    std::vector<PatternCell> squeeze(const std::vector<PatternCell>& cells, double sheetW,
                                     double sheetH) const;

private:
    std::vector<std::shared_ptr<Evaluator>> evaluators_;
};

}  // namespace tiling
// ---------------------------------------------------------------------------
// The sheet-selector family -- RE: 0xAFD60 (NoMixSheetSelector's constructor), vtables 0xA3B840 / 0xA3B9D0 / 0xA3BA60 / 0xA3BAC0
// ---------------------------------------------------------------------------

/** **A FOUR SLOT INTERFACE, AND THE BASE ITSELF HAS NO VTABLE INSTANCE** -- the RTTI carries `N5Multi13SheetSelectorE` and `re/vtables.json` has no table for it,
 *  which is what an abstract base with no out-of-line constructor looks like. Every subclass's table is
 *
 *      slot 0  the deleting destructor          `jmp 0x9984B0`
 *      slot 1  the destructor
 *      slot 2  the selection                    FILLS THE BUFFER THE CALLER PASSES
 *      slot 3  the selector's NAME              also returns through that buffer
 *
 *  **AND SLOT 2'S `rcx` IS THE BUFFER AND NOT `this`**: `Multi::AllSheetSelector`'s body begins `mov r12, rcx` (the object) and then `mov qword [rcx], 0`,
 *  `[rcx + 8]` and `[rcx + 0x10]` -- **three stores into the CALLER'S memory**, which an earlier probe read as three of the object's own fields. **That is why
 *  the object register is established before any offset is believed.**
 *
 *  **AND SLOT 3'S CONTENT IS A NAME.** RE `Multi::AllSheetSelector` 0x7D25E0 and `Multi::LargestSheetSelector` 0x7D3CE0: each builds the three word
 *  small-string form with the bytes at +0x10 and **the LENGTH at +0x08** -- 9 for `"AllSheets"` and **0xc for `"LargestSheet"`**, which is twelve characters. */
class SheetSelector {
public:
    virtual ~SheetSelector() = default;

    /** Slot 2. **RETURNED THROUGH A BUFFER THE CALLER SUPPLIES**, which is the three word `std::vector` form: `[rcx]`, `[rcx + 8]` and `[rcx + 0x10]` are
     *  initialised and the object is returned by `ret`. **The element type is NOT established** -- the bodies index sheets, not indices -- so it is declared as
     *  `std::size_t` and marked, rather than guessed at. */
    virtual std::vector<std::size_t> select() const = 0;      // NOT REVERSED: the element type
    /** Slot 3. RE 0x7D25E0 and 0x7D3CE0, and the length field at +0x08 settling it: `"AllSheets"` and `"LargestSheet"`. */
    virtual std::string name() const = 0;
};

/** RE 0xAFD60 (671 bytes). **THE OBJECT IS 0x50 BYTES AND ITS PARTS SUM TO EXACTLY THAT**, which is what makes this class landable where its three siblings are
 *  not: `LargestSheetSelector` and `RandomSheetSelector` are built by 0xB0000 and 0xB0040, whose allocations are 0x10 and 0x9e0, and their tables' install sites
 *  are not in the profile. Six fields are placed below and ONE constructor initialises all of them.
 *
 *  **THREE OF THE SIX CARRY NO NAME, BECAUSE THE MODULE GIVES NONE.** `N5Multi18NoMixSheetSelectorE` names the class and no member string names these; the two
 *  sub-objects at +0x20 and +0x38 are built by 0x523FE0 and 0xAF7D0, whose own types this project has not read. **Their offsets, types and constructors are
 *  established and their meanings are not**, so they are named for what is known and marked. */
/** **THE GENERATOR'S TWO OFFSETS ARE SETTLED AND THE OBJECT'S EIGHT TRAILING BYTES ARE NOT.** Two constructors place the same generator and a `constexpr`
 *  difference between them is the part that does not depend on either object:
 *
 *      0x84510   0x9f8 byte object (`mov ecx, 0x9f8` at 0x084519)   mt at +0x00, mti written EIGHT bytes at +0x9C0
 *      0xB0040   0x9e0 byte object (`mov ecx, 0x9e0` at 0x0B004B)   mt at +0x18, mti written EIGHT bytes at +0x9D8
 *
 *  **and +0x9D8 - +0x18 = +0x9C0**, so `mti` sits 0x9C0 bytes after `mt` in both. **What is NOT settled is where `RandomSheetSelector`'s object ends**: the
 *  loop's 624 words reach +0x9DB, the eight bytes begin at +0x9D8, and a member can only begin at +0x9E0 -- **0x9E8 against an allocation of 0x9e0.** */
inline constexpr std::size_t kMtToMti = 0x9C0;                       // RE: 0x9D8 - 0x18, and 0x9C0 - 0x00 in the other constructor
inline constexpr std::size_t kMtWords = 0x270;                       // RE 0x0B00A8 `cmp rdx, 0x270`: 624 words
inline constexpr std::size_t kMtIndexBytes = 8;                      // RE 0x0B00B7 `mov qword [rbx + 0x9d8], 0x270`

/** RE 0xB0040 (159 bytes). **THE OBJECT IS 0x9e0 BYTES AND MOST OF IT IS A `std::mt19937`**, which is what makes the class's NAME established rather than
 *  chosen: `RandomSheetSelector` selects sheets at random and carries its own generator.
 *
 *  The constructor's loop is the MT19937 seeding algorithm, instruction for instruction:
 *
 *      0B0090  mov eax, ecx / shr eax, 0x1e / xor eax, ecx
 *      0B0097  imul eax, eax, 0x6c078965          ; 1812433253 -- THE SEEDING MULTIPLIER
 *      0B00A0  mov dword [rbx + rdx*4 + 0x18], ecx
 *      0B00A8  cmp rdx, 0x270                     ; **624 elements**
 *
 *  **and the three numbers agree with the standard generator and with the allocation**: 624 words from +0x1C, an index at +0x9D8, and 0x9D8 + 8 = **0x9e0**,
 *  which is `mov ecx, 0x9e0` at 0x0B004B. **This project already records those two instructions as the generator's signature** (`re/19_mt19937.py`), so the field
 *  is not a guess: **a name established by what a class DOES is a name with an oracle.**
 *
 *  **AND THE WHOLE OBJECT IS STILL WRITTEN OUT RATHER THAN SUMMARISED**, because a declaration that said only `std::mt19937 engine_` would hide the offsets every
 *  other function uses. The three members before it are the ones 0xB0040 writes: +0x08 the second parameter, +0x10 the third (four bytes) and +0x14 a byte
 *  returned by 0x523580. */
class RandomSheetSelector : public SheetSelector {
public:
    // +0x00  RE 0x0B006F: mov qword [rbx], rax, where rax is 0xA3BA70 -- RandomSheetSelector's vtable

    /** +0x08, RE 0x0B0061: `mov qword [rax + 8], rdi` -- the constructor's SECOND parameter, a pointer. */
    // **NAMED BY OFFSET AND NOT BY ARGUMENT POSITION.** This used to be secondArg_, while NoMixSheetSelector -- a sibling -- calls the SAME field at the SAME offset irstArg_. **Both are right about their own constructor and both are wrong as names**: this class takes its destination in rcx and its vtable object in rdx, so the pointer lands in its second argument, while the subclass next door stores its first. **The offset is the only convention that survives a change of calling shape**, so the name is the offset and 	hirdArg_ below keeps its name because BOTH classes agree those are the same four bytes at +0x10.
    void* at08_ = nullptr;
    /** +0x10, RE 0x0B006C: `mov dword [rbx + 0x10], ebp` -- the constructor's THIRD parameter, FOUR bytes. */
    std::uint32_t thirdArg_ = 0;
    /** +0x14, RE 0x0B0072 `call 0x523580` and 0x0B0077 `mov byte [rbx + 0x14], al` -- ONE BYTE, and 0x523580's return. **What it means is not recovered.** */
    std::uint8_t at14_ = 0;   // renamed from yte14_ for the same reason: the name said nothing the offset does not                         // NOT REVERSED: the byte 0x523580 returns
    /** +0x18, RE 0x0B0084: `mov dword [rbx + 0x18], 1` -- **`mt[0]`, WHICH THE SEEDING SETS TO THE SEED ITSELF.** The standard seed puts the seed in the state's
     *  FIRST word and derives the rest from it, and 0x0B00A0's loop then writes `mt[1]` .. `mt[623]` because **`mov edx, 1` at 0x0B007F starts it at ONE**:
     *  first write +0x18 + 1*4 = +0x1C, last +0x18 + 623*4 = **+0x9D7**. **So the 624 words span +0x18..+0x9D7 and `mti` at +0x9D8 does not overlap them.** */
    std::uint32_t mt_[624] = {};                      // +0x18..+0x9D7
    /** +0x9D8, RE 0x0B00B7: `mov qword [rbx + 0x9d8], 0x270` -- **EIGHT bytes at +0x9D8, which OVERLAPS the last word of the 624 above.**
     *
     *  **AND THIS IS A CONTRADICTION THAT IS RECORDED RATHER THAN SMOOTHED OVER.** Three instructions and a declaration say:
     *
     *      0x0B004B  mov ecx, 0x9e0            the constructor allocates 0x9e0 bytes
     *      0x0B00A0  mov dword [rbx + rdx*4 + 0x18], ecx for rdx = 1..0x26F    624 words, +0x1C .. +0x9DB
     *      0x0B00B7  mov qword [rbx + 0x9d8], 0x270                            eight bytes at +0x9D8
     *
     *  and a declaration carrying all three measures **0x9E8**: the words reach +0x9DB, the eight bytes at +0x9D8 overlap their last word, and the next member
     *  can only begin on an 8-byte boundary at +0x9E0. **The two arithmetic facts cannot both hold of one object.** **A field is not moved to make a number
     *  agree** -- each offset and the width above is one instruction, and so is the 0x9e0 -- so what is recorded is the measurement and the disagreement. */
    /** +0x9D8, RE 0x0B00B7: `mov qword [rbx + 0x9d8], 0x270` -- **EIGHT bytes, and +0x9D8 + 8 = 0x9e0 is exactly what 0x0B004B asks the allocator for.**
     *  The instruction's width is what settles it: a four byte member here would leave the last four bytes of the object unaccounted for. */
    std::uint64_t mtIndex_ = 0;                       // +0x9D8..+0x9DF, and the object ends at 0x9e0
};

class NoMixSheetSelector : public SheetSelector {
public:
    /** RE 0xAFD60, and every line below is one store in it. The constructor takes a destination, a pointer, an int and a pointer, allocates 0x50 bytes,
     *  installs the vtable, and returns the object through the destination. */
    NoMixSheetSelector(void** destination);

    // +0x00  RE 0xAFD98: mov qword [rbx], rax, where rax is 0xA3B9E0 -- NoMixSheetSelector's vtable

    /** +0x08, RE 0xAFD89: `mov qword [rax + 8], rsi` -- the constructor's FIRST parameter, a pointer. */
    void* firstArg_ = nullptr;
    /** +0x10, RE 0xAFD94: `mov dword [rbx + 0x10], r12d` -- the constructor's THIRD parameter, FOUR bytes. */
    std::uint32_t thirdArg_ = 0;
    /** +0x18, RE 0xAFD9B and 0xAFDAB: `mov rax, qword [rbp]` then `mov qword [rbp], 0` then `mov qword [rbx + 0x18], rax`
     *  -- **the source is CLEARED, so this is a moved-from pointer and not a copy.** */
    void* owned18_ = nullptr;
    /** +0x20, RE 0xAFD9F `lea rcx, [rbx + 0x20]` and 0xAFDAF `call 0x523FE0`. **0x18 BYTES**, because 0x523FE0 touches `rbp` at +0x0 and +0x10 and nothing else,
     *  so it reaches +0x38. **Its meaning is not recovered.** */
    std::byte member20_[0x18];                        // NOT REVERSED: a sub-object constructed by 0x523FE0
    /** +0x38, RE 0xAFDB4 `lea rcx, [rbx + 0x38]` and 0xAFDBB `call 0xAF7D0`. **0x18 BYTES**, and 0x38 + 0x18 = 0x50, which is exactly the allocation. */
    std::byte member38_[0x18];                        // NOT REVERSED: a sub-object constructed by 0xAF7D0
};

}  // namespace lcns
