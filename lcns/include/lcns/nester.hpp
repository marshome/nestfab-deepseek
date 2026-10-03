// lcns/nester.hpp -- placement search: strategies, beam search, pricing, compaction,
//                    finalisation and common-cut detection.
//
// Mirrors the recovered architecture (re/REPORT.md 7.2 / 7.4, findings_engine.md):
//   Multi::Nester has a 6 slot vtable: dtor, deleting dtor, Name(), Prepare(), Estimate(),
//   Run().  `Run` is always the largest function of the class, so it is the placement body.
//   Strategies recovered: Flip / Filter / NoFill / Tiling / Compact / Limited / Nesting /
//   Database / Composite / Rectangle / MultiTorch / Row, plus Pack::{Best,Knapsack,Recursive}
//   and the Tiling::* module.
//   Multi::TerminalNode::eval() reads the node value at +0x48, Multi::SplitNode::eval() at
//   +0x50 (`movsd xmm0,[rcx+0x48] / [rcx+0x50]`); the beam tree is prepared by the function
//   that logs "Preparing tree for beam " (0x22CCA0) and cached in ..\nesting\algos\tree_db.cpp
//   (FindNode 0x1C12D0).  The beam width constant was NOT recoverable, so it is a parameter.
//   NestingNester embeds its own std::mt19937 (seed constant 0x6C078965, state words 624).
#pragma once

#include "lcns/trace.hpp"   // the recovered log prefixes (no cycle)
#include <chrono>
#include "lcns/recovery.hpp"
#include <cstdint>
#include <functional>
#include <memory>
#include <random>
#include <string>
#include <vector>

#include "lcns/geom.hpp"
#include "lcns/row.hpp"
#include "lcns/model.hpp"
#include "lcns/nfp.hpp"

namespace lcns {

// ---------------------------------------------------------------------------
// randomness -- RE: Multi::NestingNester holds a std::mt19937 at [+0x38..+0x9F8]
// ---------------------------------------------------------------------------
class Random {
public:
    explicit Random(std::uint32_t seed = 5489u);
    void seed(std::uint32_t s);
    std::uint32_t next();
    double uniform(double a, double b);
    int uniformInt(int a, int b);  // inclusive
private:
    std::mt19937 engine_;
};

// ---------------------------------------------------------------------------
// cancellation -- RE: Utils::Canceller, base probeCancel() == false (0x7D7D20)
// ---------------------------------------------------------------------------
class Canceller {
public:

