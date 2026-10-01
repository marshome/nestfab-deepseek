import sys, re
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *

keys = set(sys.argv[1:])
lines = [''.join(c if 32 <= ord(c) < 127 else '.' for c in L)
         for L in open(REDIR + r'\feat\out_dis.txt', encoding='utf-8', errors='replace')]
out = []
for i, L in enumerate(lines):
    m = re.search(r'STR:"([^"]*)"', L)
    if m and m.group(1) in keys:
        out.append('--- ' + m.group(1) + '   @' + L.split()[0])
        for j in range(i + 1, min(i + 11, len(lines))):
            s = lines[j].strip()
            if 'CALL' in s or 'mov' in s:
                out.append('    ' + s[:120])
open(REDIR + r'\feat\out_kc.txt', 'w', newline='\n').write('\n'.join(out))
print('\n'.join(out))
