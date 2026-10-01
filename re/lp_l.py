import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
print('sections:')
for n,va,vs,pr,rs,ch in SEC:
    print('  %-8s va=%08X vs=%08X pr=%08X rs=%08X ch=%08X' % (n,va,vs,pr,rs,ch))
print('PE header size of image', hex(pe.OPTIONAL_HEADER.SizeOfImage))
for r in (0xa3b0a0, 0xa3b0b0, 0xa3b1b0, 0xa3b270, 0xa3b278):
    o = rva2off(r)
    print(hex(r), 'off', hex(o) if o is not None else None, repr(data[o:o+32]) if o is not None else '')
