# liblcns.dll 导出函数表 (168 个唯一函数, 168x2=336 个序号)

VM 模式: 无名字导出 (NumberOfNames=0), 以下名字由 `dbg::symlog` 作用域跟踪器写入的 `__func__` 字面量恢复。

## 0-lifecycle  (2)

| ord | ordinals | RVA | size | 名称 | 跟踪标签 | C 别名 | 整数参 | 浮点参 | 栈参 | 估参 | 返回xmm0 | 恢复 | 证据 |
|---:|---|---|---:|---|---|---|---:|---:|---:|---:|:--:|:--:|---|
| 7 | 7-8 | 0x0118F0 | 3660 | `DeleteLaunchingOrder` | `DeleteLaunchingOrder` |  | 2 | 0 | 0 | 2 |  | yes | *** ERROR unterminated/cancelled computation *** \| ERROR unterminated/cancelled computation |
| 37 | 37-38 | 0x014620 | 1081 | `NewLaunchingOrder` | `NewLaunchingOrder` |  | 1 | 2 | 0 | 3 | Y | yes |  |

## 1-NoFit (NFP/geometry)  (8)

| ord | ordinals | RVA | size | 名称 | 跟踪标签 | C 别名 | 整数参 | 浮点参 | 栈参 | 估参 | 返回xmm0 | 恢复 | 证据 |
|---:|---|---|---:|---|---|---|---:|---:|---:|---:|:--:|:--:|---|
| 238 | 238-239 | 0x0089D0 | 54 | `NoFitGetNumberOfExternalPolygons` | `NoFitGetNumberOfExternalPolygons` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 240 | 240-241 | 0x008E70 | 335 | `NoFitGetNumberOfInternalHoles` | `NoFitGetNumberOfInternalHoles` | `CNS_NoFitGetNumberOfHoles` | 2 | 0 | 8 | 10 |  | yes | cns_no_fit.cpp \| external_number < n |
| 242 | 242-243 | 0x008FC0 | 497 | `NoFitGetNumberOfPoints` |  |  | 3 | 0 | 1 | 4 |  | yes |  |
| 244 | 244-245 | 0x0091C0 | 366 | `NoFitGetPoint` | `NoFitGetPoint` | `CNS_NoFitGetPoint` | 4 | 1 | 10 | 15 | Y | yes | cns_no_fit.cpp \| point_number < ring.size() |
| 320 | 320-321 | 0x00A9D0 | 240 | `NoFitAddNestedPart` | `NoFitAddNestedPart` |  | 3 | 1 | 6 | 10 |  | yes |  |
| 326 | 326-327 | 0x009550 | 573 | `NoFitGenerateSvgNesting` | `NoFitGenerateSvgNesting` |  | 3 | 0 | 2 | 5 |  | yes |  |
| 328 | 328-329 | 0x009790 | 403 | `NoFitGenerateSvgGeometry` | `NoFitGenerateSvgGeometry` |  | 3 | 0 | 2 | 5 |  | yes |  |
| 340 | 340-341 | 0x009930 | 443 | `NoFitSetMaximumComplexity` |  |  | 2 | 0 | 12 | 14 |  | yes |  |

## 2-setters  (53)

