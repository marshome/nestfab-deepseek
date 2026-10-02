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
class MultiOrientedPartPattern {
public:
    explicit MultiOrientedPartPattern(int partIndex);
    void addOrientation(double angleRadians, bool flipped);
    void setCellSize(double w, double h);
    void setSpacing(double spacing) { spacing_ = spacing; }

    std::vector<PatternCell> layout(double sheetW, double sheetH, int budget) const;
    std::size_t orientationCount() const { return orientations_.size(); }

private:
    struct Orientation {
        double angle;
        bool flipped;
    };
    int partIndex_;
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
class BoxMultiTiler {
public:
    void add(const std::shared_ptr<Evaluator>& e) { evaluators_.push_back(e); }
    // returns the best scoring pattern among the candidates
    std::vector<PatternCell> best(const std::vector<std::vector<PatternCell>>& candidates,
                                 double sheetArea, double* score) const;

private:
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