    virtual ~Canceller() = default;
    virtual bool probeCancel() { return cancelled_; }
    void cancel() { cancelled_ = true; }
    void reset() { cancelled_ = false; }
protected:
    bool cancelled_ = false;
};

// RE Multi::SupervisorCanceller::ProbeCancel (0x30030): elapsed / limit > 1.0
class TimeCanceller : public Canceller {
public:
    explicit TimeCanceller(double limitSeconds);
    void start();
    void setLimit(double seconds);
    double limit() const { return limit_; }
    double elapsed() const;
    bool probeCancel() override;
private:
    double limit_ = 10.0;
    std::chrono::steady_clock::time_point t0_{};
};

// RE Multi::RCompactCanceller (0x7D2CB0) is `xor eax,eax; ret` -- never cancels.
// RE Tiling::WarpCanceller::ProbeCancel (0x7E80E0, 19 bytes, seven instructions) -- a DELEGATING
// canceller, transcribed literally:
//     7E80E0  mov rcx,[rcx+8]      ; the wrapped object
//     7E80E4  test rcx,rcx ; je    ; no wrapped object -> answer false
//     7E80E9  mov rax,[rcx]        ; its vtable
//     7E80EC  jmp qword [rax+0x10] ; TAIL CALL slot 2, i.e. its own ProbeCancel
//     7E80F0  xor eax,eax ; ret
// The tail call to slot +0x10 is the same slot the base class's probe occupies, so this forwards the
// question rather than answering it.
class DelegatingCanceller : public Canceller {
public:
    explicit DelegatingCanceller(Canceller* inner = nullptr) : inner_(inner) {}
    void setInner(Canceller* inner) { inner_ = inner; }
    Canceller* inner() const { return inner_; }
    bool probeCancel() override {
        if (inner_ == nullptr) {
            return false;                  // RE 0x7E80F0: no wrapped object, answer false
        }
        return inner_->probeCancel();      // RE 0x7E80EC: tail call into slot 2
    }

private:
    Canceller* inner_ = nullptr;
};

// RE Multi::CompactCanceller::ProbeCancel (0x7D2610, 991 bytes). Its own body carries the strings
// 'm_supervisor', '..\multi\supervisor.cpp', 'Compact cancelled !' and -- recovering the METHOD NAME
// from the binary rather than guessing it -- 'ProbeCancel'. The doubles it compares against are
// 0.5, 1.05 and 60.0, and it reads the supervisor at +0x8 plus flags at +0x414/+0x415, so this probe
// asks the supervisor whether the compaction should stop. lcns models that with TimeCanceller's limit
// logic; the constants are recorded here because 1.05 is the same slack the surface check uses.

class NeverCanceller : public Canceller {
public:
    bool probeCancel() override { return false; }
};

// ---------------------------------------------------------------------------
// observers -- RE: 6 slot interface; v4 NewIntermediateSolutionFound, v5 NewNestingFound
// ---------------------------------------------------------------------------
struct Observers {
    std::function<void()> start;
    std::function<void()> stop;
    std::function<bool()> pollA;
    std::function<bool()> pollB;
    std::function<void(const Solution&)> newIntermediateSolutionFound;  // v4
    std::function<void(const Solution&)> newNestingFound;               // v5
};

/** **THE MODULE'S OWN NAME FOR THE INTERFACE `Engine::BestObserver` FORWARDS TO.** The chain is
 *  `N6Engine12BestObserverE -> N9Structure8ObserverE`, read from the module's typeinfo, so this class IS `Structure::Observer`: its name string is
 *  at 0xA311C0 and its typeinfo at 0xA1DEE0. **An earlier version of this declaration called it `ObserverSink`, a name invented here** -- which is
 *  the placeholder `re/g_base_chain.py` exists to prevent.
 *
 *  **SIX VIRTUALS, MEASURED FROM THE THREE CLASSES THAT DERIVE FROM IT** (`Engine::CompositeObserver`, `Multi::TraceObserver` and
 *  `Multi::NestingObserver`, tables at 0xA3D060, 0xA3B700 and 0xA3B7C0, every one with six slots):
 *
 *      slot 0   one per class, 1 byte             the deleting destructor
 *      slot 1   one per class, 5 bytes            the destructor
 *      slot 2   0x7C2460 in TWO of the three      `xor eax, eax` then `ret` -- THE BASE'S PLACEHOLDER FOR A PURE VIRTUAL
 *      slot 3   0x7C2470 in TWO of the three      the same
 *      slot 4   one per class, up to 4111 bytes
 *      slot 5   0x7C2480 in ONE of the three      `ret`
 *
 *  **AND THE THREE FORWARDERS FIT THAT EXACTLY**: they read the object at +0x10 and jump through `[rax + 0x10]`, `[rax + 0x18]` and `[rax + 0x28]`
 *  -- slots 2, 3 and 5. **An earlier version declared only three methods, and three methods cannot have a gap at slot 4.** The two this project
 *  does not forward are simply not forwarded, and the second is named for its slot rather than guessed at. */
class Structure_Observer {
public:
    virtual ~Structure_Observer() = default;
    virtual void offer(const Solution& solution, double score) = 0;   // slot 2, RE 0x755A47: jmp [rax + 0x10]
    virtual bool hasSolution() const = 0;                             // slot 3, RE 0x755A57: jmp [rax + 0x18]
    virtual void slot4() = 0;                                         // slot 4, NOT forwarded by BestObserver
    virtual void notify(bool finished, int offers) = 0;               // slot 5, RE 0x755A6F: jmp [rax + 0x28]
};

/** RE 0xA3CF30. **IT HOLDS ONE POINTER AT +0x10 AND FORWARDS ITS WHOLE INTERFACE TO IT.** Three of its six slots are 11, 11 and 18 bytes:
 *
 *      0x755A40  mov rcx, [rcx + 0x10] / mov rax, [rcx] / jmp [rax + 0x10]     ; slot 2
 *      0x755A50  mov rcx, [rcx + 0x10] / mov rax, [rcx] / jmp [rax + 0x18]     ; slot 3
 *      0x755A60  mov rcx, [rcx + 0x10] / movzx r8d, r8b / jmp [rax + 0x28]     ; slot 5
 *
 *  **AND THAT IS ALL THE INSTRUCTIONS ESTABLISH.** The declaration this replaces held a `Solution best_`, a `double bestScore_`, a `bool has_`
 *  and an `int offers_`, and **no instruction places any of them**: the two functions that could construct the object are the destructor pair
 *  and write only the vtable, and the constructor is not in the profile. A member nothing places is not a member.
 *
 *  A NOTE ON A TOOL, because it produced a false positive here and in `Tiling::MultiOrientedPartPattern`: counting `[rcx + N]` writes without
 *  checking that `rcx` still holds `this` reported that slot 4 at 0x755A80 writes `+0x10` through `+0x60`, and **the routine writes none of
 *  them** -- `rcx` is reloaded with other pointers inside it. **An offset is evidence only if the base register is the object.**
 */
class BestObserver : public Structure_Observer {   // RE the typeinfo chain: N6Engine12BestObserverE -> N9Structure8ObserverE
public:
    // slot 2, slot 3 and slot 5, each forwarding to the object at +0x10
    void offer(const Solution& s, double score) override;      // RE 0x755A40
    bool hasSolution() const override;                          // RE 0x755A50
    void notify(bool finished, int offers) override;            // RE 0x755A60

    /** **SLOT 4 IS NOT FORWARDED BY THIS CLASS** -- the module's own table has it, and RE 0x755A80 is the 4242 byte routine at that slot. Its body
     *  has not been read, so this says so rather than inventing one. */
    void slot4() override {}

private:
    Structure_Observer* sink_ = nullptr;             // +0x10, RE 0x755A40: mov rcx, [rcx + 0x10]
};

// ---------------------------------------------------------------------------
// pricing -- RE: Prc::PriceComputer and its four implementations.
//   BoxSurface   : the largest candidate bounding box area (y1-y0)*(x1-x0)  [0x7CB750]
//   HullSurface  : a precomputed hull surface coefficient  [0x7CA130 reads +0x48]
//   AlphaSurface : a precomputed alpha-shape coefficient   [0x7CA1B0 reads +0x68]
//   LinearCombination: sum(w_i * price_i) / sum(w_i)       [0x7CA370]
// ---------------------------------------------------------------------------
struct PriceCandidate {
    geom::Box box;
    double hullSurface = 0.0;
    double alphaSurface = 0.0;
    double demand = 1.0;
};

class PriceComputer {
public:
    virtual ~PriceComputer() = default;
    virtual const char* name() const = 0;
    virtual double price(const PriceCandidate& c) const = 0;
};

class BoxSurfacePrice : public PriceComputer {
public:
    const char* name() const override { return "BoxSurface"; }
    double price(const PriceCandidate& c) const override { return c.box.area() * c.demand; }
};

class HullSurfacePrice : public PriceComputer {
public:
    const char* name() const override { return "HullSurface"; }
    double price(const PriceCandidate& c) const override { return c.hullSurface * c.demand; }
};

class AlphaSurfacePrice : public PriceComputer {
public:
    // RE: the two AlphaPriceComputer instances 0x4D68E3 / 0x4D6907 are constructed with the
    // rodata doubles 0x9D9C08 = 0.5 and 0x9D9BE8 = 0.1, stored into the object at +0x68 (which
    // slot2 = 0x7CA1B0 returns). The two log tags 'AP ' (0x9C1C92, used by 0x220ED0) and
    // 'DP ' (0x9C1CAA, used by 0x221110) name the two variants; the RTTI names Prc::BoostAlpha
    // (0xA22260) and Prc::DimAlpha (0xA22340) are the only candidates for them, but which value
    // belongs to which name has no direct evidence, so the mapping is NOT asserted here.
    static constexpr double kBoostAlpha = 0.5;   // re/findings_lp_use.md 11.3
    static constexpr double kDimAlpha = 0.1;

