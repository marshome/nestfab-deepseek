import sys, json, csv, collections, re
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *

rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json"))

FALLBACK = {
 0x16CB0: 'AddPartVariantUserString? (unnamed; assigns a C string to the std::string at Part+0x1B8)',
 0x16CF0: 'GetPartVariantUserString? (unnamed; returns the std::string data ptr at Part+0x1B8)',
 0xAFE0 : 'SetXXX(int) (unnamed; normalises arg to bool and stores global flag @0xB23350)',
 0x1A7D0: 'CNS_SheetAddRectangularRestrictedZone (unnamed; builds a 4-corner rect from 2 points, allocates 0x60 B = 12 doubles, forwards to CNS_SheetAddRestrictedZone)',
 0xB000 : 'SetXXX(Order*, int, double) (unnamed; Order+0x100 = double, Order+0xF9 = flag)',
 0xAFF0 : 'SetXXX(Order*, int) (unnamed; Order+0xF8 = flag)',
}
ALIAS = {
 'GetSheet':'CNS_GetSheet','GetNesting':'CNS_GetNesting','GetNestedPart':'CNS_GetNestedPart',
 'GetCommonCut':'CNS_GetCommonCut','GetNumberOfCommonCuts':'CNS_GetNumberOfCommonCuts',
 'GetNestingBoundingBox':'CNS_GetNestingBoundingBox','GetNestingDimensions':'CNS_GetNestingDimensions',
 'GetPartTorchInfos':'CNS_GetPartTorchInfos','GetRow':'CNS_GetRow','SetInterpartGap':'CNS_SetInterpartGap',
 'NoFitGetPoint':'CNS_NoFitGetPoint','NoFitGetNumberOfInternalHoles':'CNS_NoFitGetNumberOfHoles',
 'NoFitContext':'CNS_NoFitContext','AddSuggestedPartsGrouping':'CNS_AddSuggestedPartsGrouping',
 'AddPartToSuggestedPartsGrouping':'CNS_AddPartToSuggestedPartsGrouping',
 'AddExternalBoundaryToPartVariant':'CNS_AddExternalBoundaryToPartVariant',
}
# families for grouping
def family(n):
    if not n: return 'Z-unnamed'
    if n in ('NewLaunchingOrder','DeleteLaunchingOrder'): return '0-lifecycle'
    if n.startswith('NoFit') or n.startswith('CNS_NoFit'): return '1-NoFit (NFP/geometry)'
    if n.startswith('Set') or n.startswith('CNS_Set'): return '2-setters'
    if n.startswith('Get'): return '3-getters'
    if n.startswith('Add'): return '4-add (problem building)'
    if n.startswith('CNS_Add') or n.startswith('CNS_Create'): return '5-CNS_ API extensions'
    if n.startswith('Create'): return '5-CNS_ API extensions'
    if 'Launch' in n or 'Wait' in n or 'Cancel' in n or 'Terminate' in n or 'Async' in n: return '6-computation control'
    if 'UnLock' in n or 'PCId' in n: return '7-licensing'
    if 'Generate' in n: return '8-report/export'
    return '9-misc'

out=[]
for r in rows:
    nm = r['name'] or FALLBACK.get(r['rva'],'?')
    named = bool(r['name'])
    out.append(dict(
        ordinals='%d-%d' % (r['ords'][0], r['ords'][-1]) if len(r['ords'])>1 else str(r['ords'][0]),
        ordinal_first=r['ords'][0], rva='0x%06X'%r['rva'], size=r['size'],
        name=nm, c_alias=ALIAS.get(r['name'],''), recovered=('yes' if named else 'no'),
        family=family(r['name']), src=r['src'] or '',
        label=(r.get('labels') or [''])[0],
        args_regs=len(r['int_regs']), args_xmm=len(r['xmm']), args_stack=r['stack_args'],
        arity_est=r['arity'], ret_xmm=r['ret_xmm'], calls=r['calls'],
        evidence=' | '.join((r['sem'] or [])[:4]),
    ))
out.sort(key=lambda d: d['ordinal_first'])
with open(r"D:\Nesting\nestfab\re\exports_table.csv","w",newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print("wrote exports_table.csv  rows=%d" % len(out))

# markdown table grouped by family
by=collections.defaultdict(list)
for d in out: by[d['family']].append(d)
with open(r"D:\Nesting\nestfab\re\exports_table.md","w",encoding='utf-8') as f:
    f.write("# liblcns.dll 导出函数表 (168 个唯一函数, 168x2=336 个序号)\n\n")
    f.write("VM 模式: 无名字导出 (NumberOfNames=0), 以下名字由 `dbg::symlog` 作用域跟踪器写入的 `__func__` 字面量恢复。\n\n")
    for fam in sorted(by):
        f.write("## %s  (%d)\n\n" % (fam, len(by[fam])))
        f.write("| ord | ordinals | RVA | size | 名称 | 跟踪标签 | C 别名 | 整数参 | 浮点参 | 栈参 | 估参 | 返回xmm0 | 恢复 | 证据 |\n")
        f.write("|---:|---|---|---:|---|---|---|---:|---:|---:|---:|:--:|:--:|---|\n")
        for d in sorted(by[fam], key=lambda d:d['ordinal_first']):
            f.write("| %d | %s | %s | %d | `%s` | %s | %s | %d | %d | %d | %d | %s | %s | %s |\n" % (
                d['ordinal_first'], d['ordinals'], d['rva'], d['size'], d['name'],
                ('`%s`'%d['label']) if d['label'] else '',
                ('`%s`'%d['c_alias']) if d['c_alias'] else '', d['args_regs'], d['args_xmm'],
                d['args_stack'], d['arity_est'], 'Y' if d['ret_xmm'] else '', d['recovered'],
                (d['evidence'][:110].replace('|','\\|'))))
        f.write("\n")
print("wrote exports_table.md")
print("\nfamily counts:")
for k in sorted(by): print("   %-32s %d" % (k, len(by[k])))
