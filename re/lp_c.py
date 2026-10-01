import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import pickle, collections
P = load_prof()
v = P[4096]
for k in ['size','nins','calls','ind','fpu','own_plain','own_comm','name']:
    print(k, repr(v[k])[:200])
print('strings', repr(v['strings'])[:300])
print('callees', repr(v['callees'])[:300])
print('callers', repr(v['callers'])[:300])
print('data_refs', repr(v['data_refs'])[:300])