    AlphaSurfacePrice() = default;
    explicit AlphaSurfacePrice(double alpha) : alpha_(alpha) {}

    const char* name() const override { return "AlphaSurface"; }
    // RE slot2 = 0x7CA1B0 is `movsd xmm0,[rdx+0x68]`: the pricer returns its stored alpha
    // coefficient (the surface value itself is precomputed into the candidate).
    double alpha() const { return alpha_; }
    double price(const PriceCandidate& c) const override {
        return (alpha_ != 0.0 ? alpha_ : 1.0) * c.alphaSurface * c.demand;
    }

private:
    double alpha_ = 1.0;
};

class LinearCombinationPrice : public PriceComputer {
public:
    void add(std::shared_ptr<PriceComputer> pc, double weight);
    const char* name() const override { return "LinearCombination"; }
    double price(const PriceCandidate& c) const override;
private:
    std::vector<std::shared_ptr<PriceComputer>> parts_;
    std::vector<double> weights_;
};

// ---------------------------------------------------------------------------
// beam search -- RE: Multi::Node / TerminalNode / SplitNode + tree_db
// ---------------------------------------------------------------------------
struct BeamParams {
    LCNS_NOT_REVERSED(search.beam_width);
int width = 8;               // NOT recovered from the binary -> tunable
    bool distinctAngle = true;   // RE key "beam_distinct_angle"
    double frequencyRatio = 1.0; // RE key "beam_frequency_ratio"
    double frequencyRatioSecondary = 0.0;   // RE 0xB3B62: a double at +0x178, eight bytes past the one above
    int maxAngleSteps = 24;
};

/** **THE THREE CLASSES THE MODULE HAS, WHICH THE PORT HAD FLATTENED INTO ONE.** The vtables and the bodies of their slots:

 *      Multi::TerminalNode   0xA3B570   4 slots   slot 2: `movsd xmm0, [rcx + 0x48] / ret`
 *                                                 slot 3: `movsd xmm0, [rcx + 0x50] / ret`
 *      Multi::SplitNode      0xA3BB70   4 slots   slot 2: `movsd xmm0, [rcx + 0x50] / ret`
 *                                                 slot 3: `movsd xmm0, [rcx + 0x58] / ret`
 *
 *  and both derive from `Multi::Node` by their typeinfo chains. **So `value()` reads +0x48 in the base, `secondary()` is the slot each class supplies, and
 *  `SplitNode` OVERRIDES `value()` as well** -- **the same offset +0x50 sits in a DIFFERENT SLOT in the two tables**, which is what a `Kind` tag with a
 *  conditional could not say, and the module has no `Kind` field anywhere.
 *
 *  **AND +0x08..+0x47 IS A REGION NO ACCESSOR READS.** The three doubles are at +0x48, +0x50 and +0x58, while a vptr and three doubles is sixteen bytes, so
 *  sixty-four bytes sit between them that no recovered function reads or writes. **They are explicit `std::byte` padding rather than named fields, because a
 *  name needs an oracle and none of the module's strings, setters or accessors names them.**
 *
 *  **AND THE ACCESSORS KEEP NEUTRAL NAMES FOR THE SAME REASON**: the module exposes them through vtable slots 2 and 3 and never names what they return. No
 *  function in the profile installs either vtable, so there is no constructor to initialise these and the members are public rather than protected. */
class Node {
public:
    virtual ~Node() = default;

    /** RE `movsd xmm0, [rcx + 0x48]`: `TerminalNode`'s slot 2, and what `SplitNode` overrides with +0x50. */
    virtual double value() const { return value48; }
    /** RE slot 3 of both tables: +0x50 in `TerminalNode` and +0x58 in `SplitNode`, so the base supplies only a default. */
    virtual double secondary() const { return 0.0; }

    std::byte reserved08[0x40];                              // +0x08..+0x47: **NO ACCESSOR READS THIS**, so it is padded rather than named
    double value48 = 0.0;                                    // +0x48
};

/** RE 0xA3B570. Four slots: the destructor pair, `value()` at slot 2 reading **+0x48** (inherited), and `secondary()` at slot 3 reading **+0x50**. */
class TerminalNode : public Node {
public:
    double secondary() const override { return value50; }     // RE 0x97500: movsd xmm0, [rcx + 0x50]

    double value50 = 0.0;                                     // +0x50
};

/** RE 0xA3BB70. Four slots: the destructor pair, `value()` at slot 2 reading **+0x50** -- an OVERRIDE, where `TerminalNode` inherits -- and `secondary()` at
 *  slot 3 reading **+0x58**. */
class SplitNode : public Node {
public:
    double value() const override { return value50; }         // RE 0x97510: movsd xmm0, [rcx + 0x50]
    double secondary() const override { return value58; }     // RE 0x97520: movsd xmm0, [rcx + 0x58]

