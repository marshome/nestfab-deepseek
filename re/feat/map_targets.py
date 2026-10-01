import json, sys
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *

TARGETS = """SetCommonCutMode SetPartCommonCutMode SetCommonCutObjective SetCommonCutCuttingPreference
SetCommonCutSafetyPreference SetCommonCutAuthorizations CNS_GetCommonCut CNS_GetNumberOfCommonCuts
SetMultiTorchMode SetMultiTorchCuttingPreference SetMultiTorchObjective SetDetailedMultiTorchObjective
CNS_GetPartTorchInfos SetShearMode SetPartialShearMode SetShearGap SetShearRepulseFromBorders
SetPipeMode SetRowMode GetNumberOfRows GetRow CNS_GetRow SetLeatherMode AddLeatherQualityZoneInPart
AddLeatherQualityZoneInSheet SetMarkMode GetNumberOfMarks GetMark AddNonRectangularSheet
AddDefectToSheet AddPolygonDefectToSheet CNS_AddDefectFromNestedPart SetDefectGap AddToolPathToPart
AddHoleInToolPath AddInflatedToolPathToPart CNS_AddOpenToolPathToPart AddOpenCuttingPathToPart
CNS_AddToolPathDefectToSheet CNS_AddExternalToolPathBoundaryToSheet CNS_SheetAddRestrictedZone
CNS_SetZoneRestrictedPart CNS_ForcePartOnBottomBorder CreateRestrictedZoneConstraint
CNS_CreateAssemblyGroup CNS_AddAssemblyGroupPart AddSuggestedPartsGrouping
AddPartToSuggestedPartsGrouping MakeClusterFromSuggestedPartsGrouping SetIncompatibleSheet
ForcePartInsideHole ForcePartOutsideHole SetOffcutEvaluation SetObjective SetSheetPrice SetSheetPriority
GetFillRatio GetNestingFillRatio SetReorganizeBiggestPartNearOrigin SetReorganizeLongestPartNearOrigin
SetSpecificSheetOrigin SetSpecificSheetObjective SetAutomaticStop SetFillLastNestingStrategy
SetExtraParameters GenerateDxfNesting GenerateHtmlSolutionReport GenerateHtmlLaunchingOrderReport
GenerateLaunchingOrderProblem GetSolution GetNesting GetNestingDimensions GetNestingBoundingBox
GetNestedPart GetNestedPartPartVariant GetPartWithBadGeometry NewLaunchingOrder DeleteLaunchingOrder
SetSheetGrainDirection SetExtraGapOnPart SetSheetGaps SetExtraGapOnPart AddPart AddSheet
SetPartPriority SetOrigin SetInterpartGap GetSheet GetNumberOfNestedParts GetMultiplicity GetLength
GetHeight SetSheetUserString GetSheetUserString SetPartUserString GetPartUserString
SetPartAuthorizations AddPartSpecificAuthorizations SetPartSpecificCommonCut CNS_SetNoOrientationMixOnPart
CNS_SetFloatingMode CNS_SetOriginPackingMode CNS_SetMultiplicityPreference CNS_SetNoMixPreference
CNS_SetNoSheetMixPreference CNS_SetEvaluateIntermediateNestingsAsLast GetNumberOfNestings
GetPartUserStringEx GetSheetUserStringEx AddPartVariantToPart AddRotatedPartVariantToPart
AddHoleToPart AddExternalBoundaryToPart AddExternalBoundaryToSheet AddCircularPart AddRectanglePart
AddPolygonPart AddOptionalQuantityToPart GetPartWithBadGeometry CNS_GetSheet CNS_GetNestedPart""".split()

d = json.load(open(REDIR + r'\exports_named.json'))
ALL = {}
for e in d:
    ALL[e['rva']] = e
BY = {}
for e in d:
    if e['name']:
        BY.setdefault(e['name'].rstrip('?'), []).append(e)

# index by any string that looks like an export name (CNS_ prefix or known)
bystr = {}
for r, s in STRS.items():
    if r >= 0x9AC000 and s and (s.startswith('CNS_') or s[0].isupper()) and ' ' not in s and 4 < len(s) < 60:
        bystr.setdefault(s, []).append(r)

lines = []
for n in TARGETS:
    es = BY.get(n)
    if not es and n in bystr:
        # find export whose strings contain it
        es = [e for e in d if n in (e['strings'] or []) or n in ''.join(e['strings'])]
    if not es:
        lines.append('%s\tNOTFOUND' % n)
        continue
    for e in es:
        lines.append('%s\t0x%X\t%d\t%s\t%s' % (n, e['rva'], e['size'],
                                               ','.join(map(str, e['ords'])), ' | '.join(e['strings'][:10])))
open(REDIR + r'\feat\targets.tsv', 'w', newline='\n').write('\n'.join(lines))
print('\n'.join(lines))
