import sys, struct
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
for a in sys.argv[1:]:
    r = int(a, 0)
    o = rva2off(r)
    q = struct.unpack_from('<Q', data, o)[0]
    d = struct.unpack_from('<d', data, o)[0]
    f = struct.unpack_from('<f', data, o)[0]
    i = struct.unpack_from('<i', data, o)[0]
    print('0x%X  q=0x%016X  double=%r  float=%r  int=%d' % (r, q, d, f, i))
