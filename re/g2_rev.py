import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
from g1_names import NAMES
import re

P = load_prof()

# build string->funcs reverse index using data_refs (which include rip targets)
def build_rev():
    rev = {}
    for rva, v in P.items():
        for t in v.get('data_refs', []):
            rev.setdefault(t, []).append(rva)
    return rev
REV = build_rev()

def refs(stro):
    return REV.get(stro, [])

def show(stro, label=None):
    if stro not in STRS:
        print('no string at', hex(stro)); return
    print('=== string', hex(stro), repr(STRS[stro]))
    for f in sorted(refs(stro)):
        print('    ', hex(f), P[f]['size'], P[f]['nins'], NAMES.get(f) or P[f].get('name'))