| ord | ordinals | RVA | size | 名称 | 跟踪标签 | C 别名 | 整数参 | 浮点参 | 栈参 | 估参 | 返回xmm0 | 恢复 | 证据 |
|---:|---|---|---:|---|---|---|---:|---:|---:|---:|:--:|:--:|---|
| 39 | 39-40 | 0x00CF20 | 303 | `SetInterpartGap` | `SetInterpartGap` | `CNS_SetInterpartGap` | 1 | 1 | 8 | 10 |  | yes | cns.cpp \| (gap >= 0.0) && "Negative part gap unsupported" |
| 41 | 41-42 | 0x00C1A0 | 241 | `SetPartAuthorizations` | `SetPartAuthorizations` |  | 3 | 2 | 0 | 5 | Y | yes |  |
| 43 | 43-44 | 0x00C420 | 446 | `SetPartUserString` |  |  | 2 | 0 | 3 | 5 |  | yes |  |
| 45 | 45-46 | 0x00CCB0 | 527 | `SetSheetGaps` |  |  | 1 | 3 | 9 | 13 |  | yes |  |
| 57 | 57-58 | 0x00C670 | 446 | `SetSheetUserString` |  |  | 2 | 0 | 3 | 5 |  | yes |  |
| 65 | 65-66 | 0x011120 | 868 | `SetExtraParameters` |  |  | 3 | 0 | 15 | 18 |  | yes |  |
| 67 | 67-68 | 0x013C90 | 411 | `SetSheetPriority` |  |  | 2 | 0 | 12 | 14 |  | yes |  |
| 73 | 73-74 | 0x00D370 | 61 | `SetLocalEngine` | `SetLocalEngine` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 78 | 78-79 | 0x00CEC0 | 45 | `SetObjective` | `SetObjective` |  | 2 | 1 | 0 | 3 |  | yes |  |
| 80 | 80-81 | 0x0109C0 | 388 | `SetDefectGap` |  |  | 1 | 1 | 3 | 5 |  | yes |  |
| 82 | 82-83 | 0x00D3B0 | 68 | `SetLocalMaximumThreads` | `SetLocalMaximumThreads` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 84 | 84-85 | 0x00D400 | 36 | `SetLocalMaximumIterations` | `SetLocalMaximumIterations` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 86 | 86-87 | 0x00D050 | 334 | `SetOrigin` |  |  | 2 | 0 | 12 | 14 |  | yes |  |
| 98 | 98-99 | 0x00C9A0 | 372 | `SetSheetGrainDirection` |  |  | 2 | 0 | 1 | 3 |  | yes |  |
| 126 | 126-127 | 0x00C2A0 | 382 | `SetPartPriority` |  |  | 2 | 0 | 12 | 14 |  | yes |  |
| 128 | 128-129 | 0x00D1A0 | 353 | `CNS_SetMultiplicityPreference` |  |  | 2 | 1 | 28 | 31 | Y | yes |  |
| 140 | 140-141 | 0x00E010 | 353 | `SetAutomaticStop` |  |  | 2 | 0 | 12 | 14 |  | yes |  |
| 142 | 142-143 | 0x00E2D0 | 399 | `SetOffcutEvaluation` |  |  | 1 | 3 | 7 | 11 |  | yes |  |
| 144 | 144-145 | 0x00DD90 | 36 | `SetFillLastNestingStrategy` | `SetFillLastNestingStrategy` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 146 | 146-147 | 0x00DDC0 | 33 | `SetShearMode` | `SetShearMode` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 148 | 148-149 | 0x00E460 | 404 | `SetCommonCutMode` |  |  | 2 | 1 | 3 | 6 |  | yes |  |
| 150 | 150-151 | 0x00E940 | 354 | `SetCommonCutSafetyPreference` |  |  | 2 | 0 | 12 | 14 |  | yes |  |
| 152 | 152-153 | 0x00EAB0 | 468 | `SetCommonCutAuthorizations` |  |  | 2 | 2 | 5 | 9 |  | yes |  |
| 154 | 154-155 | 0x00EC90 | 340 | `SetCommonCutCuttingPreference` |  |  | 2 | 0 | 1 | 3 |  | yes |  |
| 156 | 156-157 | 0x00EDF0 | 337 | `SetCommonCutObjective` |  |  | 1 | 2 | 5 | 8 |  | yes |  |
| 166 | 166-167 | 0x00DE50 | 36 | `SetPartCommonCutMode` | `SetPartCommonCutMode` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 172 | 172-173 | 0x00CB20 | 388 | `SetSheetPrice` |  |  | 1 | 1 | 3 | 5 |  | yes |  |
| 174 | 174-175 | 0x00EF50 | 479 | `SetMultiTorchMode` |  |  | 3 | 1 | 5 | 9 |  | yes |  |
| 176 | 176-177 | 0x00F130 | 388 | `SetMultiTorchCuttingPreference` |  |  | 3 | 0 | 1 | 4 |  | yes |  |
| 178 | 178-179 | 0x00F2C0 | 633 | `SetMultiTorchObjective` |  |  | 2 | 4 | 7 | 13 | Y | yes |  |
| 180 | 180-181 | 0x014450 | 449 | `SetExtraGapOnPart` |  |  | 2 | 1 | 3 | 6 |  | yes |  |
| 182 | 182-183 | 0x00DD30 | 36 | `CNS_SetFloatingMode` | `CNS_SetFloatingMode` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 186 | 186-187 | 0x00F540 | 629 | `SetDetailedMultiTorchObjective` |  |  | 1 | 3 | 13 | 17 |  | yes |  |
| 188 | 188-189 | 0x00D310 | 33 | `CNS_SetNoMixPreference` | `CNS_SetNoMixPreference` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 190 | 190-191 | 0x00DBB0 | 382 | `CNS_SetNoOrientationMixOnPart` |  |  | 2 | 0 | 12 | 14 |  | yes |  |
| 202 | 202-203 | 0x016DE0 | 61 | `CNS_SetPartVariantAuthorizations` | `// CNS_SetPartVariantAuthorizations` |  | 3 | 1 | 0 | 4 |  | yes | // CNS_SetPartVariantAuthorizations |
| 212 | 212-213 | 0x00CEF0 | 45 | `SetShearGap` | `SetShearGap` |  | 1 | 1 | 0 | 2 |  | yes |  |
| 214 | 214-215 | 0x011490 | 423 | `SetIncompatibleSheet` |  |  | 2 | 0 | 1 | 3 |  | yes |  |
| 222 | 222-223 | 0x00D340 | 33 | `CNS_SetNoSheetMixPreference` | `CNS_SetNoSheetMixPreference` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 246 | 246-247 | 0x0188D0 | 529 | `SetMarkMode` |  |  | 2 | 2 | 1 | 5 |  | yes |  |
| 256 | 256-257 | 0x00FBF0 | 244 | `SetRowMode` | `SetRowMode` |  | 2 | 2 | 3 | 7 |  | yes |  |
| 258 | 258-259 | 0x00FCF0 | 568 | `SetPipeMode` |  |  | 2 | 2 | 9 | 13 |  | yes |  |
| 268 | 268-269 | 0x00DE80 | 388 | `SetLocalEngineThreads` |  |  | 3 | 0 | 1 | 4 |  | yes |  |
| 272 | 272-273 | 0x019C40 | 411 | `SetLeatherMode` |  |  | 2 | 0 | 12 | 14 |  | yes |  |
| 280 | 280-281 | 0x01AE40 | 507 | `CNS_SetZoneRestrictedPart` |  |  | 2 | 0 | 7 | 9 |  | yes |  |
| 298 | 298-299 | 0x013E30 | 417 | `SetSpecificSheetOrigin` |  |  | 2 | 0 | 1 | 3 |  | yes |  |
| 300 | 300-301 | 0x013FE0 | 417 | `SetSpecificSheetObjective` |  |  | 2 | 0 | 1 | 3 |  | yes |  |
| 304 | 304-305 | 0x00DE20 | 33 | `SetShearRepulseFromBorders` | `SetShearRepulseFromBorders` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 312 | 312-313 | 0x00DD60 | 36 | `CNS_SetOriginPackingMode` | `CNS_SetOriginPackingMode` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 316 | 316-317 | 0x010440 | 42 | `CNS_SetEvaluateIntermediateNestingsAsLast` | `CNS_SetEvaluateIntermediateNestingsAsLast` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 330 | 330-331 | 0x00DDF0 | 36 | `SetPartialShearMode` | `SetPartialShearMode` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 336 | 336-337 | 0x010470 | 42 | `SetReorganizeBiggestPartNearOrigin` | `SetReorganizeBiggestPartNearOrigin` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 338 | 338-339 | 0x0104A0 | 42 | `SetReorganizeLongestPartNearOrigin` | `SetReorganizeLongestPartNearOrigin` |  | 2 | 0 | 0 | 2 |  | yes |  |

