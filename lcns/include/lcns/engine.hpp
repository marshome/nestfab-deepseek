// lcns/engine.hpp -- orchestration: cancellers, strategy scheduling, engine entry, SVG.
//
// Recovered architecture (re/REPORT.md 6.x / 7.2, findings_engine.md):
//   Engine::Engine vtable = [dtor, deleting dtor, Run] and the signature, inferred from the
//   call site at 0x2516E, is Run(const Problem&, double time_limit, Observer&, Result&).
//   Run slot RVAs: MultiEngine 0x755050, DelayedEngine 0x756EC0, NestingEngine 0x757250,
//   InfiniteEngine 0x759A80, CompositeEngine 0x759B70, EquivalentEngine 0x75BCC0,
//   CloudEngine 0x26A60.
//   The thread shell is RunThreadLocalComputation (0x25100); the worker loop that logs
//   "Engine finished." is 0x44E0.
//   Multi::Supervisor::Run (0x827F0) takes (Supervisor*, uint strategy_id, uint rank) and is
//   started once per strategy by std::thread.
//   Multi::AdvancedStrategist::operator() (0x2DF60) picks one of four routes and 0x2CCF0
//   cascades the budget: n -> 2 -> (n+1)/2 -> n-1.
//   Multi::StrategyAdder::Add (0x2C4D0) maps a mode tag to a concrete Nester:
//       2 -> RectangleNester, 3 -> RowNester, 4 -> RowNester(pipe),
//       mode 1 -> NestingNester, plus Compact/Filter/NoFill/Limited.
//   Cancellation: SupervisorCanceller::ProbeCancel (0x30030) is the single global gate,
//   elapsed / Problem[+0x408] > 1.0.
//   Reporting: DrawSVG / DrawSVGAux / DrawSVGMarks exist and the report uses the CSS asset
//   "cns_solution.css"; the marks layer is named "__marks__".
#pragma once

#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

#include "lcns/nester.hpp"

#include "lcns/trace.hpp"   // the recovered kTrace* prefixes (own header, no cycle)

