#!/usr/bin/env bash
# Build the COIN-OR trio that libcns_dump_64.dll links, with CLion's MinGW GCC.
#
# Fixes learned from the first attempt:
#   * git clone timestamps make make(1) believe configure/Makefile.in are stale, so it tries to
#     re-run autotools -- which is absent, and whose invocation breaks on the space in
#     "C:/Program Files/...". Fix: touch every generated file, and point the autotools variables
#     at no-ops.
#   * Osi/Clp must be told where CoinUtils is: --with-coinutils-incdir / --with-coinutils-lib.
set -u
TP=/d/Nesting/nestfab/third_party
export PATH="$TP/_shim:/c/Program Files/JetBrains/CLion 2025.3.3/bin/mingw/bin:$PATH"
export CFLAGS="-O2"
export CXXFLAGS="-O2"
# belt and braces: never let make try to regenerate the build system
export AUTOCONF=: AUTOMAKE=: ACLOCAL=: AUTOHEADER=: AUTORECONF=: LIBTOOLIZE=: AUTOHEADER=:
# ROOT CAUSE of "make: Error 127" (two layers):
#   1. configure recorded the shell as "C:/Program Files/Git/usr/bin/sh.exe";
#   2. even with SHELL=/bin/sh in the makefile, mingw32-make RESOLVES /bin/sh to that same spaced
#      Windows path, and the recipes use $(SHELL) unquoted -> "C:/Program: No such file".
# Fix: hand make an 8.3 short path, which contains no spaces.
export CONFIG_SHELL=/bin/sh
export SHELL="C:/PROGRA~1/Git/usr/bin/sh.exe"

freeze_generated () {
  local srcdir="$1"
  # Timestamps must respect the automake dependency order, oldest to newest:
  #   *.am/*.ac/*.m4/*.inc  <  aclocal.m4  <  configure  <  Makefile.in/config.h.in  <  (generated in build dir)
  # Getting this wrong is what made make re-run configure (and libtool's probing then broke).
  find "$srcdir" -type f -exec touch -d '2020-01-01 00:00' {} + 2>/dev/null
  [ -f "$srcdir/aclocal.m4" ] && touch -d '2021-01-01 00:00' "$srcdir/aclocal.m4"
  find "$srcdir" -name configure -type f -exec touch -d '2022-01-01 00:00' {} + 2>/dev/null
  find "$srcdir" -name 'Makefile.in' -type f -exec touch -d '2023-01-01 00:00' {} + 2>/dev/null
  find "$srcdir" -name 'config.h.in' -type f -exec touch -d '2023-01-01 00:00' {} + 2>/dev/null
}

build_one () {
  local name="$1" srcdir="$2" bdir="$3"; shift 3
  echo
  echo "=== $name ==="
  freeze_generated "$srcdir"
  rm -rf "$bdir"; mkdir -p "$bdir"; cd "$bdir" || return 1
  "$srcdir/configure" --prefix="$TP/install" \
      --host=x86_64-w64-mingw32 --build=x86_64-pc-mingw32 \
      --disable-shared --enable-static \
      --without-blas --without-lapack \
      --with-coinutils-incdir="$TP/install/include" \
      --with-coinutils-lib="-L$TP/install/lib -lCoinUtils" \
      --with-osi-incdir="$TP/install/include" \
      --with-osi-lib="-L$TP/install/lib -lOsi -lOsiClp" \
      SHELL="C:/PROGRA~1/Git/usr/bin/sh.exe" "$@" > cfg.log 2>&1
  local rc=$?
  echo "  configure exit=$rc"
  grep -iE "^configure: error|error:" cfg.log | head -n 4
  tail -n 2 cfg.log
  [ $rc -ne 0 ] && return 1

  # -o (--old-file) is the designed way to stop make from regenerating the build system: the
  # generated makefile wants to re-run config.status/configure, and that re-run is what broke on
  # the spaced shell path / on configure's own eval.
  make -o Makefile -o makefile -o config.status -j8 > make.log 2>&1
  rc=$?
  echo "  make exit=$rc"
  grep -iE "error:|Error [0-9]+" make.log | head -n 6
  [ $rc -ne 0 ] && return 1

  make -o Makefile -o makefile -o config.status install > install.log 2>&1
  echo "  install exit=$?"
  ls -1 "$TP/install/lib" 2>/dev/null | head -n 8
  return 0
}

build_one CoinUtils "$TP/src/coinutils-2.10" "$TP/build/cu"
build_one Osi       "$TP/src/osi-0.107"      "$TP/build/osi"
build_one Clp       "$TP/src/clp-1.15"       "$TP/build/clp"

echo
echo "=== install tree ==="
find "$TP/install" -name '*.a' 2>/dev/null | sed "s|$TP/||"
echo "  headers: $(find "$TP/install" -name '*.h' 2>/dev/null | wc -l)"
