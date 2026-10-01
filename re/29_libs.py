import sys, re, collections, json
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *

out = []
def w(*a): out.append(' '.join(str(x) for x in a))

out.append("="*90); out.append("LIBRARY / GEOMETRY FINGERPRINTS"); out.append("="*90)
pats = {
 'ClipperLib':        rb'Clipper|ClipperBase|ClipperOffset|JoinType|PolyTree|IntPoint|SimplifyPolygon',
 'clipper-lower':     rb'clipper',
 'Minkowski/NFP':     rb'[Mm]inkowski|NFP|nfp|NoFit|no_fit|noFit',
 'boost::geometry':   rb'boost::geometry|bg::',
 'anglesort/atan2':   rb'atan2|sort_by_angle|angle_sort',
 'Eigen':             rb'Eigen',
 'CGAL':              rb'CGAL',
 'Clipper-ish names': rb'Polygon|Ring|RingOf|Contour|Vertex|Edge|Segment|BoundingBox',
 'CGAL/gmp':          rb'gmp|mpfr',
 'Clp/Coin':          rb'ClpSimplex|ClpModel|CoinLp|CoinMessageHandler|OsiClp|CoinPackedMatrix|CoinError',
 'LSQR':              rb'lsqr|LSQR|istop|conlim',
 'GA/genetic':        rb'genetic|chromosome|population|mutation|crossover|fitness',
 'beams':             rb'beam|Beam',
 'hull':              rb'hull|Hull',
}
for k,p in pats.items():
    hits = [m.start() for m in re.finditer(p, data)]
    w("%-20s %7d hits" % (k, len(hits)))

out.append("")
out.append("="*90); out.append("STRINGS MATCHING geometry keywords (unique, len>=5)"); out.append("="*90)
kw = re.compile(r'[Mm]inkowski|NFP|NoFit|no_fit|hull|Hull|clip|Clip|offset|Offset|inflate|Inflate|atan2|angle|Angle|ring|Ring|polygon|Polygon|contour|Contour', re.I)
seen=set()
for r,s in sorted(STRS.items()):
    if 5 <= len(s) <= 90 and kw.search(s) and not s.startswith('_Z') and 'basic_string' not in s:
        seen.add(s)
w("count: %d" % len(seen))
for s in sorted(seen)[:400]:
    w("   ", s)

out.append("")
out.append("="*90); out.append("ALL custom RTTI class names (non-boost/std/CryptoPP/Coin/Json)"); out.append("="*90)
vt = json.load(open(r"D:\Nesting\nestfab\re\vtables.json"))
EX = ('boost::','std::','__gnu_cxx','CryptoPP','Json','Coin','Clp','CoinUtils','_')
for k,v in sorted(vt.items(), key=lambda kv: kv[1]['demangled']):
    d = v['demangled']
    if not d.startswith(EX):
        w("   %-64s vt=%s slots=%d" % (d, v['vtable_rva'] and hex(v['vtable_rva']), len(v['slots'])))
open(r"D:\Nesting\nestfab\re\out_29.txt","w",encoding='utf-8').write('\n'.join(out))
print("wrote out_29.txt  lines=%d" % len(out))
