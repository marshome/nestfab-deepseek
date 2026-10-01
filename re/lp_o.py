import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import struct
for r in (0x656310, 0x656340, 0x7c4c70, 0x7ca0d0, 0x6792c0, 0x679d00):
    o = rva2off(r)
    print(hex(r), data[o:o+64].hex())
