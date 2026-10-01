# BRIEF — reverse engineering `libcns_dump_64.dll` (Optalog CNS nesting engine)

## What the file is
- `D:\Nesting\nestfab\libcns_dump_64.dll` — 11,808,768 bytes, MD5 `01fea4b73a33dd233c66ca76235313fa`
- PE32+ **AMD64**, DLL, exports as **`liblcns.dll`** (DLL name inside export dir).
- Build: **MinGW-w64 GCC**, statically linked: Boost 1.63, COIN-OR **Clp 1.15.3 / CoinUtils**, **CryptoPP**, JsonCpp, libstdc++, WinPthreads.
  **The geometry kernel is entirely custom** — `Geom::MultiPolygon`, `PartPolygon`, `RealPolygon`, `PolygonProxy`,
  `OffsetManager`, `OffsetEvaluator`, `NoFitMap`, `NoFitStrips`, `HullSurf`, `NoFitMultiThreadComputer`.
  **Clipper, boost::geometry, CGAL, Eigen and any genetic algorithm are NOT present** (full-string scans return 0 hits —
  see `out_29.txt`). Do not assume Clipper anywhere.
- Product version resource: `CNS - unknown`, ProductVersion `5.0 - 68e2d90e72b4 5449`,
  build date strings `Jun 28 2019` / `14:03:08`, `68e2d90e72b4 5449 default`.
- Copyright string: `Authors Lionel and Lepere. All rights reserved.`
- It is a **memory dump** of a UPX-packed DLL: section names are still `BAB0` / `UPX1`, a fake UPX trailer
  sits at file offset 0x205, and the **IAT holds resolved absolute addresses from the dumping process**
  (e.g. `0x7FF99A5D0AF0`) with `OriginalFirstThunk == 0` — so the file is **not loadable**, it is
  analysis-only. Entropy of the code sections is ~6.2 (normal for x86-64 code) — the image IS unpacked.
- Source paths leaked: `C:\Users\renaud\nest\...`, `..\nesting\algos\compact.hpp`, `..\multi\nesting_nester.cpp`,
  `cns.cpp`, `cns_no_fit.cpp`, `internal.cpp`, `..\engine\engine.cpp`, `..\engine\cloud_engine.cpp`.

## Layout
| section | VA | virt size | raw size | flags |
|---|---|---|---|---|
| `BAB0` | 0x1000   | 0x724000 | 0x724000 | X, R  (CNS application code + rodata) |
| `UPX1` | 0x725000 | 0x41D000 | 0x41D000 | X, R  (CryptoPP, boost, clp, more app code/rodata) |
| `.rsrc`| 0xB42000 | 0x1000   | 0x1000   | W, R  (version info, import strings, export dir) |

ImageBase = `0x6B4C0000`.  For section `BAB0`, **file offset == RVA**.  Use `rva2off()` for anything else.

## Exports
- Export directory @ RVA `0xB424D8`; **NumberOfFunctions = 343, NumberOfNames = 0** (all names stripped).
- **336 non-zero entries → 168 unique addresses**; every address is listed **twice**
  (classic MinGW duplicate-export quirk).  Ordinal gaps at 63,64 / 75 / 106-109 (7 hollowed entries).
- All 168 exports are **free functions, not vtable slots**; they live in RVA `0x2AB0 .. 0x1AE40`.
- They are **C++ overloads** exported with mangled names (hence several share a base name).
- Text directory: `.pdata` @ RVA `0xA60000` (223,368 B) → **18,614 functions** covering `0x1000 .. 0x9A0A3A`.

## KEY: how the original function names were recovered
The whole codebase is instrumented with a scope tracer `dbg::symlog` (RTTI class `N3dbg6symlogE`),
which logs `__func__` on entry and `"// " + __func__` on exit.  Therefore each function references a
rodata literal equal to its **own unqualified name**.  Mapping "function → identifier-like string it
references" recovers names for 135/168 exports (132 with exactly one candidate).
`prof2.pkl` already contains `name`, `strings`, `callees`, `callers` per function.
Caveat: `__func__` gives the **unqualified** name only, so overloads collide
(e.g. 4 different exports are all `AddHoleToPart`) — disambiguate by inspecting arguments.