    double value50 = 0.0;                                     // +0x50
    double value58 = 0.0;                                     // +0x58
};

struct BeamStats {
    int iterations = 0;
    int expanded = 0;
    int pruned = 0;
    int placed = 0;
    double seconds = 0.0;
};

// ---------------------------------------------------------------------------
// placement validity
// ---------------------------------------------------------------------------
struct PlacementCheck {
    bool insideSheet = false;
    bool overlapsPlaced = false;
    bool inRestrictedZone = false;
    bool torchOk = true;
    bool insideHoleOnly = true;
    bool ok() const {
        return insideSheet && !overlapsPlaced && !inRestrictedZone && torchOk && insideHoleOnly;
    }
};

// ---------------------------------------------------------------------------
// solve context shared by all strategies
// ---------------------------------------------------------------------------
struct SolveContext {
    const Order* order = nullptr;
    NoFitMap* nfp = nullptr;
    Canceller* canceller = nullptr;
    Observers* observers = nullptr;
    Random* rng = nullptr;
    BeamParams beam;
    double timeLimitSeconds = 10.0;
    int maxIterations = 1000;
    bool logBeam = false;
    std::vector<std::string>* log = nullptr;

    void note(const std::string& s) const;
};

void addLog(const SolveContext& ctx, const std::string& s);

// ---------------------------------------------------------------------------
// the Nester interface -- 6 virtual slots, exactly the recovered vtable layout
// ---------------------------------------------------------------------------
class Nester {
public:
    virtual ~Nester() = default;
    virtual const char* name() const = 0;                 // v2
    // RE: each Run body writes a fixed prefix into the log; those strings were recovered
    // verbatim (trace.hpp). Classes with a proven prefix override this; the default is empty,
    // so a class whose prefix was never observed invents nothing.
    virtual const char* tracePrefix() const { return ""; }
    virtual bool prepare(SolveContext&) { return true; }  // v3
    virtual double estimate(const SolveContext&) const;   // v4
    virtual Solution run(SolveContext&) = 0;              // v5
};

// --- concrete strategies -----------------------------------------------------

/** The two halves of a nester's seed argument. RE 0x342EF `mov rdi, r8`, then 0x3430B reads [rdi] and 0x34301 reads [rdi + 8]. */
struct SeedPair {
    void* first = nullptr;      // RE 0x3430B: mov rax, [rdi]
    void* second = nullptr;     // RE 0x34301: mov rdx, [rdi + 8]
};

/** The Mersenne Twister Multi::NestingNester embeds, at the offsets RE 0x342E0 gives it.
 *
 *  0x6C078965 is 1812433253, the standard MT19937 seeding multiplier, and 0x270 is 624, the state size -- **so a reader of
 *  `imul eax, eax, 0x6c078965` does not have to recognise a magic number to learn that this class carries a random number generator.**
 */
struct Mt19937 {
    static constexpr std::size_t kStateSize = 624;                  // RE 0x3435C: cmp rdx, 0x270
    static constexpr std::uint32_t kSeedMultiplier = 0x6C078965u;   // RE 0x3434B

    std::array<std::uint32_t, kStateSize> state{};                  // RE 0x34354: [rbx + rdx*4 + 0x38]
    std::uint32_t index = kStateSize;                               // RE 0x3436D: 0x270 means untwisted
};

/** RE 0xA3B690, Run = 0x378E0. The members below are placed by its constructor 0x342E0, which is why the class carries them at all: the
 *  constructor sets its object register ONCE (0x342EC `mov rbx, rcx`, popped at 0x343F1, with nothing writing rbx between), so every store
 *  through rbx in that 422 byte body is a store into this object.
 *
 *  THE SEVEN PLACED MEMBERS, each with its instruction, and then the MT19937 the constructor SEEDS with a 624 iteration loop. **The
 *  offsets are asserted below**, so a member added in the wrong place fails the build rather than producing a class that is quietly not the
 *  module's.
 */
class NestingNester : public Nester {          // RE 0xA3B690, Run = 0x378E0
public:

    const char* name() const override { return "NestingNester"; }
    double estimate(const SolveContext&) const override;
    Solution run(SolveContext&) override;

    /** RE 0x342E0's signature: (this, second, SeedPair*), and RE 0x342F5 calls the base constructor 0xB4470 before installing the vtable. */
    NestingNester(const SeedPair& seeds);
    NestingNester() = default;

    void* seedP = nullptr;                  // +0x18, RE 0x34312: mov [rbx + 0x18], rax
    void* seedQ = nullptr;                  // +0x20, RE 0x3430E: mov [rbx + 0x20], rdx
    std::uint32_t seed = 0;                 // +0x28, RE 0x34341: mov [rbx + 0x28], eax -- from a double via 0x34323's cvttsd2si
    double ratio = 0.0;                     // +0x30, RE 0x343E3: movsd [rbx + 0x30], xmm6 -- one measurement over another at 0x343DF
    Mt19937 twister{};                      // +0x38, RE 0x34354 and 0x3436D
};

// THE LAYOUT IS MEASURED, AND IT DOES NOT MATCH THE MODULE -- recorded rather than hidden.
//
// The compiler, through a temporary target, gives this class sizeof(Nester) = 0x8 and:
//
//     seedP  0x08    seedQ  0x10    seed  0x18    ratio  0x20    twister  0x28
//
// while the module's instructions write:
//
//     seedP  0x18    seedQ  0x20    seed  0x28    ratio  0x30    twister  0x38
//
// **EVERY MEMBER IS 0x10 FURTHER ALONG IN THE MODULE**, which means the module's base occupies 0x10 bytes that this C++ `Nester` does not have:
// a vtable pointer is 8, and 0x18 - 0x08 = 0x10, so there are two unaccounted for quadwords between the vptr and the first member. **What they
// are is NOT established** -- the base constructor 0xB4470 has not been read -- and inventing them would place a field on no instruction.
//
// SO THE ASSERT BELOW CHECKS THE DIFFERENCE RATHER THAN PRETENDING IT AWAY: the module's offsets are recorded as constants with their
// instructions, the model's offsets are asserted in lcns/tests/test_recovered.cpp -- **a test is where a measurement belongs and a header is
// where a declaration belongs**, which is also why the offsets are not asserted here: `offsetof` on a polymorphic class is only conditionally
// supported and GCC warns, and a warning is a measurement the gate refuses.
constexpr std::size_t kNestingNesterBaseDataGap = 0x10;    // module offset minus model offset, the same for all five members

static_assert(offsetof(SeedPair, second) == 0x08, "RE 0x34301: mov rdx, [rdi + 8]");
static_assert(Mt19937::kStateSize == 624, "RE 0x3435C: cmp rdx, 0x270");
static_assert(Mt19937::kSeedMultiplier == 1812433253u, "RE 0x3434B: imul eax, eax, 0x6c078965");

// RE 0xA3B490, Run = 0x4B870. The two members are BOOLEANS the constructor COMPUTES from its argument, and neither is a ratio -- the previous
// declaration had a `double ratio_`, which came from a guess. lcns/src/flip_nester.cpp carries the constructor's instructions.
class FlipNester : public Nester {
public:
    FlipNester() = default;
    explicit FlipNester(const SolveContext& ctx);

