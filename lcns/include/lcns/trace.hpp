#pragma once

namespace lcns {

// lcns/trace.hpp -- the recovered log prefixes, in their own header.
//
// These strings are written verbatim into the original's log, so reproducing them is fidelity, not
// decoration. They live here (rather than in engine.hpp) because nester.hpp needs them for the
// strategy classes' tracePrefix(), and engine.hpp includes nester.hpp -- putting them in either one
// made the other fail to see them (recorded as an open item in re/SWEEP.md, round 39). This header
// includes nothing of ours, so there is no cycle.
//
// RE trace prefixes -- verbatim strings the original writes to its log. They are user visible, so
// reproducing them exactly is real fidelity, not decoration. Each cites where it was read:
//   0x4B870  Multi::FlipNester::Run            "Flip "
//   0xB3AE0  Multi::FilterNester::Run          "Filter "
//   0x763ee0 / 0x76A130  packer cache thread pool
//                                              "Thread <" ... " updating part " ... " tilings."
//                                              "Packer Cache max threads: "
//   0x40720  RenestInHoles                     "Renested " ... " parts."      (nested TU)
//   0x1C7980 / 0x65DD20  beam visit report     "Visited Nodes=" "calls="
//   0x7B3510 / 0x7B3D20 / 0x7B4880  buckets    "Buckets : " "Buckets : empty"
//   0x655A30  beam try report                  "Beam width=" "Beam try nb : " "nb_buckets=" "beam_try_"
//   0x60A620  error reporter                   "*** INTERNAL ERROR: please contact support ***"
inline constexpr const char* kTraceFlip = "Flip ";
inline constexpr const char* kTraceFilter = "Filter ";
inline constexpr const char* kTraceNoFill = "NoFill(";   // RE 0x7f240
inline constexpr const char* kTraceRow = "Row ";          // RE 0x913e0
inline constexpr const char* kTracePipe = "Pipe ";        // RE 0x913e0
inline constexpr const char* kTraceThread = "Thread <";
inline constexpr const char* kTraceUpdatingPart = " updating part ";
inline constexpr const char* kTraceTilings = " tilings.";
inline constexpr const char* kTracePackerCacheThreads = "Packer Cache max threads: ";
inline constexpr const char* kTraceRenested = "Renested ";
inline constexpr const char* kTraceVisitedNodes = "Visited Nodes=";
inline constexpr const char* kTraceCalls = "calls=";
inline constexpr const char* kTraceBuckets = "Buckets : ";
inline constexpr const char* kTraceBucketsEmpty = "Buckets : empty";
inline constexpr const char* kTraceBeamWidth = "Beam width=";
inline constexpr const char* kTraceBeamTryNb = "Beam try nb : ";
inline constexpr const char* kTraceNbBuckets = "nb_buckets=";
inline constexpr const char* kTraceInternalError = "*** INTERNAL ERROR: please contact support ***";

}  // namespace lcns