namespace lcns {

// RE 0x2C4D0 Multi::StrategyAdder::Add -- the object sizes it allocates (operator new 0x998500,
// size passed in ecx) and the mode -> class table. The sizes are a second, independent fingerprint
// of the recovered mapping: 2624 B for the base packer, 2552/2536 for compact/filter, 96 for no-fill.
inline constexpr int kTilingNesterBytes = 0x20;         // RE 0x2C525 ecx = 0x20
inline constexpr int kNestingNesterBytes = 0xA40;       // RE 0x2CB1C ecx = 0xA40
inline constexpr int kRectangleNesterBytes = 0x20;      // RE 0x2CB50
inline constexpr int kRowNesterBytes = 0x20;            // RE 0x2CB70 / 0x2CB91
inline constexpr int kFlipNesterBytes = 0x28;           // RE 0x2C953
inline constexpr int kMultiTorchNesterBytes = 0x28;     // RE 0x2C591
inline constexpr int kLimitedNesterBytes = 0x48;        // RE 0x2C9F0 / 0x2C9A0
inline constexpr int kNoFillNesterBytes = 0x60;         // RE 0x2C604
inline constexpr int kCompactNesterBytes = 0x9F8;       // RE 0x2CA30
inline constexpr int kFilterNesterBytes = 0x9E8;        // RE 0x2CA77
inline constexpr int kStrategyModeCount = 5;            // modes 0..4; >= 5 asserts in the binary

// The sheet selector family Add chooses from (not present in the earlier notes):
//   Multi::LargestSheetSelector 0xB0000, Multi::RandomSheetSelector 0xB0040,
//   Multi::NoMixSheetSelector   0xAFD60, driven by options[+0x2C0] / options[+0x2C4] and 0x4FC250.

// RE 0x2CE00 (1055 B) -- the route the dispatcher 0x2DF60 takes when Pb[+0xC8] != 0, i.e. MODE 2.
// It reads the byte AFTER that selector (Pb[+0xC9]) and a bool returned by 0x5223A0, then flags an
// incompatibility it builds inline as an assertion message:
//     '!is_tool' 'ing && "' 'Normal s' 'hear is ' 'incompat' 'ible wit' 'g contac'
//   =  !is_tooling && "Normal shear is incompatible with ... contact ..."
// so the engine has TWO feature concepts the earlier notes did not have:
//   * tooling -- an is_tooling predicate, switched by Pb[+0xC9];
//   * shear   -- with a function literally named AddShear (string at 0x2CF69, TU ..\multi\...),
//                and "Normal shear" is mutually exclusive with tooling (the assertion above).
inline constexpr std::size_t kPbMode2SelectorByte = 0xC8;   // RE 0x4FC260 / 0x4FC2C0
inline constexpr std::size_t kPbToolingByte = 0xC9;         // RE 0x2CE3C cmp byte [rax+1],0
inline constexpr int kModeShearTooling = 2;                 // RE 0x2CE00 is that mode's body

// RE ..\nesting\algos\bucket_manager.hpp -- the beam-tree/bucket kernel (re/findings_bucket_manager.md).
// The node evaluator is bounded by a slack on the surface: the assertion repeated at the three
// ComputeNodeIndex instantiations (0x81C370 / 0x81C690 / 0x81C9B0) reads
//     eval.m_c >= 0 && eval.m_c <= max_surface * 1.05
// so 1.05 is a recovered constant, not a tuning choice. The same TU also asserts over
// pricer.m_prices[p], surface_step, m_best and slices_width, i.e. the node carries a cost m_c, a
// surface step, and the pricer exposes a per-part price array.
inline constexpr double kEvalSurfaceSlack = 1.05;           // RE 0x81C690 assertion text

// RE the assertion repeated at the three ComputeNodeIndex instantiations (0x81C370 / 0x81C690 /
// 0x81C9B0), quoted verbatim in re/findings_bucket_manager.md:
//     'eval.m_c >= 0 && eval.m_c <= max_surface * 1.05'
// Both halves belong to the check, so the predicate carries both: a negative evaluation is as
// invalid as one above the slacked surface. The 1.05 is not a tuning choice, it is in the text.
bool withinSurfaceSlack(double evalC, double maxSurface);

// RE the 0x6CA720 family: twelve handlers, 279 bytes / 78 instructions each, laid out exactly 0x120
// bytes apart from 0x6CA720 to 0x6CB380, all calling the same nine routines -- one entry per classd
// parameter. Each carries its class name as a LENGTH PREFIXED ascii string; all twelve were read
// in round 66 and the leading decimal equals the length of the name that follows in every case, so
// the encoding is <decimal length><name>. The names are real identities taken from the binary, and
// NOTE two of them contain a digit ('Off2Weight', 'ODescriptions2'), so the body is alphanumeric.
extern const char* const kTypeInfoNames[12];

// CORRECTION (goal round 79). These strings are not a serialisation format invented by the library:
// they are Itanium C++ ABI type_info names. 'type_info::name()' for a class Foo is "<len(Foo)>Foo",
// so "10BeamValues" is BeamValues, "13dupcol_action" is dupcol_action. 198 such strings exist in the
// image; the twelve below are the ones the 0x6CA720 family handles. The earlier reading in this file
// (length-prefixed parameter names for a config system) was WRONG and is corrected here rather than
// left standing.
std::string encodeTypeInfoName(const std::string& name);                  // "UseMap" -> "6UseMap"
bool decodeTypeInfoName(const std::string& encoded, std::string* name);   // validates the prefix
int typeInfoNameIndex(const std::string& encoded);                        // -1 when unknown

// RE 0x9B15E0 -- the double 0.99, referenced twice inside 0x73280 (at 0x754ED and 0x75EF3) in
// the same shape: two pairs of doubles are differenced and multiplied (an AREA), one branch
// doubles it, the result is scaled by this constant and compared with `ucomisd` against the
// other area, with `jbe` skipping when 0.99*X <= area. So the constant is an area-coverage
// slack of about one percent. The ARITHMETIC is evidence; the NAME is an inference -- no symbol
// or string states this meaning. Compare the 1.05 upper bound asserted in bucket_manager.hpp:
// both are area tolerances built the same way.
inline constexpr double kAreaCoverageSlack = 0.99;   // RE 0x9B15E0 via 0x754ED / 0x75EF3

// RE 0x754ED..0x754F9 and 0x75EF3..0x75EFF -- the two reference sites have the SAME shape:
//     xmm1 = (a - c) * (b - d)            ; a candidate AREA
//     xmm0 = (e - f) * (g - h) [*2]       ; the reference AREA, doubled on one branch
//     xmm0 = xmm0 * kAreaCoverageSlack    ; scale the reference by 0.99
//     ucomisd xmm0, xmm1 ; jbe <skip>     ; branch away when 0.99*reference <= candidate
// so the code takes its action when the candidate area reaches 0.99 of the reference, i.e. the
// candidate must COVER the reference to within one percent. That is the predicate below; the branch
// polarity is the one the instruction sequence has, not a guess.
bool coversReference(double candidateArea, double referenceArea);



// RE 0x7BCC0 (MultiTorchNester::Run) -- the tolerance family this binary uses. Its own
// assertion text spells one of them out: 'res <= y * 1.001'. The rest are read from the
// constants it loads: 1.001 and 0.999 (a +-0.1% pair, used repeatedly), 0.99 (the 1% area
// slack already named kAreaCoverageSlack), 0.5 and 0.25 (step halving), 0.05, and 3. The
// VALUES are recovered; the SEMANTICS of each one is inferred from its use, so they are named
// after their role in the comparison rather than after any symbol.
inline constexpr double kToleranceUpper = 1.001;   // RE 0x9B1740, see 'res <= y * 1.001'
inline constexpr double kToleranceLower = 0.999;   // RE 0x9B1758

struct EngineParams {
    int threads = 1;                    // RE: Problem::nb_max_threads
    std::uint32_t seed = 0;             // RE: Problem::seed (read at 0x24A80)
    double timeLimitSeconds = 10.0;     // written into Problem[+0x408]
    int maxIterations = 1000;
    BeamParams beam;
    bool cascadeBudgets = true;         // RE 0x2CCF0
    bool compactAtEnd = true;
    bool finalizeBottomLeft = true;     // RE "Finalize : Nesting packed bottom left"
    bool renestInHoles = true;          // RE "Finalize : Parts renested in holes"
};

struct EngineResult {
    Solution solution;
    double score = 0.0;
    bool cancelled = false;
    int strategiesRun = 0;
    double seconds = 0.0;
    std::vector<std::string> log;
    CommonCutEvaluation commonCuts;
};

// RE 0x2DF60 (AdvancedStrategist::operator(), 481 B / 108 insns) -- the mode DISPATCHER, read
// instruction by instruction. The route is chosen from the already recovered configuration gates:
//
//   2DF66  rax = this->[0x18] ; 2DF6A cmp byte [rax+0x81],0 ; jne -> cascade(mode = 2)
//   2DF79  rcx = this->[0x10]                     ; Pb, the Set* parameter block
//   2DF7D  call 0x4FC260  = Pb[0xC8]      ; jne -> 0x2CE00(this,arg)   mode 2 专用体 (1055 B)
//   2DF8A  call 0x4FC2F0  = Pb[0x170]     ; jne -> cascade(mode = 3)   <- SetPipeMode 的 pipe 闸
//   2DF9B  call 0x4FC300  = Pb[0x1A0]     ; jne -> cascade(mode = 4)   <- SetCommonCutParameters 闸
//   2DFAE  call 0x2D330                   ; 默认体 (3118 B)
//
// and the 40 byte block handed to the cascade 0x2CCF0 is, exactly (r8 = rsp+0x20 in the dump):
//   +0x00 int    mode (2 / 3 / 4)              +0x0A u8  1        (the only non-zero bool)
//   +0x04 u8[6]  zero except +0x0A             +0x10 qword 0
//   +0x0C int    0                             +0x18 int 0  +0x1C int 0
//                                              +0x20 double 1.0 (rodata 0x9AEC90)
inline constexpr std::size_t kPbModeByte = 0xC8;         // RE 0x4FC260 (mode route 2)
inline constexpr std::size_t kPbPipeByte = 0x170;        // RE 0x4FC2F0 == SetPipeMode gate
inline constexpr std::size_t kPbCommonCutByte = 0x1A0;   // RE 0x4FC300 == SetCommonCutParameters
inline constexpr std::size_t kPbInnerFlag = 0x81;        // RE 0x2DF6A (this->[0x18]->[0x81])
inline constexpr int kModeAdvanced3 = 3;                 // RE 0x2E0E2 mov dword [rsp+0x20], 3
inline constexpr int kModeAdvanced4 = 4;                 // RE 0x2E068 mov dword [rsp+0x20], 4
inline constexpr std::size_t kModeBlockSize = 0x28;      // RE: the 40 B descriptor POD
inline constexpr std::size_t kModeBlockBoolAt = 0x0A;    // RE 0x2DFFD/0x2E07A/0x2E0F4 = 1
inline constexpr std::size_t kModeBlockDoubleAt = 0x20;  // RE 0x2E037 = 1.0 @0x9AEC90
inline constexpr double kModeBlockDoubleValue = 1.0;     // RE rodata 0x9AEC90

// RE 0x2D330 (default schedule, 3118 B / 528 insns) and 0x2DF60: the 40 byte descriptor, decoded
// from its USE. 0x2CCF0 and 0x2D220 are byte-identical twins (same instructions, 0x130 apart):
// both call Multi::StrategyAdder::Add (0x2C4D0, 2072 B) and then cascade on the field at +0x0C:
//     Add(mode, n = 2);
//     if (n > 4) Add(mode, n = (n+1)/2);
//     Add(mode, n = n - 1);            // reached directly when n == 4
//     (esi is callee saved, so 2CD5B's "cmp esi,4" really tests the descriptor's n)
inline constexpr std::size_t kDescMode = 0x00;    // int mode (1 on every 0x2D330 step; 2/3/4 at 0x2DF60)
inline constexpr std::size_t kDescFlags = 0x04;   // bool[6] PER-STEP enable flags, not padding
inline constexpr std::size_t kDescN = 0x0C;       // int n, the schedule width the cascade reads
inline constexpr std::size_t kDescAt10 = 0x10;    // double, 0.0 in every default-schedule step
inline constexpr std::size_t kDescAt18 = 0x18;    // int, copied from the options object
inline constexpr std::size_t kDescAt1C = 0x1C;    // int, a computed count in two of the steps
inline constexpr std::size_t kDescAt20 = 0x20;    // double 1.0 (rodata 0x9AEC90)
inline constexpr int kCascadeFirstN = 2;          // RE 0x2CD37 / 0x2D267
inline constexpr int kCascadeEarlyOut = 2;        // RE 0x2CD0B cmp esi,2 ; jle -> return
inline constexpr int kCascadeMidThreshold = 4;    // RE 0x2CD5B cmp esi,4

// RE: the 40 byte strategy descriptor POD {int mode; bool[6]; int n; qword; int,int; double}
struct StrategyDescriber {
    int mode = 1;
    int n = 1;
    double ratio = 1.0;
    std::string name;