    const char* name() const override { return "FlipNester"; }
    const char* tracePrefix() const override { return kTraceFlip; }   // RE verbatim
    Solution run(SolveContext&) override;

    /** Whether the flip is recorded, and whether the two scores are compared -- both COMPUTED from the context by the constructor, at
     *  0x4B59B and 0x4B5AE, rather than passed in. */
    bool record_ = false;
    bool compare_ = false;

    /** The comparison the module makes at 0x4B8CF: one measurement over the other. */
    static double score(const Solution& solution);
};

// RE 0xA3B4F0, Run = 0xB3AE0. **THE CLASS DELEGATES TO AN INNER NESTER AT +0x18**, holds the seed it was reset with at +0x10, and carries a
// MERSENNE TWISTER at +0x20 whose seed is the constant 1 at construction. Its vtable's slot 2 is the RESEED at 0xB43B0, not an estimate. See
// lcns/src/filter_nester.cpp for the instructions.
class FilterNester : public Nester {
public:
    FilterNester();

    const char* name() const override { return "FilterNester"; }
    const char* tracePrefix() const override { return kTraceFilter; }   // RE verbatim
    Solution run(SolveContext&) override;

    /** RE 0xB43B0, vtable slot 2: re-seed the generator with `index + 1` and forward the same index to the inner nester. The module calls
     *  the inner object's slot 2 THROUGH ITS VTABLE, so the inner object implements this same interface. */
    virtual void reset(int index);

    /** RE 0x609E20: a Bernoulli trial that advances the generator it is given. */
    bool draw(double probability);

private:
    /** RE 0xB4449: the object at +0x18 that actually nests, reached through its own vtable. */
    FilterNester* inner_ = nullptr;
    int seed_ = 0;         // RE 0xB4455: mov dword [rbx + 0x10], esi
    Mt19937 rng_;          // RE 0xB3AB0: the state at +0x20, and RE 0xB3AC1 the index at +0x9E0

    void seedMt(std::uint32_t seed);   // the recurrence the constructor and the reseed both perform
};

/** RE 0x97A090, 1599 bytes, SEVENTEEN callers: it takes the generator and a double and produces a double. A free function, because other
 *  nesters reach it too and a member would claim it as one class's own. */
double filterScore(const SolveContext& ctx, Mt19937& rng);

class NoFillNester : public Nester {           // RE 0xA3B530, Run = 0x7F240
public:

    const char* name() const override { return "NoFillNester"; }
    const char* tracePrefix() const override { return kTraceNoFill; }   // RE verbatim
    Solution run(SolveContext&) override;
};

class TilingNester : public Nester {           // RE 0xA3B5A0, Run = 0x46940 (largest)
public:

    const char* name() const override { return "TilingNester"; }
    Solution run(SolveContext&) override;
};

class CompactNester : public Nester {          // RE 0xA3B610, Run = 0xB13D0
public:

    const char* name() const override { return "CompactNester"; }
    Solution run(SolveContext&) override;
};

/** RE 0x2C9A0 and 0x2C9F0: the engine allocates 0x48 bytes twice and calls 0x4AAD0, whose body is the constructor below. **`Run = 0x4AB40` WAS WRONG and is
 *  removed**: 0x4AB40 is 1650 bytes, has one caller, and its second instruction group writes `[rsi]` -- **a vptr is never assigned outside a constructor**, so
 *  0x4AB40 is not this class's `run`. Its `run` is `LCNS_SUBSTITUTED` and has no address here.
 *
 *  **AND THE TWO INT MEMBERS HAD NO EVIDENCE AT ALL**: nothing in the constructor stores at +0x08 or +0x0C, and the substitute does not read them. **They are
 *  deleted rather than kept looking recovered**, and the fields the constructor DOES write are declared in their place. */
class LimitedNester : public Nester {
public:

    /** RE 0x4AAD0, 101 bytes, one caller. `rcx` is the new object, `r8` is a `{count, pointer}` pair and `r9` is a copy of it. **The object register is `rbx`,
     *  established by 0x4AAD6 `mov rbx, rcx`, and every store below is through it**:
     *
     *      04AAE9  lea rax, [rip + 0x9f0b70]      ; the vtable
     *      04AAF0  mov qword [rbx], rax           ; **written here and nowhere else, which is what a constructor is**
     *      04AAFA  mov qword [rbx + 0x20], rax    ; from r9
     *      04AAF6  mov qword [rbx + 0x28], rdx    ; from [r9 + 8]
     *      04AAFE  call 0x5f3900 with rcx = rbx + 0x30   ; constructs the member at +0x30
     *      04AB03  mov qword [rbx + 0x38], 0
     *      04AB0B  mov dword [rbx + 0x40], 0x3b9ac999f   ; a large bound
     *      04AB12  mov byte  [rbx + 0x44], 1
     *      04AB16  mov byte  [rbx + 0x45], 0
     *
     *  **AND THE `(int maxParts, int maxAngles)` ARGUMENTS THE PREVIOUS DECLARATION NAMED ARE NOT IN THIS BODY**: r8 and r9 carry a pair, not two ints. */
    LimitedNester();
    const char* name() const override { return "LimitedNester"; }
    Solution run(SolveContext&) override;
private:
    // **THE NAMES ARE THE OFFSETS BECAUSE THE MODULE GIVES NO ORACLE FOR THEM YET.** The two members that were here (`maxParts_`, `maxAngles_`) had NO evidence --
    // nothing stores at +0x08 or +0x0C and the substitute does not read them -- so they are gone. What is certain is WHERE the constructor writes:
    std::uint64_t at20 = 0;   // +0x20, 0x4AAFA: `mov qword [rbx + 0x20], rax`, rax from r9
    std::uint64_t at28 = 0;   // +0x28, 0x4AAF6: `mov qword [rbx + 0x28], rdx`, rdx from [r9 + 8]
    std::uint64_t at30 = 0;   // +0x30, 0x4AAFE: constructed by 0x5F3900, which stores the result of 0x5F47C0 at its own +0x00
    std::uint64_t at38 = 0;   // +0x38, 0x4AB03: zeroed
    std::uint32_t at40 = 0;   // +0x40, 0x4AB0B: initialised to 0x3B9AC99F, a large bound
    bool at44 = true;         // +0x44, 0x4AB12
    bool at45 = false;        // +0x45, 0x4AB16
};

class DatabaseNester : public Nester {         // RE 0xA3B740, Run = 0x5B250
public:

    const char* name() const override { return "DatabaseNester"; }
    Solution run(SolveContext&) override;
    // RE: ..\nesting\algos\tree_db.cpp (FindNode 0x1C12D0)
    static std::uint64_t hashNesting(const Nesting& n);
    void remember(std::uint64_t hash, const Solution& s);
private:
    std::vector<std::pair<std::uint64_t, Solution>> db_;
};

// RE 0x1ADC20 (3261 B / 655 instructions, 3 callers, 46 callees). Its own strings are 'choosen' and
// 'database' (referenced at 0x1ADDB4 and 0x1AE718) and it calls three times into
// ..\nesting\algos\multinesting_optimizer.cpp. Two tolerance-shaped uses were read at instruction
// level:
//     1AE387  movsd xmm6,[0.999] ; 1AE392 mulsd xmm6,xmm0     -> 0.999 * f(...)
//     1AE682  imul rcx,rdx ; 1AE693 cvtsi2sd xmm0,rcx ; 1AE698 mulsd xmm0,[0.25]
//                                                             -> 0.25 * (a * b), sign checked first
// RECOVERED: the texts, the tolerance constants and the call into the multinesting optimizer.
// NOT RECOVERED: what the two formulas compute and what their operands are, so no function is written
// for them -- the constants are kept with their provenance instead.
inline constexpr double kMultinestingTolerance = 0.999;   // RE 0x1AE387
inline constexpr double kMultinestingQuarter = 0.25;      // RE 0x1AE698, a product scaled by 1/4

// RE 0x69BE80 (3226 B / 668 instructions). Its own assertion text is, verbatim:
//     'm_base && "call SetActiveNesting first"'
// and one of its callees carries the text 'GetActiveParts'. So the class that owns m_base has two
// methods, SetActiveNesting() and GetActiveParts(), and the assert states the precondition of the
// second: the active nesting must have been set before the parts can be asked for. The condition the
// assert actually tests is `m_base`, which is what the helper below evaluates.
inline constexpr const char* kMethodSetActiveNesting = "SetActiveNesting";   // RE 0x69BE80
inline constexpr const char* kMethodGetActiveParts = "GetActiveParts";       // RE 0x69BE80
inline constexpr const char* kAssertSetActiveNestingFirst =
    "m_base && \"call SetActiveNesting first\"";                            // RE 0x69BE80, verbatim

// RE the assert's own condition: the pointer must be non-null before the parts are available.
inline bool activeNestingReady(const void* mBase) { return mBase != nullptr; }

// RE 0x1CC0 and 0x5D90 (427 bytes each, two callers each). Neither carries any other text; each carries
// a comment the binary stores verbatim, and that comment states what the function waits for:
//     0x1CC0  '// LocalCancel waiting for threads termination'
//     0x5D90  '// LocalTerminate waiting for threads termination'
// So the pair is the local shutdown path: one for cancellation, one for termination, both waiting until
// the worker threads have stopped. The comments are kept verbatim because they are the evidence; the
// waiting mechanism itself was not read far enough to be reimplemented.
inline constexpr const char* kCommentLocalCancel = "// LocalCancel waiting for threads termination";
inline constexpr const char* kCommentLocalTerminate = "// LocalTerminate waiting for threads termination";

// RE 0x1CC0 (LocalCancel) and 0x5D90 (LocalTerminate). Both start by comparing the SAME field with two
// values and returning immediately unless one matches:
//     1CCA  mov eax,[rcx+0x4C] ; cmp eax,9   ; je <work>
//     1CD5  mov eax,[rcx+0x4C] ; cmp eax,0xA ; je <work>
// so the field at +0x4C is a state and these two values are the states in which the local shutdown runs.
// RECOVERED: the field offset, the two compared values and the early-return shape.
// INFERRED:  that the state names are about cancelling and terminating -- the comments on the two
//            functions say so, the numbers themselves carry no name.
inline constexpr int kThreadStateCancel = 9;       // RE 0x1CCA: cmp eax,9
inline constexpr int kThreadStateTerminate = 10;   // RE 0x1CD8: cmp eax,0xA

// RE the early-return shape of both functions: only those two states do the work.
inline bool isShutdownState(int state) {
    return state == kThreadStateCancel || state == kThreadStateTerminate;
}





class RectangleNester : public Nester {        // RE 0xA3B800, Run = 0x75FB0
public:

