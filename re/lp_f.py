import sys; sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
import pickle, collections
X = pickle.load(open(REDIR + r'\xref.pkl','rb'))
print(type(X), len(X))
if isinstance(X, dict):
    ks=list(X)[:5]
    for k in ks: print(hex(k) if isinstance(k,int) else k, type(X[k]), str(X[k])[:200])
