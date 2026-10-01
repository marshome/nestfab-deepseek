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
class PackerCache {
public:
    void clear();
    std::size_t size() const { return entries_; }
    void store(const std::string& key);
    bool contains(const std::string& key) const;

private:
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

class MultitorchEvaluator : public Evaluator {         // rewards cells sharing torch lines
public:
    explicit MultitorchEvaluator(int nbTorches = 2) : nbTorches_(nbTorches) {}
    const char* name() const override { return "MultitorchEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;

private:
    int nbTorches_;
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