## Known names (135 exports) — verified by both tracer literals and assert/error strings
```
AddCircularPart* AddDefectToSheet AddExternalBoundaryToPart AddExternalBoundaryToSheet
AddHoleInToolPath AddHoleToPart AddInflatedToolPathToPart AddLeatherQualityZoneInPart
AddLeatherQualityZoneInSheet AddNonRectangularSheet AddOpenCuttingPathToPart
AddOptionalQuantityToPart AddPart AddPartSpecificAuthorizations AddPartToSuggestedPartsGrouping
AddPartVariantToPart AddRotatedPartVariantToPart AddSheet AddSuggestedPartsGrouping
AddToolPathToPart AsyncCancelAllComputationsAndDeleteLaunchingOrder
CNS_AddAssemblyGroupPart CNS_AddDefectFromNestedPart CNS_AddOpenToolPathToPart
CNS_AddPartToSuggestedPartsGrouping CNS_AddSuggestedPartsGrouping CNS_CreateAssemblyGroup
CNS_ForcePartOnBottomBorder CNS_GetCommonCut CNS_GetNestedPart CNS_GetNesting
CNS_GetNestingBoundingBox CNS_GetNestingDimensions CNS_GetNumberOfCommonCuts CNS_GetPartTorchInfos
CNS_GetRow CNS_GetSheet CNS_NoFitContext CNS_NoFitGetNumberOfHoles CNS_NoFitGetPoint
CNS_SetEvaluateIntermediateNestingsAsLast CNS_SetFloatingMode CNS_SetInterpartGap
CNS_SetMultiplicityPreference CNS_SetNoMixPreference CNS_SetNoOrientationMixOnPart
CNS_SetNoSheetMixPreference CNS_SetOriginPackingMode CNS_SetZoneRestrictedPart
CNS_SheetAddRestrictedZone CreateRestrictedZoneConstraint DeleteLaunchingOrder DeleteNoFitContext
DeleteNoFitGeometry DeleteNoFitNesting ForcePartInsideHole ForcePartOutsideHole
GenerateDxfNesting GenerateHtmlLaunchingOrderReport GenerateHtmlSolutionReport
GenerateLaunchingOrderProblem GetBuildDate GetBuildVersion GetComputationStatus GetFillRatio
GetHeight GetLength GetMajorVersion GetMark GetMultiplicity GetNestedPartPartVariant
GetNestingFillRatio GetNoFitMap GetNoFitPlacementMap GetNumberOfMarks GetNumberOfNestedParts
GetNumberOfNestings GetNumberOfRows GetPartUserString GetPartUserStringEx GetPartWithBadGeometry
GetPCId GetRow GetSheetUserString GetSheetUserStringEx GetSolution LaunchComputation
LaunchEstimateLocalComputation LaunchLimitedLocalComputation LaunchLocalComputation
NewLaunchingOrder NewNoFitContext NewNoFitNesting NoFitAddNestedPart NoFitGenerateSvgGeometry
NoFitGenerateSvgNesting NoFitGetNumberOfExternalPolygons NoFitGetNumberOfPoints
NoFitSetMaximumComplexity SetAutomaticStop SetCommonCutAuthorizations SetCommonCutCuttingPreference
SetCommonCutMode SetCommonCutObjective SetCommonCutSafetyPreference SetDefectGap
SetDetailedMultiTorchObjective SetExtraGapOnPart SetExtraParameters SetFillLastNestingStrategy
SetIncompatibleSheet SetInterpartGap SetLeatherMode SetLocalEngine SetLocalEngineThreads
SetLocalMaximumIterations SetLocalMaximumThreads SetMarkMode SetMultiTorchCuttingPreference
SetMultiTorchMode SetMultiTorchObjective SetObjective SetOffcutEvaluation SetOrigin
SetPartAuthorizations SetPartCommonCutMode SetPartPriority SetPartUserString SetPartialShearMode
SetPipeMode SetReorganizeBiggestPartNearOrigin SetReorganizeLongestPartNearOrigin SetRowMode
SetShearGap SetShearMode SetShearRepulseFromBorders SetSheetGaps SetSheetGrainDirection
SetSheetPrice SetSheetPriority SetSheetUserString SetSpecificSheetObjective SetSpecificSheetOrigin
UnLockLaunchingOrder UnLockLaunchingOrderOxy UnLockLaunchingOrderPCId UnLockLaunchingOrderSntl
WaitComputationStatus WaitComputationTermination WaitNextSolution
```