    const char* name() const override { return "RectangleNester"; }
    Solution run(SolveContext&) override;
};

// ---------------------------------------------------------------------------
// RE: the 0xD0 = 208 byte core that Multi::RowNester's CONSTRUCTOR allocates.
//
// Multi::RowNester has the vtable address point 0xA3BB40 (typeinfo RVA 0xA18390, name
// 'N5Multi9RowNesterE'), and its constructor is 0x8F210:
//     8F221  call 0xB4470                     ; base (Multi::Nester) constructor
//     8F226  lea rax,[rip+0x9AC913] -> 0xA3BB40
//     8F230  [rbx] = rax                      ; install the vtable
//     8F238  ecx = 0xD0 ; call operator new   ; 208 byte core
//     8F252  call 0x6AABC0(core, rdx, pipe)   ; fill it (see below)
//     8F257  [rbx+0x18] = rsi                 ; Multi::RowNester::+0x18 = the core
//
// 0x6AABC0 (5763 B) lives in ..\multi\row_nester.cpp -- its inline-constructed strings resolve to
// that path -- and is called exactly once, from the constructor above; Multi::RowNester::Run
// (vtable slot 5 = 0x913E0, 12380 B) does NOT call it. So the core, and with it the
// Row::Squeezer, is built at CONSTRUCTION time from the model geometry (0x6AABC0 calls
// 0x4FC940 GetSheet and 0x4FC5B0 GetPart), not during Run.
//
// Core layout recovered from 0x6AABC0:
//     [+0x08 .. +0x50]  config block, handed to 0x13C380 as its third argument
//     [+0x18]           double  == cfg[+0x10] of that call == the Squeezer cost threshold
//     [+0x20]           double  == cfg[+0x18] of that call == the coefficient
//     [+0x40]           mode, compared against 0 / 1 / 3 (0x6AB6B5, 0x6AB6C0, 0x6AB6C9)
//     [+0xC0]           Row::Squeezer*, installed at 0x6AC118 `[rbp+0xC0] = rsi`, the previous
//                       one destroyed at 0x6AC124 via 0x13C520 + operator delete
// The core's configuration defaults are rodata constants, read straight from the prologue of
// 0x6AABC0 (the core's initialisation function):
//     6AABDF  xmm2 = [0x9B1A40] = 10.0   -> core[+0x08]
//     6AABE7  xmm3 = [0x9B1A48] =  4.0   -> core[+0x18]   (== cfg[+0x10], the cost threshold)
//     6AABEF  xmm4 = [0x9B1A50] = 20.0   -> core[+0x20]   (== cfg[+0x18], the coefficient)
//     6AABDB  xmm6 = 0                   -> core[+0x10] and core[+0x30]
//     6AAC05  core[+0x00] = pipe ;  6AAC8E  core[+0x40] = 0
// and they can be OVERRIDDEN from the problem object:
//     6AAC2A  call 0x4FC2F0(arg)   ; `mov rax,[rcx] ; movzx eax,byte [rax+0x170]`
//     6AAC42  call 0x4FC300(arg)   ; `mov rax,[rcx] ; movzx eax,byte [rax+0x1A0]`
//     6AAC53  call 0x4FC3C0(arg)   ; `mov rax,[rcx] ; add rax,0x1A0`
//     6AAC5D  core[+0x20] = [rax+0x08]   ; == problem+0x1A8
//     6AAC6B  core[+0x18] = [rax+0x10]   ; == problem+0x1B0  <-- the threshold in the override path
//     6AAC62  core[+0x28] = (byte)[rax+0x18]
//     6AAC75  core[+0x30] = [rax+0x20]
inline constexpr double kRowCoreAt0x08 = 10.0;   // RE 0x9B1A40
inline constexpr double kRowCoreAt0x18 = 4.0;    // RE 0x9B1A48
inline constexpr double kRowCoreAt0x20 = 20.0;   // RE 0x9B1A50

class RowNestCore {
public:
    // RE: 0x6AABC0(core, problem, pipe). The two configuration scalars default to the recovered
    // rodata constants; the binary may instead take them from the problem's +0x1A8 / +0x1B0
    // (see above), which this Order does not model, so they stay parameters.
    RowNestCore(const Order& order, bool pipe, double configAt0x18 = kRowCoreAt0x18,
                double configAt0x20 = kRowCoreAt0x20);

    double threshold() const { return threshold_; }   // RE core+0x18
    double coeff() const { return coeff_; }           // RE core+0x20
    int mode() const { return mode_; }                // RE core+0x40
    bool pipe() const { return pipe_; }
    std::size_t rowCount() const { return rowCount_; }
    const row::Squeezer& squeezer() const { return squeezer_; }   // RE core+0xC0
    bool hasSqueezer() const { return hasSqueezer_; }

private:
    double threshold_ = 0.0;   // RE +0x18
    double coeff_ = 0.0;       // RE +0x20
    int mode_ = 0;             // RE +0x40
    bool pipe_ = false;
    std::size_t rowCount_ = 0;
    row::Squeezer squeezer_;   // RE +0xC0
    bool hasSqueezer_ = false;
};

class RowNester : public Nester {              // RE 0xA3BB40, ctor 0x8F210, Run slot5 = 0x913E0
public:

    explicit RowNester(bool pipe = false) : pipe_(pipe) {}
    const char* name() const override { return pipe_ ? "RowNester(pipe)" : "RowNester"; }
    Solution run(SolveContext&) override;

