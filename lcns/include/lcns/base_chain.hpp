// lcns/include/lcns/base_chain.hpp -- the module's INHERITANCE, read out of its own RTTI.
//
// **WHY THIS FILE EXISTS.** Every class in lcns/ was written as a STANDALONE type, and the module's classes are not: a whole layer of ABSTRACT
// BASES was missing from the tree, which is why a field would appear at +0x10 with nothing to own it, and why `Row::Squeezer` looked like a handle
// with a vtable and one pointer instead of a `Distancer`.
//
// THE EVIDENCE IS THE MODULE'S OWN RTTI, NOT A SHAPE. In the Itanium C++ ABI a single-inheritance typeinfo is
//
//     __si_class_type_info  { vptr, name*, base* }
//
// so a class's base is the typeinfo its own +0x10 points at, and the base's name is a string in the module:
//
//     Row::Squeezer     vtable 0xA3B1E0, typeinfo 0xA17E00
//         at 0xA17E00: "N3Row8SqueezerE"
//         at +0x10:    -> typeinfo 0xA17E60 whose name is "N3Row9DistancerE"
//
// **AND AN ABSTRACT BASE HAS NO INSTANTIATED VTABLE, so it is NOT a key in re/vtables.json** -- which is exactly why these classes were never
// noticed. `Multi::Nester`, `Tiling::Evaluator`, `Multi::CompositeNester`, `Row::Distancer`, `Engine::Engine` and `Multi::Node` are all absent from
// that file and all present in the module.
//
// Regenerate with `python -u re/g_base_chain.py --out re/base_chains.txt`, which reads re/vtables.json and the module's bytes.
#pragma once