## Internal class model (from Itanium RTTI, 474 vtables recovered -> `vtables.json`)
- `dbg::symlog`, `dbg::file_error`, `dbg::frame_sink`, `dbg::symsink`, `dbg::pe_sink`
- `Multi::` (30 classes): `Nester`, `FlipNester`, `FilterNester`, `NoFillNester`, `TilingNester`,
  `CompactNester`, `LimitedNester`, `NestingNester`, `DatabaseNester`, `CompositeNester`,
  `RectangleNester`, `MultiTorchNester`, `RowNester`, `Supervisor`, `AdvancedStrategist`,
  `Strategist`, `StrategyAdder`, `StrategyBasicAdder`, `StrategyDescriber`, `SheetSelector`,
  `AllSheetSelector`, `LargestSheetSelector`, `RandomSheetSelector`, `NoMixSheetSelector`,
  `TerminalNode`, `SplitNode`, `Node`, `WrapObserver`, `TraceObserver`, `NestingObserver`,
  `CompactCanceller`, `RCompactCanceller`, `NoFitMapCanceller`, `SupervisorCanceller`,
  `PartUpdaterLimiter`, `NestingContextPool`, `NestingContext`, `BeamNesting`, `HoleRenester`, `Nesting`
- `Engine::`: `Engine`, `CompositeEngine`, `CloudEngine`, `NestingEngine`, `DelayedEngine`,
  `InfiniteEngine`, `MultiEngine`, `EquivalentEngine`, `BestObserver`, `CompositeObserver`,
  `EquivalentObserver`, `ObservingEngine`, `MakeMaxTimeEngine`, `MakeSkipSmallTimeEngine`
- `Pack::`: `Nester`, `BestNester`, `KnapsackNester`, `RecursiveNester`
- `Tiling::` (17): `BoxMultiTiler`, `SqueezeMultiTiler`, `BiModulePattern`, `MultiOrientedPartPattern`,
  `DensityEvaluator`, `UnlimitedDensityEvaluator`, `UnlimitedXDensityEvaluator`, `ObliqueEvaluator`,
  `QuantityEvaluator`, `ReusableEvaluator`, `MultitorchEvaluator`, `OldMultitorchEvaluator`,
  `BasicCandidater`, `CompositePart`, `Part`, `PackerCache`, `WarpCanceller`
- `Prc::`: `PriceComputer`, `AlphaPriceComputer`, `BoxPriceComputer`, `HullPriceComputer`,
  `LinearCombinationPricer`, `DimAlpha`, `SurfaceCoeffs`, `BoostAlpha`.
  NOTE (corrected): this is a **pricing / surface-measure SCORING layer**, not proven to be
  Dantzig-Wolfe column generation. The classes ARE constructed and reachable (vtable ADDRESS POINTS
  `vtable+16`, not headers, are what code references — searching the header gives a false "dead code"
  verdict). Reached from `Multi::CompactNester::Run` (0xB13D0) via
  `0xB0380 -> 0x67460 -> 0x1CD290 -> 0x1CB100 -> 0x1A6020 -> 0x1A5B20 -> 0x4D64C0` (pricer factory).
  `Prc::BoostAlpha/SurfaceCoeffs/DimAlpha` have zero pointer references -> non-polymorphic data types.
  See `findings_lp.md` and report §7.3.
