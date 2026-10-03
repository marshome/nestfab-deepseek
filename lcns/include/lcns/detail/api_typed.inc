// AUTO-ASSEMBLED typed view of the recovered API.  SIGNATURES ARE INFERRED.
//
// Every line below was derived from the reverse engineering as follows:
//   * the NAME comes from the dbg::symlog entry label literal (99% of cases), and
//   * the PARAMETER LIST is our best reconstruction from argument-register analysis
//     (rcx/rdx/r8/r9 + xmm0..3) plus the semantic evidence (assert strings, callees,
//     saved field offsets) documented in re/exports_table.json and re/REPORT.md.
//
// There is no symbol or debug information in the binary, so a parameter list can be
// wrong in the details (extra opaque parameters, enums passed as int, ...). Anything
// not listed here is still reachable via lcns::Library::byName().
//
// Format: LCNS_TYPED(return_type, name, (parameter list))

// ---------------------------------------------------------------- lifecycle
LCNS_TYPED(OrderHandle, NewLaunchingOrder, (int, double, double))            // inferred
LCNS_TYPED(int, DeleteLaunchingOrder, (OrderHandle))                          // inferred

// ---------------------------------------------------------------- problem build
LCNS_TYPED(Sheet, AddSheet, (OrderHandle, int, double, double, int))                        // inferred
LCNS_TYPED(Sheet, AddNonRectangularSheet, (OrderHandle, int, int, const double*, int))      // inferred
LCNS_TYPED(Sheet, AddNonRectangularPolygonSheet, (OrderHandle, int, int, const double*, int))  // inferred
LCNS_TYPED(Part, AddPart, (OrderHandle, int, int, const double*, int))                      // inferred
LCNS_TYPED(Part, AddPolygonPart, (OrderHandle, int, int, const double*, int))               // inferred
LCNS_TYPED(Part, AddCircularPart, (OrderHandle, int, double, double, double, int))          // inferred
LCNS_TYPED(Part, AddRectanglePart, (OrderHandle, int, double, double, double, double, int)) // inferred
LCNS_TYPED(int, AddHoleToPart, (Part, int, int, const double*))                       // inferred, 4 overloads
LCNS_TYPED(int, AddPolygonHoleToPart, (Part, int, const double*))                     // inferred
LCNS_TYPED(int, AddCircularHoleToPart, (Part, double, double, double))                // inferred
LCNS_TYPED(int, AddRectangularHoleToPart, (Part, double, double, double, double))     // inferred
LCNS_TYPED(int, AddExternalBoundaryToPart, (Part, int, const double*))                // inferred
LCNS_TYPED(int, AddExternalPolygonBoundaryToPart, (Part, const double*))              // inferred
LCNS_TYPED(int, AddCircularExternalBoundaryToPart, (Part, double, double, double))    // inferred
LCNS_TYPED(int, AddRectangularExternalBoundaryToPart, (Part, double, double, double, double))  // inferred
LCNS_TYPED(int, AddDefectToSheet, (Sheet, int, const double*))                        // inferred
LCNS_TYPED(int, AddPolygonDefectToSheet, (Sheet, const double*))                      // inferred
LCNS_TYPED(int, AddOptionalQuantityToPart, (Part, int))                               // inferred
LCNS_TYPED(int, AddToolPathToPart, (Part, int, const double*))                        // inferred
LCNS_TYPED(int, AddHoleInToolPath, (Part, int, const double*))                        // inferred
LCNS_TYPED(int, AddInflatedToolPathToPart, (Part, double))                            // inferred
LCNS_TYPED(int, AddOpenCuttingPathToPart, (Part, int, const double*))                 // inferred

