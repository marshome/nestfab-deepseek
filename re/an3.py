import sys, json, collections, struct
sys.path.insert(0, 'D:/Nesting/nestfab/re')
from an2 import *

def find_qword(val):
    """file offsets containing the 8-byte little-endian value"""
    b = struct.pack('<Q', val)
    out = []
    i = data.find(b)
    while i >= 0:
        out.append(i)
        i = data.find(b, i + 1)
    return out

def pair_search(k, vals):
    """find an adjacent qword pair (k, vals[i]) and return file offsets"""
    out = []
    for i in range(0, len(data) - 16, 8):
        if u64(i) == k:
            v = u64(i + 8)
            for want in vals:
                if norm(v) == want or v == want:
                    out.append((i, want, u64(i - 8) if i >= 8 else 0))
    return out