## 3-getters  (33)

| ord | ordinals | RVA | size | 名称 | 跟踪标签 | C 别名 | 整数参 | 浮点参 | 栈参 | 估参 | 返回xmm0 | 恢复 | 证据 |
|---:|---|---|---:|---|---|---|---:|---:|---:|---:|:--:|:--:|---|
| 15 | 15-16 | 0x0107E0 | 155 | `GetComputationStatus` | `GetComputationStatus` |  | 2 | 0 | 0 | 2 |  | yes | // GetComputationStatus |
| 17 | 17-18 | 0x00B100 | 34 | `GetMultiplicity` | `GetMultiplicity` |  | 1 | 0 | 0 | 1 |  | yes |  |
| 19 | 19-20 | 0x00D460 | 688 | `GetNestedPart` | `GetNestedPart` | `CNS_GetNestedPart` | 4 | 1 | 10 | 15 | Y | yes | cns.cpp \| nested_part_number <= nested_parts.size() \| part_number <= order->parts.size() |
| 21 | 21-22 | 0x010F30 | 490 | `GetNesting` | `GetNesting` | `CNS_GetNesting` | 2 | 0 | 8 | 10 |  | yes | cns.cpp \| nesting_number < solution_aux.size() |
| 23 | 23-24 | 0x00B190 | 63 | `GetNumberOfNestedParts` | `GetNumberOfNestedParts` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 25 | 25-26 | 0x00B0C0 | 52 | `GetNumberOfNestings` | `GetNumberOfNestings` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 27 | 27-28 | 0x00C5E0 | 36 | `GetPartUserString` | `GetPartUserString` |  | 1 | 0 | 0 | 1 |  | yes |  |
| 29 | 29-30 | 0x00B510 | 43 | `GetPartWithBadGeometry` | `GetPartWithBadGeometry` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 31 | 31-32 | 0x00B600 | 332 | `GetSheet` | `GetSheet` | `CNS_GetSheet` | 2 | 0 | 29 | 31 |  | yes | number <= order->sheets.size() \| cns.cpp |
| 33 | 33-34 | 0x00B0A0 | 29 | `GetSolution` | `GetSolution` |  | 1 | 0 | 0 | 1 |  | yes |  |
| 55 | 55-56 | 0x00B020 | 52 | `GetPartUserStringEx` | `GetPartUserStringEx` |  | 3 | 0 | 0 | 3 |  | yes |  |
| 59 | 59-60 | 0x00C830 | 353 | `GetSheetUserString` |  |  | 1 | 0 | 10 | 11 |  | yes |  |
| 61 | 61-62 | 0x00B060 | 52 | `GetSheetUserStringEx` | `GetSheetUserStringEx` |  | 3 | 0 | 0 | 3 |  | yes |  |
| 88 | 88-89 | 0x00B490 | 31 | `GetBuildVersion` | `GetBuildVersion` |  | 0 | 0 | 0 | 0 |  | yes |  |
| 90 | 90-91 | 0x00B470 | 31 | `GetBuildDate` | `GetBuildDate` |  | 0 | 0 | 0 | 0 |  | yes |  |
| 92 | 92-93 | 0x00B450 | 31 | `GetMajorVersion` | `GetMajorVersion` |  | 0 | 0 | 0 | 0 |  | yes |  |
| 96 | 96-97 | 0x00B130 | 36 | `GetLength` | `GetLength` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 100 | 100-101 | 0x00B160 | 36 | `GetHeight` | `GetHeight` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 158 | 158-159 | 0x00D710 | 346 | `GetNumberOfCommonCuts` | `GetNumberOfCommonCuts` | `CNS_GetNumberOfCommonCuts` | 2 | 0 | 8 | 10 |  | yes | cns.cpp \| cns_nesting->nesting \| // GetNumberOfCommonCuts  |
| 160 | 160-161 | 0x00BA50 | 825 | `GetCommonCut` | `GetCommonCut` | `CNS_GetCommonCut` | 4 | 4 | 17 | 25 | Y | yes | cns.cpp \| nesting->nesting \| common_cut_number < evaluation.common_cut_segments.size() |
| 168 | 168-169 | 0x00B4B0 | 34 | `GetFillRatio` | `GetFillRatio` |  | 1 | 0 | 0 | 1 |  | yes |  |
| 170 | 170-171 | 0x00BD90 | 470 | `GetNestingDimensions` | `GetNestingDimensions` | `CNS_GetNestingDimensions` | 3 | 1 | 8 | 12 |  | yes | cns.cpp |
| 184 | 184-185 | 0x00D870 | 826 | `GetPartTorchInfos` | `GetPartTorchInfos` | `CNS_GetPartTorchInfos` | 4 | 1 | 31 | 36 | Y | yes | cns.cpp \| nesting->nesting \| part_index < nesting->nesting->nested_parts().size() \| part_index < nesting->nest |
| 192 | 192-193 | 0x00B4E0 | 38 | `GetNestingFillRatio` | `GetNestingFillRatio` |  | 1 | 0 | 0 | 1 |  | yes |  |
| 206 | 206-207 | 0x016E60 | 1727 | `GetNestedPartPartVariant` | `GetNestedPartPartVariant` |  | 3 | 0 | 35 | 38 |  | yes |  |
| 226 | 226-227 | 0x00C010 | 386 | `GetPCId` | `GetPCId` |  | 2 | 1 | 16 | 19 | Y | yes |  |
| 234 | 234-235 | 0x008AC0 | 939 | `GetNoFitMap` | `GetNoFitMap` |  | 3 | 2 | 30 | 35 | Y | yes | //GetNoFitMap |
| 248 | 248-249 | 0x018AF0 | 889 | `GetNumberOfMarks` |  |  | 3 | 0 | 9 | 12 |  | yes |  |
| 250 | 250-251 | 0x018E70 | 1312 | `GetMark` |  |  | 4 | 1 | 9 | 14 | Y | yes |  |
| 264 | 264-265 | 0x00FF30 | 271 | `GetNumberOfRows` |  |  | 1 | 0 | 1 | 2 |  | yes |  |
| 266 | 266-267 | 0x010040 | 384 | `GetRow` | `GetRow` | `CNS_GetRow` | 4 | 1 | 12 | 17 | Y | yes | cns.cpp \| row_number < row_intervals.size() |
| 324 | 324-325 | 0x00A620 | 934 | `GetNoFitPlacementMap` |  |  | 4 | 1 | 7 | 12 | Y | yes |  |
| 332 | 332-333 | 0x00B750 | 384 | `GetNestingBoundingBox` | `GetNestingBoundingBox` | `CNS_GetNestingBoundingBox` | 4 | 1 | 8 | 13 | Y | yes | cns.cpp \| min_x && min_y && max_x && max_y |