// ---------------------------------------------------------------- setters
LCNS_TYPED(void, SetObjective, (OrderHandle, Objective))                       // enum proven (0x511080)
LCNS_TYPED(void, SetOrigin, (OrderHandle, NestingOrigin))                      // enum proven
LCNS_TYPED(void, SetInterpartGap, (OrderHandle, double))                       // gap >= 0 asserted
LCNS_TYPED(void, SetExtraGapOnPart, (OrderHandle, int, double))                // Part+0x10 per RE
LCNS_TYPED(void, SetDefectGap, (OrderHandle, double))                          // Order+0x118 per RE
LCNS_TYPED(void, SetShearGap, (OrderHandle, double))                           // Order+0x50
LCNS_TYPED(void, SetShearMode, (OrderHandle, int))                             // Order+0x44
LCNS_TYPED(void, SetPartialShearMode, (OrderHandle, int))                      // writes 0x48 and 0x44
LCNS_TYPED(void, SetShearRepulseFromBorders, (OrderHandle, int))               // Order+0x58
LCNS_TYPED(void, SetRowMode, (OrderHandle, int))                               // Order+0x128 row block
LCNS_TYPED(void, SetPipeMode, (OrderHandle, int))                              // Order+0x158 pipe block
LCNS_TYPED(void, SetMarkMode, (OrderHandle, int))                              // Order+0xE8/0xF0
LCNS_TYPED(void, SetLeatherMode, (OrderHandle, int))                           // quality zones
LCNS_TYPED(void, SetAutomaticStop, (OrderHandle, int))                         // Order+0x240
LCNS_TYPED(void, SetFillLastNestingStrategy, (OrderHandle, int))
LCNS_TYPED(void, SetOffcutEvaluation, (OrderHandle, double, double, double))   // 3 doubles per RE
LCNS_TYPED(void, SetSheetPrice, (OrderHandle, double))                         // Sheet+0x138
LCNS_TYPED(void, SetSheetPriority, (OrderHandle, int))                         // Sheet+0x120
LCNS_TYPED(void, SetSheetGrainDirection, (OrderHandle, int))                   // Sheet+0x134
LCNS_TYPED(void, SetSheetGaps, (OrderHandle, double, double, double, double))  // Sheet+0xF8..0x110
LCNS_TYPED(void, SetPartPriority, (OrderHandle, int, int))
LCNS_TYPED(void, SetPartUserString, (OrderHandle, int, const char*))
LCNS_TYPED(void, SetSheetUserString, (OrderHandle, int, const char*))
LCNS_TYPED(void, SetPartAuthorizations, (OrderHandle, int, int))
LCNS_TYPED(void, AddPartSpecificAuthorizations, (OrderHandle, int, int))
LCNS_TYPED(void, SetIncompatibleSheet, (OrderHandle, int, int))                // Order+0x1F8
LCNS_TYPED(void, SetSpecificSheetOrigin, (OrderHandle, int, double, double))   // Order+0x124/0x128
LCNS_TYPED(void, SetSpecificSheetObjective, (OrderHandle, int, int))           // Order+0x12C/0x130
LCNS_TYPED(void, SetExtraParameters, (OrderHandle, const char*, double))       // key -> Order+0x220..0x238
LCNS_TYPED(void, SetReorganizeBiggestPartNearOrigin, (OrderHandle, int))       // Order+0x22
LCNS_TYPED(void, SetReorganizeLongestPartNearOrigin, (OrderHandle, int))       // Order+0x23
LCNS_TYPED(void, SetLocalEngine, (OrderHandle, int, int))                      // Order+0x200/0x201
LCNS_TYPED(void, SetLocalEngineThreads, (OrderHandle, int, int))
LCNS_TYPED(void, SetLocalMaximumThreads, (OrderHandle, int))                   // Order+0x1F8
LCNS_TYPED(void, SetLocalMaximumIterations, (OrderHandle, int))                // Order+0x1FC

