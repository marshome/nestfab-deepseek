import re, struct, collections
PATH = r"D:\Nesting\nestfab\libcns_dump_64.dll"
data = open(PATH,'rb').read()

# collect all C strings with offsets
strs=[]
cur=bytearray(); start=0
for i,b in enumerate(data):
    if 32<=b<127:
        if not cur: start=i
        cur.append(b)
    else:
        if len(cur)>=1: strs.append((start,bytes(cur).decode('latin1')))
        cur=bytearray()

cns_exact = [(o,s) for o,s in strs if re.fullmatch(r'CNS_[A-Za-z0-9_]+', s)]
cns_cmt   = [(o,s) for o,s in strs if re.fullmatch(r'//\s*CNS_[A-Za-z0-9_]+', s)]
print("exact 'CNS_xxx' strings      :", len(cns_exact))
print("'// CNS_xxx' comment strings :", len(cns_cmt))

uniq_e = sorted(set(s for _,s in cns_exact))
uniq_c = sorted(set(s[2:].strip() for _,s in cns_cmt))
print("unique exact :", len(uniq_e), " unique comments :", len(uniq_c))
print("comments also present as exact:", len(set(uniq_c) & set(uniq_e)))
print("\nAll comment-style names (%d):" % len(uniq_c))
for i,s in enumerate(uniq_c): print("  %3d %s" % (i+1,s))