## 4-add (problem building)  (33)

| ord | ordinals | RVA | size | 名称 | 跟踪标签 | C 别名 | 整数参 | 浮点参 | 栈参 | 估参 | 返回xmm0 | 恢复 | 证据 |
|---:|---|---|---:|---|---|---|---:|---:|---:|---:|:--:|:--:|---|
| 1 | 1-2 | 0x016420 | 490 | `AddPolygonHoleToPart` | `// AddPolygonHoleToPart` |  | 3 | 2 | 6 | 11 | Y | yes | // AddPolygonHoleToPart |
| 3 | 3-4 | 0x0162B0 | 353 | `AddPolygonPart` | `// AddPolygonPart` |  | 4 | 1 | 2 | 7 | Y | yes | // AddPolygonPart |
| 5 | 5-6 | 0x015BF0 | 1717 | `AddSheet` |  |  | 4 | 2 | 5 | 11 |  | yes |  |
| 69 | 69-70 | 0x016B20 | 353 | `AddNonRectangularPolygonSheet` | `// AddNonRectangularPolygonSheet` |  | 4 | 1 | 2 | 7 | Y | yes | // AddNonRectangularPolygonSheet |
| 71 | 71-72 | 0x016970 | 426 | `AddPolygonDefectToSheet` | `// AddPolygonDefectToSheet` |  | 3 | 2 | 6 | 11 | Y | yes | // AddPolygonDefectToSheet |
| 94 | 94-95 | 0x010CE0 | 584 | `AddPartSpecificAuthorizations` | `AddPartSpecificAuthorizations` |  | 2 | 3 | 6 | 11 | Y | yes |  |
| 102 | 102-103 | 0x016610 | 419 | `AddExternalPolygonBoundaryToSheet` | `// AddExternalPolygonBoundaryToSheet` |  | 3 | 2 | 6 | 11 | Y | yes | // AddExternalPolygonBoundaryToSheet |
| 104 | 104-105 | 0x0167C0 | 426 | `AddExternalPolygonBoundaryToPart` | `// AddExternalPolygonBoundaryToPart` |  | 3 | 2 | 6 | 11 | Y | yes | // AddExternalPolygonBoundaryToPart |
| 110 | 110-111 | 0x014D10 | 1891 | `AddPart` |  |  | 4 | 3 | 7 | 14 |  | yes |  |
| 112 | 112-113 | 0x0132E0 | 176 | `AddHoleToPart` | `AddHoleToPart` |  | 3 | 2 | 0 | 5 | Y | yes |  |
| 114 | 114-115 | 0x013390 | 124 | `AddExternalBoundaryToPart` | `AddExternalBoundaryToPart` |  | 3 | 2 | 0 | 5 |  | yes |  |
| 116 | 116-117 | 0x0157A0 | 1098 | `AddNonRectangularSheet` |  |  | 4 | 2 | 6 | 12 | Y | yes |  |
| 118 | 118-119 | 0x014190 | 124 | `AddDefectToSheet` | `AddDefectToSheet` |  | 3 | 2 | 0 | 5 |  | yes |  |
| 120 | 120-121 | 0x014210 | 117 | `AddExternalBoundaryToSheet` | `AddExternalBoundaryToSheet` |  | 3 | 2 | 0 | 5 |  | yes |  |
| 124 | 124-125 | 0x014A60 | 678 | `AddOpenCuttingPathToPart` | `AddOpenCuttingPathToPart` |  | 4 | 1 | 28 | 33 | Y | yes |  |
| 130 | 130-131 | 0x015480 | 404 | `AddCircularPart` | `// AddCircularPart` |  | 2 | 4 | 1 | 7 | Y | yes | // AddCircularPart |
| 132 | 132-133 | 0x013800 | 581 | `AddCircularHoleToPart` | `// AddCircularHoleToPart` |  | 2 | 4 | 10 | 16 | Y | yes | // AddCircularHoleToPart |
| 134 | 134-135 | 0x015620 | 374 | `AddRectanglePart` | `// AddRectanglePart` |  | 2 | 3 | 2 | 7 | Y | yes | // AddRectanglePart |
| 136 | 136-137 | 0x013A50 | 569 | `AddRectangularHoleToPart` | `// AddRectangularHoleToPart` |  | 2 | 3 | 14 | 19 |  | yes | // AddRectangularHoleToPart |
| 138 | 138-139 | 0x014290 | 440 | `AddOptionalQuantityToPart` |  |  | 2 | 0 | 12 | 14 |  | yes |  |
| 194 | 194-195 | 0x018100 | 1955 | `AddPartVariantToPart` | `AddPartVariantToPart` |  | 3 | 3 | 8 | 14 |  | yes |  |
| 196 | 196-197 | 0x016D00 | 49 | `AddHoleToPartVariant` | `// AddHoleToPartVariant` |  | 3 | 0 | 0 | 3 |  | yes | // AddHoleToPartVariant |
| 218 | 218-219 | 0x011640 | 483 | `AddSuggestedPartsGrouping` | `AddSuggestedPartsGrouping` | `CNS_AddSuggestedPartsGrouping` | 1 | 0 | 8 | 9 |  | yes | cns.cpp |
| 220 | 220-221 | 0x00F7C0 | 1072 | `AddPartToSuggestedPartsGrouping` |  | `CNS_AddPartToSuggestedPartsGrouping` | 4 | 2 | 15 | 21 |  | yes | cns.cpp |
| 254 | 254-255 | 0x017520 | 3027 | `AddRotatedPartVariantToPart` | `AddRotatedPartVariantToPart` |  | 4 | 3 | 20 | 27 | Y | yes |  |
| 260 | 260-261 | 0x013410 | 512 | `AddCircularExternalBoundaryToPart` | `// AddCircularExternalBoundaryToPart` |  | 1 | 4 | 0 | 5 | Y | yes | // AddCircularExternalBoundaryToPart |
| 262 | 262-263 | 0x013610 | 486 | `AddRectangularExternalBoundaryToPart` | `// AddRectangularExternalBoundaryToPart` |  | 1 | 4 | 1 | 6 | Y | yes | // AddRectangularExternalBoundaryToPart |
| 274 | 274-275 | 0x019DE0 | 350 | `AddLeatherQualityZoneInPart` | `AddLeatherQualityZoneInPart` |  | 4 | 2 | 0 | 6 | Y | yes |  |
| 276 | 276-277 | 0x01A0A0 | 331 | `AddLeatherQualityZoneInSheet` | `AddLeatherQualityZoneInSheet` |  | 4 | 2 | 0 | 6 | Y | yes |  |
| 290 | 290-291 | 0x0101C0 | 127 | `AddToolPathToPart` | `AddToolPathToPart` |  | 3 | 2 | 0 | 5 |  | yes |  |
| 292 | 292-293 | 0x019F40 | 342 | `AddLeatherQualityZoneInPart` | `AddLeatherQualityZoneInPart` |  | 4 | 2 | 0 | 6 | Y | yes |  |
| 294 | 294-295 | 0x012C60 | 169 | `AddInflatedToolPathToPart` | `AddInflatedToolPathToPart` |  | 1 | 1 | 0 | 2 |  | yes |  |
| 296 | 296-297 | 0x010240 | 124 | `AddHoleInToolPath` | `AddHoleInToolPath` |  | 3 | 2 | 0 | 5 |  | yes |  |

