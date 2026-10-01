import sys, io, contextlib, importlib.util
sys.path.insert(0, r'D:\Nesting\nestfab\re')
from lib import *
spec = importlib.util.spec_from_file_location('dd', REDIR + r'\feat\d.py')
dd = importlib.util.module_from_spec(spec)
sys.modules['dd'] = dd
spec.loader.exec_module(dd)

txt = []
for a in sys.argv[1:]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        dd.show(int(a, 0))
    txt.append(buf.getvalue())
open(REDIR + r'\feat\out_dis.txt', 'w').write('\n'.join(txt))
print('wrote', sum(len(t) for t in txt))
