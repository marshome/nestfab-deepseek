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
class BiModulePattern {
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
class MultiOrientedPartPattern {
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
class Evaluator {
public:
    virtual ~Evaluator() = default;
    virtual const char* name() const = 0;
    virtual double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const = 0;
};

class DensityEvaluator : public Evaluator {          // used area / sheet area
public:
    const char* name() const override { return "DensityEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;
};

class UnlimitedDensityEvaluator : public Evaluator {  // density, ignoring the sheet border
public:
    const char* name() const override { return "UnlimitedDensityEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;
};

class UnlimitedXDensityEvaluator : public Evaluator {  // density along x only
public:
    const char* name() const override { return "UnlimitedXDensityEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;
};

class QuantityEvaluator : public Evaluator {           // number of cells
public:
    const char* name() const override { return "QuantityEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;
};

class ReusableEvaluator : public Evaluator {           // cells whose footprint leaves a usable offcut
public:
    const char* name() const override { return "ReusableEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;
};

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
}  // namespace lcns