## 5-CNS_ API extensions  (8)

| ord | ordinals | RVA | size | 名称 | 跟踪标签 | C 别名 | 整数参 | 浮点参 | 栈参 | 估参 | 返回xmm0 | 恢复 | 证据 |
|---:|---|---|---:|---|---|---|---:|---:|---:|---:|:--:|:--:|---|
| 198 | 198-199 | 0x016D40 | 49 | `CNS_AddExternalBoundaryToPartVariant` | `// CNS_AddExternalBoundaryToPartVariant` |  | 3 | 0 | 0 | 3 |  | yes | // CNS_AddExternalBoundaryToPartVariant |
| 200 | 200-201 | 0x016D80 | 96 | `CNS_AddOpenCuttingPathToPartVariant` | `// CNS_AddOpenCuttingPathToPartVariant` |  | 4 | 1 | 1 | 6 | Y | yes | // CNS_AddOpenCuttingPathToPartVariant |
| 204 | 204-205 | 0x016E20 | 63 | `CNS_AddPartVariantSpecificAuthorizations` | `// CNS_AddPartVariantSpecificAuthorizations` |  | 2 | 2 | 0 | 4 |  | yes | // CNS_AddPartVariantSpecificAuthorizations |
| 278 | 278-279 | 0x01AA90 | 944 | `CreateRestrictedZoneConstraint` |  |  | 2 | 0 | 1 | 3 |  | yes |  |
| 306 | 306-307 | 0x012F40 | 894 | `CNS_AddDefectFromNestedPart` | `CNS_AddDefectFromNestedPart` |  | 2 | 3 | 2 | 7 | Y | yes |  |
| 308 | 308-309 | 0x010B50 | 395 | `CNS_CreateAssemblyGroup` | `CNS_CreateAssemblyGroup` |  | 2 | 0 | 1 | 3 |  | yes |  |
| 310 | 310-311 | 0x011830 | 180 | `CNS_AddAssemblyGroupPart` | `CNS_AddAssemblyGroupPart` |  | 4 | 0 | 5 | 9 |  | yes |  |
| 314 | 314-315 | 0x012D10 | 552 | `CNS_AddOpenToolPathToPart` | `CNS_AddOpenToolPathToPart` |  | 4 | 2 | 18 | 24 |  | yes |  |

