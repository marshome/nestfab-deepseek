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
LCNS_TYPED(Order, NewLaunchingOrder, (int, double, double))            // inferred
LCNS_TYPED(int, DeleteLaunchingOrder, (Order))                          // inferred

// ---------------------------------------------------------------- problem build
LCNS_TYPED(Sheet, AddSheet, (Order, int, double, double, int))                        // inferred
LCNS_TYPED(Sheet, AddNonRectangularSheet, (Order, int, int, const double*, int))      // inferred
LCNS_TYPED(Sheet, AddNonRectangularPolygonSheet, (Order, int, int, const double*, int))  // inferred
LCNS_TYPED(Part, AddPart, (Order, int, int, const double*, int))                      // inferred
LCNS_TYPED(Part, AddPolygonPart, (Order, int, int, const double*, int))               // inferred
LCNS_TYPED(Part, AddCircularPart, (Order, int, double, double, double, int))          // inferred
LCNS_TYPED(Part, AddRectanglePart, (Order, int, double, double, double, double, int)) // inferred
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
LCNS_TYPED(void, SetObjective, (Order, Objective))                       // enum proven (0x511080)
LCNS_TYPED(void, SetOrigin, (Order, NestingOrigin))                      // enum proven
LCNS_TYPED(void, SetInterpartGap, (Order, double))                       // gap >= 0 asserted
LCNS_TYPED(void, SetExtraGapOnPart, (Order, int, double))                // Part+0x10 per RE
LCNS_TYPED(void, SetDefectGap, (Order, double))                          // Order+0x118 per RE
LCNS_TYPED(void, SetShearGap, (Order, double))                           // Order+0x50
LCNS_TYPED(void, SetShearMode, (Order, int))                             // Order+0x44
LCNS_TYPED(void, SetPartialShearMode, (Order, int))                      // writes 0x48 and 0x44
LCNS_TYPED(void, SetShearRepulseFromBorders, (Order, int))               // Order+0x58
LCNS_TYPED(void, SetRowMode, (Order, int))                               // Order+0x128 row block
LCNS_TYPED(void, SetPipeMode, (Order, int))                              // Order+0x158 pipe block
LCNS_TYPED(void, SetMarkMode, (Order, int))                              // Order+0xE8/0xF0
LCNS_TYPED(void, SetLeatherMode, (Order, int))                           // quality zones
LCNS_TYPED(void, SetAutomaticStop, (Order, int))                         // Order+0x240
LCNS_TYPED(void, SetFillLastNestingStrategy, (Order, int))
LCNS_TYPED(void, SetOffcutEvaluation, (Order, double, double, double))   // 3 doubles per RE
LCNS_TYPED(void, SetSheetPrice, (Order, double))                         // Sheet+0x138
LCNS_TYPED(void, SetSheetPriority, (Order, int))                         // Sheet+0x120
LCNS_TYPED(void, SetSheetGrainDirection, (Order, int))                   // Sheet+0x134
LCNS_TYPED(void, SetSheetGaps, (Order, double, double, double, double))  // Sheet+0xF8..0x110
LCNS_TYPED(void, SetPartPriority, (Order, int, int))
LCNS_TYPED(void, SetPartUserString, (Order, int, const char*))
LCNS_TYPED(void, SetSheetUserString, (Order, int, const char*))
LCNS_TYPED(void, SetPartAuthorizations, (Order, int, int))
LCNS_TYPED(void, AddPartSpecificAuthorizations, (Order, int, int))
LCNS_TYPED(void, SetIncompatibleSheet, (Order, int, int))                // Order+0x1F8
LCNS_TYPED(void, SetSpecificSheetOrigin, (Order, int, double, double))   // Order+0x124/0x128
LCNS_TYPED(void, SetSpecificSheetObjective, (Order, int, int))           // Order+0x12C/0x130
LCNS_TYPED(void, SetExtraParameters, (Order, const char*, double))       // key -> Order+0x220..0x238
LCNS_TYPED(void, SetReorganizeBiggestPartNearOrigin, (Order, int))       // Order+0x22
LCNS_TYPED(void, SetReorganizeLongestPartNearOrigin, (Order, int))       // Order+0x23
LCNS_TYPED(void, SetLocalEngine, (Order, int, int))                      // Order+0x200/0x201
LCNS_TYPED(void, SetLocalEngineThreads, (Order, int, int))
LCNS_TYPED(void, SetLocalMaximumThreads, (Order, int))                   // Order+0x1F8
LCNS_TYPED(void, SetLocalMaximumIterations, (Order, int))                // Order+0x1FC

// common cut (Order+0x5C..0x90, mode tag at +0x88: 1 = preset @+0x8C, 0 = objective @+0x90)
LCNS_TYPED(void, SetCommonCutMode, (Order, int, int))
LCNS_TYPED(void, SetPartCommonCutMode, (Order, int, int))                // Part+0x1C
LCNS_TYPED(void, SetCommonCutSafetyPreference, (Order, int, int))
LCNS_TYPED(void, SetCommonCutCuttingPreference, (Order, int, int))
LCNS_TYPED(void, SetCommonCutObjective, (Order, double, double))
LCNS_TYPED(void, SetCommonCutAuthorizations, (Order, int, int, int))