    // RE: Multi::RowNester::+0x18.
    // NOTE (deviation, deliberate): the binary builds this core inside the constructor because
    // its constructor already receives the problem; this engine's makeStrategy() has no Order
    // yet, so the core is built on the first run(). The recovered structure -- RowNester holding
    // a 208 byte core at +0x18, the core holding the squeezer at +0xC0 -- is preserved.
    const RowNestCore* core() const { return core_.get(); }

    // The two core configuration scalars (core+0x18, core+0x20). They default to the recovered
    // rodata constants kRowCoreAt0x18 / kRowCoreAt0x20 (see above); the binary can override them
    // from the problem's +0x1B0 / +0x1A8, which this Order does not model.
    void setRowConfig(double at0x18, double at0x20) { cfg18_ = at0x18; cfg20_ = at0x20; }
    double cfg18() const { return cfg18_; }
    double cfg20() const { return cfg20_; }

private:
    bool pipe_;
    double cfg18_ = kRowCoreAt0x18;   // RE 0x9B1A48, overridable from problem+0x1B0
    double cfg20_ = kRowCoreAt0x20;   // RE 0x9B1A50, overridable from problem+0x1A8
    std::unique_ptr<RowNestCore> core_;   // RE: this+0x18
};

class MultiTorchNester : public Nester {       // RE 0xA3B8A0, Run = 0x7BCC0
public:

    const char* name() const override { return "MultiTorchNester"; }
    Solution run(SolveContext&) override;
};

class CompositeNester : public Nester {        // RE 0xA3B780 (shell)
public:
    void add(std::shared_ptr<Nester> n) { children_.push_back(std::move(n)); }
    const char* name() const override { return "CompositeNester"; }
    Solution run(SolveContext&) override;
private:
    std::vector<std::shared_ptr<Nester>> children_;
};

namespace pack {
// RE Pack::BestNester 0xA3B400 / KnapsackNester 0xA3B430 / RecursiveNester 0xA3B460
class BestNester : public Nester {
public:

    void add(std::shared_ptr<Nester> n) { children_.push_back(std::move(n)); }
    const char* name() const override { return "Pack::BestNester"; }
    Solution run(SolveContext&) override;
private:
    std::vector<std::shared_ptr<Nester>> children_;
};
class KnapsackNester : public Nester {
public:

    const char* name() const override { return "Pack::KnapsackNester"; }
    Solution run(SolveContext&) override;
};
class RecursiveNester : public Nester {
public:

    const char* name() const override { return "Pack::RecursiveNester"; }
    Solution run(SolveContext&) override;
};
}  // namespace pack

// ---------------------------------------------------------------------------
// primitives shared by the strategies
// ---------------------------------------------------------------------------
// Fill part.shape from part.rawShape by inflating with `gap` and removing self intersections.
// This is the equivalent of the recovered AddInflatedToolPathToPart (0x12C60): the outer ring
// gets +gap and every inner ring gets -gap. The engine calls it once per run using
// interpartGap/2 per part, so that two neighbouring parts end up `interpartGap` apart.
void prepareInflatedShapes(Order& order, double gap);

// Validate one candidate placement.
PlacementCheck checkPlacement(const Order& order, const Nesting& nesting, int sheetIndex,
                             const Part& part, const NestedPart& np);

// Score a partial nesting (higher is better). Used as the beam node value.
double scoring(const Order& order, const Nesting& nesting, const Part& newlyPlaced);

// Try to place `partIndex` on `sheetIndex` starting from every vertex of the no-fit
// geometry plus a coarse grid; returns the accepted placement if any.
bool placePart(const Order& order, SolveContext& ctx, Nesting& nesting, int sheetIndex,
               int partIndex, const BeamParams& beam, NestedPart* out, bool allowHoles);

// One full pass of the main packer over all pending instances. `forbidFill` implements
// the NoFillNester difference. `seed` pre-fills the nesting (used by the tiling strategies,
// which lay a repeated pattern first and let the packer fill the remainder).
Nesting packAll(const Order& order, SolveContext& ctx, int sheetIndex, const BeamParams& beam,
                bool forbidFill, bool* cancelled, const Nesting* seed = nullptr);

// RE Multi::MultiTorchNester / Tiling::MultitorchEvaluator
std::vector<MultitorchInfo> evaluateMultitorch(const Order& order, const Nesting& nesting);

// ---------------------------------------------------------------------------
// compaction -- RE Compact::Compacter::Implementation (vtable 0xA3D470) + 0x252B60
//   grid step = min(width, height) / 10.0   (double 10.0 @ 0x9C2BB0)
//   RotateCompact (0x678230) early-outs when the improvement threshold is <= 1e-6
//   (~ 0x9BF5D0)
// ---------------------------------------------------------------------------
struct CompactionStats {
    bool improved = false;
    double gain = 0.0;
    int moves = 0;
    int rotations = 0;
};
CompactionStats compactNesting(const Order& order, Nesting& nesting, SolveContext& ctx,
                               double acceptThreshold = 1e-6);

// ---------------------------------------------------------------------------
// finalisation -- RE finalisation passes, in the order their strings appear:
//   "Finalize : Parts renested in holes"      (RenestInHoles 0x40720)
//   "Finalize : Nesting packed bottom left"   (BL/BLF stabilisation)
// ---------------------------------------------------------------------------
int renestInHoles(const Order& order, Nesting& nesting, SolveContext& ctx);
void packedBottomLeft(const Order& order, Nesting& nesting);

// ---------------------------------------------------------------------------
// common cut -- RE LoadSegment's field list and the stats keys
// ---------------------------------------------------------------------------
CommonCutEvaluation detectCommonCuts(const Order& order, const Solution& solution);

}  // namespace lcns