    // RE 0x2CCF0: n -> 2 -> (n+1)/2 -> n-1
    std::vector<int> cascade() const;
};

// RE Multi::StrategyAdder::Add 0x2C4D0
std::shared_ptr<Nester> makeStrategy(int mode);
std::vector<std::shared_ptr<Nester>> makeDefaultStrategies();

// RE Multi::Supervisor (vtable 0xA3B4D0), Run at 0x827F0
class Supervisor {
public:
    Supervisor(const Order& order, SolveContext& ctx, EngineParams params);

    void addStrategy(std::shared_ptr<Nester> n, const StrategyDescriber& d);
    std::size_t strategyCount() const { return strategies_.size(); }

    // Runs every registered strategy (spread over `threads` workers) and returns the best.
    Solution run(BestObserver* sink = nullptr);

private:
    const Order& order_;
    SolveContext& ctx_;
    EngineParams params_;
    std::vector<std::pair<std::shared_ptr<Nester>, StrategyDescriber>> strategies_;
    std::mutex mu_;
};

class Engine {
public:
    // RE Engine::MultiEngine::Run 0x755050 (the same shape as every other engine)
    EngineResult run(const Order& order, const EngineParams& params = {}, Observers* obs = nullptr);
};

// ---------------------------------------------------------------------------
// reporting -- SVG output, format recovered from ..\structure\svg_io.cpp
// (entry points: export 326 NoFitGenerateSvgNesting 0x9550, export 328
//  NoFitGenerateSvgGeometry 0x9790; the writer itself is 0x7CCDF0, 16831 B)
//
// The style fragments below are the ones the binary emits, verbatim:
//   0x5DAEB0  'fill:none;stroke:black;stroke-width:0.1%'
//   0x5DDDD0  ');stroke:rgb(0, 0, 0);stroke-width:0.1%' ;  ';fill:rgb('
//   0x5DC9D0  ');stroke:rgb(0, 0, 0);stroke-width:0.2%'
//   0x5DE320  ');stroke:rgb(192, 0, 0);stroke-width:0.1%'          <- marks are dark red
//   0x5DCE70  'fill: url(#diagonalHatch' + '); stroke-width:0.1%; fill-opacity:0.7; stroke-opacity:0.7'
//   0x5D9BF0  ';stroke-opacity:0.4;fill:rgb(128,128,128);stroke:rgb(0,0,0);'
//   0x516380  'fill:white' ; 'fill-opacity:0.8;fill:black;stroke:black;stroke-width:0.1%'
//   marks     '<circle cx="' ... '" r="0.5%">'   -- a PERCENT radius, so Order::markSize is not
//             what the binary uses for the radius; that field drives other reporting.
// The hatch pitch and the sheet margins are runtime numbers in the binary, so these two are ours.
inline constexpr double kSheetMargin = 10.0;
inline constexpr double kSheetGap = 20.0;
inline constexpr double kHatchPitch = 4.0;
inline constexpr double kSvgMarkRadiusPct = 0.5;
inline constexpr const char* kSvgPartFill = "fill:rgb(128,128,128);stroke:rgb(0, 0, 0);stroke-width:0.1%";
inline constexpr const char* kSvgStrokeBlack = ";stroke:rgb(0, 0, 0);stroke-width:0.1%";
inline constexpr const char* kSvgMarkStyle = "stroke:rgb(192, 0, 0);stroke-width:0.1%;fill:none";
inline constexpr const char* kSvgHatchFill = "fill: url(#diagonalHatch0)";

std::string toSvg(const Order& order, const Solution& solution, bool includeMarks = true);
bool writeSvg(const std::string& path, const Order& order, const Solution& solution,
              bool includeMarks = true);
std::string toHtmlReport(const Order& order, const Solution& solution);

}  // namespace lcns
