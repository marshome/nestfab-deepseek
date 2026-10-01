"""Loader shim: lib.py's module docstring contains `D:\\Nesting\\...` (invalid \\N escape),
which Python 3.14 rejects.  Make the docstring raw, then register it as `lib`."""
import sys

_P = r"D:\Nesting\nestfab\re\lib.py"
_src = open(_P, encoding="utf-8").read()
_src = _src.replace('"""', 'r"""', 1)
_mod = type(sys)("lib")
_mod.__file__ = _P
sys.modules["lib"] = _mod
exec(compile(_src, _P, "exec"), _mod.__dict__)
