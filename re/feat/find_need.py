import json, sys
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *

NEED = """CNS_GetCommonCut CNS_GetNumberOfCommonCuts CNS_GetPartTorchInfos GetRow CNS_GetRow
CNS_AddToolPathDefectToSheet CNS_AddExternalToolPathBoundaryToSheet AddSuggestedPartsGrouping
AddPartToSuggestedPartsGrouping MakeClusterFromSuggestedPartsGrouping ForcePartOutsideHole
GenerateLaunchingOrderProblem GetNesting GetNestingDimensions GetNestingBoundingBox GetNestedPart
UnSerializeSolution DrawSVG common_cut_segments multitorch_infos row_intervals
ComputeSheetGeometryRowMode GetCommonCutProperties GetMultitorchProperties
border_property.hpp GetLayerRestrictedZonePart GetLayerRestrictedZoneSheet GetLayerLeatherPart
GetLayerLeatherSheet SetSheetGrainDirection SetIncompatibleSheet SetExtraGapOnPart BadCommonCutGaps
cns_solution.css common_cut_safety_preference all_settings m_infos""".split()

d = json.load(open(REDIR + r'\exports_named.json'))
lines = []
for t in NEED:
    hits = [e for e in d if t in ''.join(e['strings']) or (e['name'] and t in e['name'])]
    if not hits:
        # search global strings
        rs = [(r, s) for r, s in STRS.items() if t in s]
        lines.append('%-42s EXPORT-NOHIT  strRVAs=%s' % (t, ['0x%X' % r for r, s in rs[:12]]))
    else:
        for e in hits[:6]:
            lines.append('%-42s rva=%7d size=%6d name=%-40s strings=%s' % (
                t, e['rva'], e['size'], e['name'], '; '.join(e['strings'][:6])))
open(REDIR + r'\feat\out_need.txt', 'w').write('\n'.join(lines))
print('\n'.join(lines))