// common cut (Order+0x5C..0x90, mode tag at +0x88: 1 = preset @+0x8C, 0 = objective @+0x90)
LCNS_TYPED(void, SetCommonCutMode, (OrderHandle, int, int))
LCNS_TYPED(void, SetPartCommonCutMode, (OrderHandle, int, int))                // Part+0x1C
LCNS_TYPED(void, SetCommonCutSafetyPreference, (OrderHandle, int, int))
LCNS_TYPED(void, SetCommonCutCuttingPreference, (OrderHandle, int, int))
LCNS_TYPED(void, SetCommonCutObjective, (OrderHandle, double, double))
LCNS_TYPED(void, SetCommonCutAuthorizations, (OrderHandle, int, int, int))

// multi-torch (Order+0x98..0xD8)
LCNS_TYPED(void, SetMultiTorchMode, (OrderHandle, int, int, double, double, int))
LCNS_TYPED(void, SetMultiTorchCuttingPreference, (OrderHandle, int, int))
LCNS_TYPED(void, SetMultiTorchObjective, (OrderHandle, double, double, double, double))
LCNS_TYPED(void, SetDetailedMultiTorchObjective, (OrderHandle, double, double, double, double))

// grouping / zones
LCNS_TYPED(void, AddSuggestedPartsGrouping, (OrderHandle, int, int))
LCNS_TYPED(void, AddPartToSuggestedPartsGrouping, (OrderHandle, int, int))
LCNS_TYPED(void, CNS_CreateAssemblyGroup, (OrderHandle, int))
LCNS_TYPED(void, CNS_AddAssemblyGroupPart, (OrderHandle, int, int, int))
LCNS_TYPED(void, CNS_SheetAddRestrictedZone, (OrderHandle, int, int, const double*))
LCNS_TYPED(void, CNS_SetZoneRestrictedPart, (OrderHandle, int, int))
LCNS_TYPED(void, CNS_ForcePartOnBottomBorder, (OrderHandle, int, int))
LCNS_TYPED(void, CreateRestrictedZoneConstraint, (OrderHandle, int, int))
LCNS_TYPED(void, AddLeatherQualityZoneInPart, (Part, int, int, const double*))
LCNS_TYPED(void, AddLeatherQualityZoneInSheet, (Sheet, int, int, const double*))

// ---------------------------------------------------------------- licensing
LCNS_TYPED(int, UnLockLaunchingOrder, (OrderHandle, int))                              // Order+0x244 = mode
LCNS_TYPED(int, UnLockLaunchingOrderSntl, (OrderHandle, const char*, const char*))     // 2 keys -> +0x248/+0x268
LCNS_TYPED(int, UnLockLaunchingOrderOxy, (OrderHandle, const char*, const char*))
LCNS_TYPED(int, UnLockLaunchingOrderPCId, (OrderHandle, const char*, const char*))
LCNS_TYPED(const char*, GetPCId, ())                                            // "%ld" of MAC+volume hash

// ---------------------------------------------------------------- computation control
LCNS_TYPED(void*, LaunchLocalComputation, (OrderHandle, double))                       // returns new engine object
LCNS_TYPED(void*, LaunchLimitedLocalComputation, (OrderHandle, double))
LCNS_TYPED(void*, LaunchEstimateLocalComputation, (OrderHandle, double))
LCNS_TYPED(void*, LaunchComputation, (OrderHandle, const char*, const char*, double))  // cloud entry
LCNS_TYPED(int, WaitNextSolution, (void*, int*))
LCNS_TYPED(int, WaitComputationTermination, (void*))
LCNS_TYPED(int, GetComputationStatus, (void*))
LCNS_TYPED(int, CancelComputation, (void*))
LCNS_TYPED(int, TerminateComputation, (void*))
LCNS_TYPED(int, AsyncCancelAllComputationsAndDeleteLaunchingOrder, (OrderHandle))