// multi-torch (Order+0x98..0xD8)
LCNS_TYPED(void, SetMultiTorchMode, (Order, int, int, double, double, int))
LCNS_TYPED(void, SetMultiTorchCuttingPreference, (Order, int, int))
LCNS_TYPED(void, SetMultiTorchObjective, (Order, double, double, double, double))
LCNS_TYPED(void, SetDetailedMultiTorchObjective, (Order, double, double, double, double))

// grouping / zones
LCNS_TYPED(void, AddSuggestedPartsGrouping, (Order, int, int))
LCNS_TYPED(void, AddPartToSuggestedPartsGrouping, (Order, int, int))
LCNS_TYPED(void, CNS_CreateAssemblyGroup, (Order, int))
LCNS_TYPED(void, CNS_AddAssemblyGroupPart, (Order, int, int, int))
LCNS_TYPED(void, CNS_SheetAddRestrictedZone, (Order, int, int, const double*))
LCNS_TYPED(void, CNS_SetZoneRestrictedPart, (Order, int, int))
LCNS_TYPED(void, CNS_ForcePartOnBottomBorder, (Order, int, int))
LCNS_TYPED(void, CreateRestrictedZoneConstraint, (Order, int, int))
LCNS_TYPED(void, AddLeatherQualityZoneInPart, (Part, int, int, const double*))
LCNS_TYPED(void, AddLeatherQualityZoneInSheet, (Sheet, int, int, const double*))

// ---------------------------------------------------------------- licensing
LCNS_TYPED(int, UnLockLaunchingOrder, (Order, int))                              // Order+0x244 = mode
LCNS_TYPED(int, UnLockLaunchingOrderSntl, (Order, const char*, const char*))     // 2 keys -> +0x248/+0x268
LCNS_TYPED(int, UnLockLaunchingOrderOxy, (Order, const char*, const char*))
LCNS_TYPED(int, UnLockLaunchingOrderPCId, (Order, const char*, const char*))
LCNS_TYPED(const char*, GetPCId, ())                                            // "%ld" of MAC+volume hash

// ---------------------------------------------------------------- computation control
LCNS_TYPED(void*, LaunchLocalComputation, (Order, double))                       // returns new engine object
LCNS_TYPED(void*, LaunchLimitedLocalComputation, (Order, double))
LCNS_TYPED(void*, LaunchEstimateLocalComputation, (Order, double))
LCNS_TYPED(void*, LaunchComputation, (Order, const char*, const char*, double))  // cloud entry
LCNS_TYPED(int, WaitNextSolution, (void*, int*))
LCNS_TYPED(int, WaitComputationTermination, (void*))
LCNS_TYPED(int, GetComputationStatus, (void*))
LCNS_TYPED(int, CancelComputation, (void*))
LCNS_TYPED(int, TerminateComputation, (void*))
LCNS_TYPED(int, AsyncCancelAllComputationsAndDeleteLaunchingOrder, (Order))

// ---------------------------------------------------------------- result query
LCNS_TYPED(Solution, GetSolution, (Order))
LCNS_TYPED(int, GetNumberOfNestings, (Solution))
LCNS_TYPED(Nesting, GetNesting, (Solution, int))
LCNS_TYPED(int, GetNumberOfNestedParts, (Nesting))
LCNS_TYPED(NestedPart, GetNestedPart, (Nesting, int))
LCNS_TYPED(NestedPart, GetNestedPartPartVariant, (Nesting, int))
LCNS_TYPED(Sheet, GetSheet, (Order, int))
LCNS_TYPED(double, GetLength, (Part))
LCNS_TYPED(double, GetHeight, (Part))
LCNS_TYPED(int, GetMultiplicity, (Part))
LCNS_TYPED(double, GetFillRatio, (Solution))
LCNS_TYPED(double, GetNestingFillRatio, (Nesting))
LCNS_TYPED(int, GetNestingBoundingBox, (Order, double*, double*, double*, double*))
LCNS_TYPED(int, GetNestingDimensions, (Nesting, double*, double*))
LCNS_TYPED(int, GetPartWithBadGeometry, (Order))
LCNS_TYPED(int, GetPartUserString, (Part, const char**))
LCNS_TYPED(int, GetSheetUserString, (Sheet, const char**))
LCNS_TYPED(int, GetNumberOfCommonCuts, (Order))
LCNS_TYPED(int, GetCommonCut, (Order, int, void*))
LCNS_TYPED(int, GetPartTorchInfos, (Order, int, void*))
LCNS_TYPED(int, GetNumberOfRows, (Order))
LCNS_TYPED(int, GetRow, (Order, int, double*, double*))                          // y-band start/end
LCNS_TYPED(int, GetNumberOfMarks, (Order))
LCNS_TYPED(int, GetMark, (Order, int))
LCNS_TYPED(int, GetMajorVersion, ())
LCNS_TYPED(const char*, GetBuildVersion, ())
LCNS_TYPED(const char*, GetBuildDate, ())

// ---------------------------------------------------------------- reports
LCNS_TYPED(int, GenerateDxfNesting, (Nesting, const char*))
LCNS_TYPED(int, GenerateHtmlSolutionReport, (Solution, const char*))
LCNS_TYPED(int, GenerateHtmlLaunchingOrderReport, (Order, const char*))
LCNS_TYPED(int, GenerateLaunchingOrderProblem, (Order, const char*))

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
