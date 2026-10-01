import re, collections
PATH = r"D:\Nesting\nestfab\libcns_dump_64.dll"
data = open(PATH,'rb').read()

def strings(minlen=4, encoding='latin1'):
    out=[]
    cur=bytearray(); start=0
    for i,b in enumerate(data):
        if 32<=b<127:
            if not cur: start=i
            cur.append(b)
        else:
            if len(cur)>=minlen: out.append((start, cur.decode('latin1')))
            cur=bytearray()
    if len(cur)>=minlen: out.append((start,cur.decode('latin1')))
    return out
S = strings(4)
print("total strings:", len(S))

KEY = ['nest','minkowski','clipper','deepnest','svg','dxf','part','sheet','genetic','chromosome',
       'placement','rotation','polygon','offset','lp_','Clp','simplex','ga_','nfp','ifp','hull',
       'util','merge','collision','boundary','ga','config','json','liblcns','lcns','cns','dump']
print("\n=== interesting strings ===")
seen=set()
for off,s in S:
    low=s.lower()
    if any(k.lower() in low for k in KEY) and len(s)<160 and s not in seen:
        seen.add(s)
print("count:", len(seen))

# group: print the most telling
prio = [s for s in seen if any(k in s.lower() for k in ['minkowski','clipper','nfp','ifp','nest','deepnest','lcns','cns'])]
for s in sorted(prio)[:200]:
    print("  ", s)