## 6-computation control  (15)

| ord | ordinals | RVA | size | 名称 | 跟踪标签 | C 别名 | 整数参 | 浮点参 | 栈参 | 估参 | 返回xmm0 | 恢复 | 证据 |
|---:|---|---|---:|---|---|---|---:|---:|---:|---:|:--:|:--:|---|
| 9 | 9-10 | 0x00B1D0 | 370 | `GenerateHtmlLaunchingOrderReport` | `GenerateHtmlLaunchingOrderReport` |  | 2 | 0 | 0 | 2 |  | yes | <h1> Problem contains invalid parts. </h1> \| <h1> Problem contains invalid sheets. </h1> |
| 13 | 13-14 | 0x00B8D0 | 378 | `GenerateLaunchingOrderProblem` | `GenerateLaunchingOrderProblem` |  | 2 | 0 | 2 | 4 |  | yes | source_version |
| 35 | 35-36 | 0x006100 | 3894 | `LaunchComputation` | `LaunchComputation` |  | 4 | 3 | 28 | 35 | Y | yes | c:\Temp\cns.pb.json \| // LaunchComputation |
| 47 | 47-48 | 0x0104D0 | 370 | `WaitComputationTermination` | `WaitComputationTermination` |  | 2 | 0 | 0 | 2 |  | yes | // WaitComputationTermination \| c:\Temp\computation_solution.html |
| 49 | 49-50 | 0x010650 | 386 | `WaitNextSolution` | `WaitNextSolution` |  | 2 | 0 | 65 | 67 |  | yes | c:\Temp\computation_solution.html \| // WaitNextSolution |
| 51 | 51-52 | 0x002AB0 | 2134 | `LaunchLocalComputation` | `// LaunchLocalComputation` |  | 2 | 2 | 3 | 7 | Y | yes | cns_force_cloud \| cns1.optalog.com;cns2.optalog.com \| c:\Temp\cns.pb.json \| // LaunchLocalComputation |
| 53 | 53-54 | 0x010880 | 155 | `CancelComputation` | `// CancelComputation` |  | 2 | 0 | 0 | 2 |  | yes | CancelComputation  \| // CancelComputation |
| 76 | 76-77 | 0x00D430 | 36 | `UnLockLaunchingOrder` | `UnLockLaunchingOrder` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 122 | 122-123 | 0x010920 | 155 | `TerminateComputation` | `// TerminateComputation` |  | 2 | 0 | 0 | 2 |  | yes | TerminateComputation  \| // TerminateComputation |
| 162 | 162-163 | 0x00E180 | 111 | `UnLockLaunchingOrderSntl` | `UnLockLaunchingOrderSntl` |  | 3 | 0 | 0 | 3 |  | yes |  |
| 164 | 164-165 | 0x003310 | 66 | `LaunchLimitedLocalComputation` | `LaunchLimitedLocalComputation` |  | 1 | 0 | 0 | 1 |  | yes |  |
| 216 | 216-217 | 0x003360 | 52 | `LaunchEstimateLocalComputation` | `// LaunchEstimateLocalComputation` |  | 1 | 1 | 0 | 2 |  | yes | // LaunchEstimateLocalComputation |
| 228 | 228-229 | 0x00E260 | 111 | `UnLockLaunchingOrderPCId` | `UnLockLaunchingOrderPCId` |  | 3 | 0 | 0 | 3 |  | yes |  |
| 252 | 252-253 | 0x00B540 | 177 | `AsyncCancelAllComputationsAndDeleteLaunchingOrder` | `AsyncCancelAllComputationsAndDeleteLaunchingOrder` |  | 3 | 0 | 2 | 5 |  | yes |  |
| 342 | 342-343 | 0x00E1F0 | 111 | `UnLockLaunchingOrderOxy` | `UnLockLaunchingOrderOxy` |  | 3 | 0 | 0 | 3 |  | yes |  |

