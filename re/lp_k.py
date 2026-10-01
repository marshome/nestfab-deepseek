import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import struct, re
# search whole file for the 8-byte little endian absolute VA (IB + rva) of interesting vtables, and the 4-byte rva
for rva in (0xa3ada0,0xa3aed0,0xa3b0b0,0xa3b0f0,0xa3b130,0xa3b170,0xa3b1b0,0xa3b1e0,0xa3b270):
    va = rva + IB
    p8 = struct.pack('<Q', va)
    p4 = struct.pack('<I', rva)
    o8 = [m.start() for m in re.finditer(re.escape(p8), data)]
    print('%08X va=%016X  8byte hits=%d  rva4=%d' % (rva, va, len(o8), len([m.start() for m in re.finditer(re.escape(p4), data)])))
    for o in o8[:8]:
        print('     off', hex(o), 'rva', hex(off2rva(o)))
# how about the load of the vtable as a MOV immediate? look for 'movabs rax, imm64'
print('--- e.g. any refs to 0xa3b0b0 area at all')
cnt=0
for off in range(0, len(data)-8):
    v = struct.unpack_from('<Q', data, off)[0]
    if 0xa3b000 <= v <= 0xa3b300:
        cnt+=1
        if cnt<40: print('  stored qword @', hex(off), 'rva', hex(off2rva(off)), '=', hex(v))
print('total', cnt)
