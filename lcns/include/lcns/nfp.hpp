// lcns/nfp.hpp -- No-Fit-Polygon map and its cache.
//
// Recovered structure (re/REPORT.md 7.1, findings_geometry.md):
//   NoFitGeometry (== NFPMap handle) = 24 bytes { std::vector<Polygon> result @+0x00 }
//       -> NoFitGetNumberOfExternalPolygons (0x89D0) is (end-begin)/48
//       -> DeleteNoFitGeometry (0x8A10) recurses with a 0x30 stride
//   NoFitContext = 240 bytes (0xF0):
//       +0x78  std::map<Key(4 x int64), std::vector<Polygon>>   NFPMap cache
//       +0xA8  a second, isomorphic map
//       +0xD8  total number of cached polygons; > 19,999,999 (0x1312CFF) clears the cache
//       +0xE8  m_max_complexity (NoFitSetMaximumComplexity 0x9930 writes it; default 25000)
//   NoFitNesting = 32 bytes { void* ctx; std::vector<40-byte record> }
//       -> NoFitAddNestedPart (0xA9D0) pushes {Part*, bool flip, double, double, double}
// This header models the same behaviour with STL containers. Where the original uses a
// real polygon boolean union (..\exact\boolean.cpp, which we did NOT decompile) we keep a
// list of polygons and answer membership queries against the list; this is documented on
// every affected API.
#pragma once

#include <cstddef>
#include <cstdint>
#include <unordered_map>
#include <vector>

#include "lcns/geom.hpp"
#include "lcns/model.hpp"

namespace lcns {

// The 4 x int64 cache key from the original map.
struct NFPKey {
    std::int64_t a = 0;  // part index
    std::int64_t b = 0;  // sheet index
    std::int64_t c = 0;  // orientation step
    std::int64_t d = 0;  // flip (0/1)
    bool operator==(const NFPKey& o) const { return a == o.a && b == o.b && c == o.c && d == o.d; }
};

struct NFPKeyHash {
    std::size_t operator()(const NFPKey& k) const noexcept {
        std::size_t h = 1469598103934665603ull;
        auto mix = [&h](std::int64_t v) {
            h ^= static_cast<std::size_t>(v);
            h *= 1099511628211ull;
        };
        mix(k.a); mix(k.b); mix(k.c); mix(k.d);
        return h;
    }
};

// One cached no-fit geometry: the polygon list plus the data needed to query it.
struct NFPEntry {
    NFPKey key;
    int partIndex = -1;
    int sheetIndex = -1;
    bool flipped = false;
    double angle = 0.0;
    geom::Polygon sheetOutline;
    geom::MultiPolygon map;      // <-- "NoFitGeometry": vector<Polygon>

    std::size_t polygonCount() const { return map.size(); }
};

class NoFitMap {
public:
    static constexpr int kDefaultMaxComplexity = 25000;         // 0x61A8
    static constexpr std::size_t kCacheClearThreshold = 19999999;  // 0x1312CFF
    static constexpr double kTolerance = 1e-6;                  // 0x9AC818

    explicit NoFitMap(int maxComplexity = kDefaultMaxComplexity);

    // RE GetNoFitMap (0x8AC0) / GetNoFitPlacementMap (0xA620):
    // cache lookup, otherwise compute and insert.
    const NFPEntry& get(const Order& order, int partIndex, int sheetIndex, bool flip, int angleStep,
                        double angleRadians);

    void setMaximumComplexity(int c);          // RE NoFitSetMaximumComplexity 0x9930
    int maximumComplexity() const;

    void clear();                              // cache eviction
    std::size_t cachedPolygons() const;
    std::size_t entryCount() const;
    bool tooComplex() const;

    // Build the no-fit geometry for one (part, sheet, orientation) pair.
    // For a convex part vs. convex sheet this is exactly
    //     MinkowskiSum(sheet, reverse(part))
    // i.e. the locus of part-reference translations at which the part touches the sheet
    // boundary; candidate placements are generated from it.
    static NFPEntry build(const Order& order, int partIndex, int sheetIndex, bool flip,
                          int angleStep, double angleRadians);

private:
    std::unordered_map<NFPKey, NFPEntry, NFPKeyHash> cache_;
    int maxComplexity_;
    std::size_t cachedPolygons_ = 0;
};

// RE: NoFitNesting = 32 bytes { void* ctx; std::vector<40-byte record> }
struct NoFitPlacement {
    int partIndex = -1;
    bool flipped = false;
    double x = 0.0;
    double y = 0.0;
    double angle = 0.0;
};

class NoFitNesting {
public:
    NoFitNesting(NoFitMap& map, int sheetIndex);

    // RE NoFitAddNestedPart (0xA9D0)
    void addNestedPart(const NoFitPlacement& p);
    // RE DeleteNoFitNesting (0x9500)
    void clear();

    const std::vector<NoFitPlacement>& placements() const { return placements_; }
    int sheetIndex() const { return sheetIndex_; }

    // Forbidden region for `partIndex` at this orientation = union of NFP(part, placedPart)
    // over every already placed part on this sheet. Returned as a polygon LIST because we
    // do not implement the original's boolean union; use contains()/intersects() below.
    geom::MultiPolygon forbiddenRegion(const Order& order, int partIndex, bool flip,
                                      double angle, const geom::MultiPolygon& partShape) const;

    // Membership test against the forbidden list.
    static bool forbiddenContains(const geom::MultiPolygon& region, geom::FPoint reference);
    static bool forbiddenIntersects(const geom::MultiPolygon& region, const geom::MultiPolygon& shape);

private:
    NoFitMap* map_;
    int sheetIndex_;
    std::vector<NoFitPlacement> placements_;
};

}  // namespace lcns