## 8-report/export  (2)

| ord | ordinals | RVA | size | 名称 | 跟踪标签 | C 别名 | 整数参 | 浮点参 | 栈参 | 估参 | 返回xmm0 | 恢复 | 证据 |
|---:|---|---|---:|---|---|---|---:|---:|---:|---:|:--:|:--:|---|
| 11 | 11-12 | 0x00B350 | 247 | `GenerateHtmlSolutionReport` | `GenerateHtmlSolutionReport` |  | 2 | 0 | 0 | 2 |  | yes |  |
| 224 | 224-225 | 0x00BF70 | 148 | `GenerateDxfNesting` | `GenerateDxfNesting` |  | 2 | 0 | 0 | 2 |  | yes |  |

## 9-misc  (8)

| ord | ordinals | RVA | size | 名称 | 跟踪标签 | C 别名 | 整数参 | 浮点参 | 栈参 | 估参 | 返回xmm0 | 恢复 | 证据 |
|---:|---|---|---:|---|---|---|---:|---:|---:|---:|:--:|:--:|---|
| 230 | 230-231 | 0x009AF0 | 452 | `NewNoFitContext` | `// NewNoFitContext` |  | 2 | 0 | 1 | 3 |  | yes | // NewNoFitContext |
| 232 | 232-233 | 0x009CC0 | 568 | `DeleteNoFitContext` | `DeleteNoFitContext` |  | 1 | 0 | 0 | 1 |  | yes |  |
| 236 | 236-237 | 0x008A10 | 171 | `DeleteNoFitGeometry` | `DeleteNoFitGeometry` |  | 1 | 0 | 0 | 1 |  | yes |  |
| 284 | 284-285 | 0x01A210 | 1468 | `CNS_SheetAddRestrictedZone` |  |  | 4 | 1 | 9 | 14 |  | yes |  |
| 302 | 302-303 | 0x01A8F0 | 411 | `CNS_ForcePartOnBottomBorder` |  |  | 2 | 0 | 10 | 12 |  | yes |  |
| 318 | 318-319 | 0x009330 | 449 | `NewNoFitNesting` | `// NewNoFitNesting` |  | 2 | 0 | 1 | 3 |  | yes | // NewNoFitNesting |
| 322 | 322-323 | 0x009500 | 70 | `DeleteNoFitNesting` | `DeleteNoFitNesting` |  | 1 | 0 | 0 | 1 |  | yes |  |
| 334 | 334-335 | 0x00C610 | 43 | `ForcePartInsideHole` | `ForcePartInsideHole` |  | 1 | 0 | 0 | 1 |  | yes |  |

