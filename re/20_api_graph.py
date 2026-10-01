import sys, json, struct, collections
sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *
from capstone.x86 import *

rows = json.load(open(r"D:\Nesting\nestfab\re\exports_table.json"))
name_of = {r['rva']: (r['name'] or 'sub_%X' % r['rva']) for r in rows}

print("="*100); print("EXPORT -> EXPORT CALL GRAPH (API layering)"); print("="*100)
for r in sorted(rows, key=lambda r: r['ords'][0]):
    if r['callees_exp']:
        print("  %-52s -> %s" % (name_of[r['rva']],
              ', '.join(name_of.get(c, '%08X'%c) for c in r['callees_exp'])))

print("\n" + "="*100); print("EXPORTS GROUPED BY SOURCE FILE (assert strings)"); print("="*100)
g = collections.defaultdict(list)
for r in rows:
    g[r['src'] or '(unknown)'].append(name_of[r['rva']])
for k in sorted(g, key=lambda k: -len(g[k])):
    print("\n  [%s]  %d functions" % (k, len(g[k])))
    print("     " + ', '.join(sorted(g[k])))

print("\n" + "="*100); print("TINY EXPORTS (<80 bytes) — likely inline accessors/wrappers"); print("="*100)
for r in sorted(rows, key=lambda r: r['size']):
    if r['size'] < 80:
        print("  %-52s %08X size=%-4d ord=%s  insn: %s" % (name_of[r['rva']], r['rva'], r['size'],
              ','.join(map(str,r['ords'])),
              ' ; '.join('%s %s'%(i.mnemonic,i.op_str) for i in list(disasm(r['rva'], count=4)))))
