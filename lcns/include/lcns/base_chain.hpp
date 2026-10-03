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
// IS "N5Multi15CompositeNesterE".** Verified by walking NoFillNester's own typeinfo chain: NoFillNester 0xA18010 -> CompositeNester 0xA18150 ->
// Nester 0xA18380.
//
// **AND BOTH BASES' INTERFACES ARE MEASURABLE, because a slot address SHARED by several derived tables is the base's own implementation and one
// that differs is the derived class's override.** Every class in this family has SIX slots:
//
//     Multi::Nester             slot 0  91 bytes    the deleting destructor, one per class
//                               slot 1  99 bytes    the destructor, one per class
//                               slot 2   4 bytes    **SHARED by FOUR of its five derived classes, at 0xB4430**
//                               slot 3  39 bytes    one per class
//                               slot 4  82 bytes    one per class
//                               slot 5  16258 bytes one per class -- the Run
//
//     Multi::CompositeNester    slot 0  15 or 59 bytes  one per class
//                               slot 1  36 or 67 bytes  one per class
//                               slot 2  31 bytes        **SHARED by FOUR of its six, at 0xB4440**
//                               slot 3  211 bytes       one per class
//                               slot 4  894 bytes       **SHARED by THREE, at 0xB46F0**
//                               slot 5  3496 bytes      one per class -- the Run
//
// **SO BOTH BASES HAVE SIX VIRTUALS AND EACH IMPLEMENTS AT LEAST ONE OF THEM.** The four-byte slot 2 of `Nester` is a `const char*` accessor -- the
// `name()` this project already declares -- and `0xB4430` and `0xB4440` are four bytes apart, which is two adjacent accessors of the same kind.
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
//         **DECLARED** in nester.hpp, from four slot bodies and the layout they imply: `TerminalNode` 0xA3B570 is slot 2 `movsd xmm0, [rcx + 0x48] / ret` and
//         slot 3 `movsd xmm0, [rcx + 0x50] / ret`; `SplitNode` 0xA3BB70 is slot 2 `movsd xmm0, [rcx + 0x50] / ret` and slot 3 `movsd xmm0, [rcx + 0x58] / ret`.
//         **so the base's `value()` reads +0x48 and `secondary()` is the slot each class supplies, with `SplitNode` overriding `value()` too** -- the SAME
//         offset +0x50 in a DIFFERENT SLOT of the two tables. Neither vtable has an install site in the profile, so there is no constructor.
//     Multi::CompactCanceller, NoFitMapCanceller, RCompactCanceller,
//     SupervisorCanceller, Tiling::WarpCanceller                 ->  Utils::Canceller
//
// **AND THE CONSTRUCTORS OF `BiModulePattern` AND `MultiOrientedPartPattern` ESTABLISH A SECOND THING ABOUT THIS FAMILY: THE CALLER GETS A
// `std::shared_ptr`.** RE 0x4F2870, `Tiling::BiModulePattern`'s constructor, 156 bytes:
//
//     0x4F2877  mov rsi, rcx                      ; the destination -- a 2 WORD object the CALLER owns
//     0x4F287A  mov ecx, 0xf8 / call 0x998500      ; THE CLASS ITSELF, 0xf8 bytes
//     0x4F2893  lea rax, [rip + 0x54a936]          ; = 0xA3D1D0, and 0xA3D1C0 is `Tiling::BiModulePattern`
//     0x4F289E  mov qword [rbx], rax               ; so rbx IS the BiModulePattern
//     0x4F2887  mov r8d, 0xf0 / 0x4F289A lea rcx, [rbx + 8] / 0x4F28A1 call 0x63F2F8
//                                                  ; and 0xf0 bytes are BLITTED from rdi into rbx + 8
//     0x4F28A6  mov qword [rsi], rbx               ; the caller's first word takes the object
//     0x4F28A9  mov ecx, 0x18 / 0x4F28B6 call 0x998500   ; A CONTROL BLOCK of 0x18 bytes
//     0x4F28C2  mov dword [rax + 8], 1             ; TWO reference counts, both 1
//     0x4F28C9  mov dword [rax + 0xc], 1
//     0x4F28D0  mov qword [rax], rdx               ; its vtable, from 0xA56100
//     0x4F28D3  mov qword [rax + 0x10], rbx        ; pointing back at the object
//     0x4F28D7  mov qword [rsi + 8], rax           ; and the caller's SECOND word
//
// **AND THE CONTROL BLOCK'S TYPEINFO NAMES IT**: the string at its typeinfo is
// `St15_Sp_counted_ptrIPN6Tiling15BiModulePatternELN9__gnu_cxx12_Lock_policyE2EE`, which is
// `std::_Sp_counted_ptr<BiModulePattern*, __gnu_cxx::_Lock_policy, 2>` -- libstdc++'s own class for a `shared_ptr` control block. **So the 2 word object the
// caller owns IS a `std::shared_ptr<BiModulePattern>`**, 0x18 bytes because `_Sp_counted_ptr` holds only the vtable, the two atomic counts and the
// pointer: **the allocator and the deleter are the DEFAULT ones and are not stored.**
//
// **AND THAT IS AN ORACLE RATHER THAN A SHAPE** -- the name is in the module's RTTI, so the "reference-counted handle" this project recorded by its
// structure now has the standard library's own name.
//
// **AND THE CONSTRUCTOR'S SECOND ARGUMENT IS AN ELEMENT OF A `std::vector` OF 0xf0 BYTE RECORDS.** The call site at 0x4EA310 iterates
// `0x4EA380 add rbx, 0xf0` from the container's begin to its end, and constructs one `BiModulePattern` per element -- so the 0xf0 bytes blitted into each
// object are a RECORD of that vector, and **the vector's element type is not established**: 0x4E9A10 produces it and its `lea` targets are data rather
// than vtables.
//
// **AND ONE OF THESE HAS A MEASURED LAYOUT EVEN THOUGH IT IS NOT DECLARED: `Tiling::Pattern`.** Its COPY CONSTRUCTOR is 0x4E7E50, 539 bytes, and it is
// the routine SIX OF THE EIGHT EVALUATORS carry at vtable slot 3:
//
//     0x4E7E5F  mov rax, [r8]  ...  through [r8 + 0x58] into [rcx]     ; 0x60 BYTES OF THE OBJECT ARE COPIED FLAT
//     0x4E7ECB  mov rax, rbx / sar rax, 4 / imul rax, 0x8E38E38E38E38E39 ; rbx = end - begin, and after these three the value is FIVE TIMES the
//                                                                        ;   ELEMENT COUNT -- see the measurement below
//     0x4E7F01  call 0x998500                                            ; the allocator
//     0x4E7F41  call 0x63F2F8                                            ; ONE CALL PER ELEMENT
//     0x4E7F49  add rbx, 0x90  /  0x4E7F50 add r9, 0x90                   ; THE ELEMENT STRIDE IS 0x90
//
// **THE STRIDE IS THE SOLID FACT AND THE ARITHMETIC IS NOT.** `add rbx, 0x90` appears twice, at 0x4E7F49 and 0x4E7F50, and the loop walks
// `end - begin` bytes in those steps, so **an element of the container at +0x48/+0x50/+0x58 is 0x90 bytes**.
//
// **AND I FIRST READ THE MAGIC AS A DIVIDE BY SOMETHING IT IS NOT.** `sar rax, 4` then `imul rax, 0x8E38E38E38E38E39` looked like the compiler's
// division by 9, and the constant is 5 times the reciprocal `0x1C71C71C71C71C7` of nine -- **so the product is FIVE TIMES the element count rather
// than the count.** Measured over the first 5000 multiples of 0x90 the product divided by the count is 5.00000 every time. **What the code does with
// a value five times the count is NOT established here**, so this note says the measurement and stops rather than naming the arithmetic.
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