// ---------------------------------------------------------------- result query
LCNS_TYPED(SolutionHandle, GetSolution, (OrderHandle))
LCNS_TYPED(int, GetNumberOfNestings, (SolutionHandle))
LCNS_TYPED(Nesting, GetNesting, (SolutionHandle, int))
LCNS_TYPED(int, GetNumberOfNestedParts, (Nesting))
LCNS_TYPED(NestedPart, GetNestedPart, (Nesting, int))
LCNS_TYPED(NestedPart, GetNestedPartPartVariant, (Nesting, int))
LCNS_TYPED(Sheet, GetSheet, (OrderHandle, int))
LCNS_TYPED(double, GetLength, (Part))
LCNS_TYPED(double, GetHeight, (Part))
LCNS_TYPED(int, GetMultiplicity, (Part))
LCNS_TYPED(double, GetFillRatio, (SolutionHandle))
LCNS_TYPED(double, GetNestingFillRatio, (Nesting))
LCNS_TYPED(int, GetNestingBoundingBox, (OrderHandle, double*, double*, double*, double*))
LCNS_TYPED(int, GetNestingDimensions, (Nesting, double*, double*))
LCNS_TYPED(int, GetPartWithBadGeometry, (OrderHandle))
LCNS_TYPED(int, GetPartUserString, (Part, const char**))
LCNS_TYPED(int, GetSheetUserString, (Sheet, const char**))
LCNS_TYPED(int, GetNumberOfCommonCuts, (OrderHandle))
LCNS_TYPED(int, GetCommonCut, (OrderHandle, int, void*))
LCNS_TYPED(int, GetPartTorchInfos, (OrderHandle, int, void*))
LCNS_TYPED(int, GetNumberOfRows, (OrderHandle))
LCNS_TYPED(int, GetRow, (OrderHandle, int, double*, double*))                          // y-band start/end
LCNS_TYPED(int, GetNumberOfMarks, (OrderHandle))
LCNS_TYPED(int, GetMark, (OrderHandle, int))
LCNS_TYPED(int, GetMajorVersion, ())
LCNS_TYPED(const char*, GetBuildVersion, ())
LCNS_TYPED(const char*, GetBuildDate, ())

// ---------------------------------------------------------------- reports
LCNS_TYPED(int, GenerateDxfNesting, (Nesting, const char*))
LCNS_TYPED(int, GenerateHtmlSolutionReport, (SolutionHandle, const char*))
LCNS_TYPED(int, GenerateHtmlLaunchingOrderReport, (OrderHandle, const char*))
LCNS_TYPED(int, GenerateLaunchingOrderProblem, (OrderHandle, const char*))

// ---------------------------------------------------------------- NoFit (NFP / geometry)
LCNS_TYPED(NoFitContext, NewNoFitContext, (void*))                               // operator new(0xF0)
LCNS_TYPED(void, DeleteNoFitContext, (NoFitContext))
LCNS_TYPED(NoFitGeometry, GetNoFitMap, (NoFitContext, int, int))
LCNS_TYPED(NoFitGeometry, GetNoFitPlacementMap, (NoFitContext, int, int))
LCNS_TYPED(int, NoFitGetNumberOfExternalPolygons, (NoFitGeometry))               // len / 48
LCNS_TYPED(int, NoFitGetNumberOfInternalHoles, (NoFitGeometry, int))
LCNS_TYPED(int, NoFitGetNumberOfPoints, (NoFitGeometry, int, int, int))
LCNS_TYPED(int, NoFitGetPoint, (NoFitGeometry, int, int, int, double*, double*))
LCNS_TYPED(void, NoFitSetMaximumComplexity, (NoFitContext, int))                 // default 25000
LCNS_TYPED(NoFitNesting, NewNoFitNesting, (NoFitContext))
LCNS_TYPED(void, DeleteNoFitNesting, (NoFitNesting))
LCNS_TYPED(void, NoFitAddNestedPart, (NoFitNesting, Part, int, double, double, double))
LCNS_TYPED(void, DeleteNoFitGeometry, (NoFitGeometry))
LCNS_TYPED(int, NoFitGenerateSvgNesting, (NoFitNesting, const char*))
LCNS_TYPED(int, NoFitGenerateSvgGeometry, (NoFitGeometry, const char*))
