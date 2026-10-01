import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from g1_names import NAMES
from g5_inline import inline_strings
from g3_dis import P


def short(rva):
    v = P.get(rva, {})
    n = NAMES.get(rva) or v.get('name')
    return '%s@%x(%d)' % (n or '?', rva, v.get('size', 0))


def info(rva, deep=1):
    v = P.get(rva)
    if not v:
        print('no prof for', hex(rva)); return
    print('=== %s  size=%d nins=%d ind=%d' % (short(rva), v['size'], v['nins'], v['ind']))
    print('  strings:', [s for _, s in inline_strings(rva) if len(s) >= 5][:20])
    for _ in range(deep):
        print('  callers:')
        for c in v['callers']:
            print('     ', short(c))
        print('  callees:')
        for c in sorted(set(v['callees'])):
            print('     ', short(c))