namespace lcns {

/** RE the RTTI typeinfo chain. **EACH ENTRY IS A `static_assert`ABLE FACT ABOUT THE MODULE'S OWN NAMES**, and each is checked in test_recovered.cpp
 *  against the declaration it implies. */
namespace base_chain {

// -------------------------------------------------------------------------------------------------------------------------------
// THE NESTER FAMILY. **TWO LAYERS, AND THE MIDDLE ONE WAS ENTIRELY MISSING.**
//
//     NoFillNester, CompactNester, FilterNester, FlipNester, LimitedNester, MultiTorchNester
//         -> Multi::CompositeNester -> Multi::Nester
//     DatabaseNester, NestingNester, RectangleNester, RowNester, TilingNester
//         -> Multi::Nester
//
// THIS IS WHERE THE +0x10 BASE GAP COMES FROM. `Multi::Nester` declares no data members here, and `NoFillNester`'s slot 5 at 0x7F240 stores
// through its object at +0x10, +0x18, +0x20 .. +0x130 with IMMEDIATE ZEROS at +0x70, +0x78 and +0x90 -- `mov qword [rbp + 0x78], 0` is a member
// being initialised and not an argument being saved. **THE FIELDS BELONG TO CompositeNester, WHOSE OWN TYPEINFO IS AT 0xA18150 AND WHOSE NAME
// IS "N5Multi15CompositeNesterE".**
inline constexpr const char* kNester = "N5Multi6NesterE";
inline constexpr const char* kCompositeNester = "N5Multi15CompositeNesterE";

// -------------------------------------------------------------------------------------------------------------------------------
// THE ROW FAMILY. **`Row::Squeezer` IS A `Row::Distancer` AND WAS WRITTEN AS A STANDALONE HANDLE.**
//
//     Row::Squeezer  ->  Row::Distancer        (typeinfo 0xA17E00 says so)
//     Row::BasicDistancer is a SEPARATE sibling with its own vtable at 0xA3B1B0
inline constexpr const char* kRowDistancer = "N3Row9DistancerE";

// -------------------------------------------------------------------------------------------------------------------------------
// THE ENGINE FAMILY. **EVERY CONCRETE ENGINE DERIVES FROM `Engine::Engine`, WHICH IS ABSENT FROM re/vtables.json.**
//
//     InfiniteEngine, MultiEngine, DelayedEngine, NestingEngine, CompositeEngine, EquivalentEngine, CloudEngine  ->  Engine::Engine
inline constexpr const char* kEngineEngine = "N6Engine6EngineE";

// -------------------------------------------------------------------------------------------------------------------------------
// THE OBSERVER FAMILY. **`Structure::Observer`, NOT A BASE INVENTED HERE.**
//
//     Engine::BestObserver, Engine::CompositeObserver, Engine::EquivalentObserver,
//     Multi::NestingObserver, Multi::TraceObserver                              ->  Structure::Observer
// and Structure::Observer HAS an instantiated vtable at 0xA53550 with six slots.
inline constexpr const char* kStructureObserver = "N9Structure8ObserverE";

// -------------------------------------------------------------------------------------------------------------------------------
// THE TILER FAMILY. **`Tiling::MultiTiler` IS THE BASE OF BOTH MULTI TILERS AND WAS MISSING.**
//
//     Tiling::BoxMultiTiler, Tiling::SqueezeMultiTiler  ->  Tiling::MultiTiler
inline constexpr const char* kTilingMultiTiler = "N6Tiling10MultiTilerE";

// -------------------------------------------------------------------------------------------------------------------------------
// THE EVALUATOR FAMILY. **SIX CLASSES IN lcns/tiling.hpp DERIVE FROM A BASE THAT IS ABSENT FROM re/vtables.json.**
//
//     DensityEvaluator, UnlimitedDensityEvaluator, UnlimitedXDensityEvaluator,
//     QuantityEvaluator, ReusableEvaluator, ObliqueEvaluator, MultitorchEvaluator,
//     OldMultitorchEvaluator                                     ->  Tiling::Evaluator
inline constexpr const char* kTilingEvaluator = "N6Tiling9EvaluatorE";

// -------------------------------------------------------------------------------------------------------------------------------
// THE PATTERN FAMILY.
//
//     Tiling::BiModulePattern, Tiling::MultiOrientedPartPattern  ->  Tiling::Pattern
//     Tiling::CompositePart                                      ->  Tiling::Part
//     Tiling::BasicCandidater                                    ->  Tiling::Candidater
//     Multi::AllSheetSelector and its siblings                   ->  Multi::SheetSelector
//     Multi::AdvancedStrategist                                  ->  Multi::Strategist
//     Multi::SplitNode, Multi::TerminalNode                      ->  Multi::Node
//     Multi::CompactCanceller, NoFitMapCanceller, RCompactCanceller,
//     SupervisorCanceller, Tiling::WarpCanceller                 ->  Utils::Canceller
inline constexpr const char* kTilingPattern = "N6Tiling7PatternE";
inline constexpr const char* kTilingPart = "N6Tiling4PartE";
inline constexpr const char* kTilingCandidater = "N6Tiling10CandidaterE";
inline constexpr const char* kMultiSheetSelector = "N5Multi13SheetSelectorE";
inline constexpr const char* kMultiStrategist = "N5Multi10StrategistE";
inline constexpr const char* kMultiNode = "N5Multi4NodeE";
inline constexpr const char* kUtilsCanceller = "N5Utils9CancellerE";

/** **THE CLASSES THE MODULE HAS THAT lcns/ DOES NOT DECLARE AT ALL.** Each is an abstract base whose typeinfo exists and whose vtable does not,
 *  which is why `re/vtables.json` never showed them. **Naming them from the module's own strings is what this list is for** -- the alternative
 *  would be inventing a name like `NesterBase`, which is the placeholder this project forbids.
 *
 *  A `const char* const[]` rather than a `constexpr` array, because an array of pointers to separately declared constants is not a constant
 *  expression in C++17. */
inline const char* const kUndeclaredAbstractBases[] = {
    "N5Multi6NesterE",                    // Multi::Nester
    "N5Multi15CompositeNesterE",          // Multi::CompositeNester  -- the fields at +0x10 belong HERE
    "N3Row9DistancerE",                   // Row::Distancer          -- Squeezer's base
    "N6Engine6EngineE",                   // Engine::Engine          -- every concrete engine's base
    "N9Structure8ObserverE",              // Structure::Observer     -- has a vtable at 0xA53550
    "N6Tiling10MultiTilerE",              // Tiling::MultiTiler
    "N6Tiling9EvaluatorE",                // Tiling::Evaluator       -- eight evaluators derive from it
    "N6Tiling7PatternE",                  // Tiling::Pattern
    "N6Tiling4PartE",                     // Tiling::Part
    "N6Tiling10CandidaterE",              // Tiling::Candidater
    "N5Multi13SheetSelectorE",            // Multi::SheetSelector
    "N5Multi10StrategistE",               // Multi::Strategist
    "N5Multi4NodeE",                      // Multi::Node
    "N5Utils9CancellerE",                 // Utils::Canceller
};

}  // namespace base_chain
}  // namespace lcns