## Z-unnamed  (6)

| ord | ordinals | RVA | size | 名称 | 跟踪标签 | C 别名 | 整数参 | 浮点参 | 栈参 | 估参 | 返回xmm0 | 恢复 | 证据 |
|---:|---|---|---:|---|---|---|---:|---:|---:|---:|:--:|:--:|---|
| 208 | 208-209 | 0x016CB0 | 57 | `AddPartVariantUserString? (unnamed; assigns a C string to the std::string at Part+0x1B8)` |  |  | 2 | 0 | 0 | 2 |  | no |  |
| 210 | 210-211 | 0x016CF0 | 8 | `GetPartVariantUserString? (unnamed; returns the std::string data ptr at Part+0x1B8)` |  |  | 1 | 0 | 0 | 1 |  | no |  |
| 270 | 270-271 | 0x00AFE0 | 13 | `SetXXX(int) (unnamed; normalises arg to bool and stores global flag @0xB23350)` |  |  | 1 | 0 | 0 | 1 |  | no |  |
| 282 | 282-283 | 0x01A7D0 | 286 | `CNS_SheetAddRectangularRestrictedZone (unnamed; builds a 4-corner rect from 2 points, allocates 0x60 B = 12 doubles, forwards to CNS_SheetAddRestrictedZone)` |  |  | 4 | 4 | 0 | 8 | Y | no |  |
| 286 | 286-287 | 0x00B000 | 18 | `SetXXX(Order*, int, double) (unnamed; Order+0x100 = double, Order+0xF9 = flag)` |  |  | 1 | 1 | 0 | 2 |  | no |  |
| 288 | 288-289 | 0x00AFF0 | 10 | `SetXXX(Order*, int) (unnamed; Order+0xF8 = flag)` |  |  | 1 | 0 | 0 | 1 |  | no |  |