- `Row::`: `Distancer`, `BasicDistancer`, `Squeezer`
- `Lp::LinearProgram`, `Coin::CoinLP` (wraps COIN-OR Clp)  -> **LP master problem**
- `Structure::`: `Observer`, `ClusterObserver`, `BoxAreaDimensioner`, `SizeDimensioner`,
  `WidthDimensioner`, `ParseProblemException`, `ParseSolutionException`
- `Utils::`: `Canceller`, `LogSink`, `OstreamSink<T>`, `Pool<T>`, `Timer::Implementation`,
  `TimerWinImplementation`, `ConnectException`, `ResolveException`, `TimeoutException`,
  `BadResponseException`
- `Compact::Compacter::Implementation`, `RCompact::RotateLogger`

## Cloud / licensing surface
- `cns1.optalog.com;cns2.optalog.com`, option `cns_force_cloud`, `Engine::CloudEngine`,
  HTTP PUT/GET to `/pb/`, `/sol/`, `/best_sol/` with `final` / `intermediate` payloads.
- License gates: `UnLockLaunchingOrderSntl` (Sentinel dongle), `UnLockLaunchingOrderOxy`,
  `UnLockLaunchingOrderPCId`, `GetPCId`; imports `CryptGenRandom`, `GetAdaptersInfo`
  (machine fingerprint), `bind`, `GetProcessMemoryInfo`, `MessageBoxA`.
- Local trace files: `c:\Temp\log_nest.txt`, `c:\Temp\cloud_nest.txt`, `c:\Temp\local_nest.txt`,
  `c:\Temp\debug_nest.txt`, `c:\Temp\cns.pb.json`, `c:\Temp\computation_solution.html`.
- A base64 blob sits at RVA `0x9A2080`: **984 base64 chars -> 736 bytes**, entropy 7.688, first byte 0xAF.
  It IS referenced — exactly twice: `lea rdx,[rip+..]` at `0x12BC04` (in fn `0x12BBA0`) and `0x12BD3F`
  (in fn `0x12BCC0`), each immediately followed by `call hasp_login`. It is the **Sentinel HASP Vendor Code**.
  Decoded copy: `re\blob_9a2080.bin`. See `findings_cloud_lic.md` §2.7.
- Licensing verdict: CryptoPP is statically linked but **has no call sites in the licence path**;
  verification is delegated to `hasp_windows_x64.dll` / `sntl_adminapi_windows_x64.dll`.
- LP/least-squares message table (LSQR `istop` strings) at RVA `0x9A74A0`.

## Tooling available on this machine
- Python: `C:\Users\16479\AppData\Local\Python\bin\python.exe` (3.14, `pefile` + `capstone` installed).
- **Shared helper**: `import sys; sys.path.insert(0, r"D:\Nesting\nestfab\re"); from lib import *`
  gives `data, pe, IB, SEC, rva2off, off2rva, norm, STRS, FUNCS, owner, func_extent, EXPORTS,
  load_prof, disasm(rva), rip_targets(rva), strings_of(rva)`.
- `re\xref.pkl` / `re\prof2.pkl` — per-function profile (size, nins, calls, callees, callers, strings, name).
- `re\vtables.json` — class -> vtable RVA -> virtual slot RVAs.
- `re\funcs.json` — all 18,614 `[begin,end]` RVAs.
- Useful existing scripts: `12_xref.py`, `14_name_exports.py`, `15_validate.py`.

## Deliverable expectations
Concrete, evidence-backed findings: function/ordinal, what it does, the algorithm and data structures,
key constants and callees, with RVA citations. Note clearly where a conclusion is inferred vs. proven.
