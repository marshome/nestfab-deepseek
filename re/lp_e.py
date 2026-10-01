import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
for r in range(0x9d9d00, 0x9d9dc0, 0x10):
    print(hex(r), repr(data[rva2off(r):rva2off(r)+0x10]))
print('---- 9C2DF0 area')
for r in range(0x9c2df0, 0x9c2e60, 0x10):
    print(hex(r), repr(data[rva2off(r):rva2off(r)+0x10]))
print('---- 7C9A10')
print(hex(0x7c9a10), repr(STRS.get(0x7c9a10)), repr(data[rva2off(0x7c9a10):rva2off(0x7c9a10)+48]))
print('---- 4D96D0')
print(repr(data[rva2off(0x4d96d0):rva2off(0x4d96d0)+48]))
