#!/usr/bin/env bash
# Generate the authentic config headers for Clp 1.15.3 (the exact version the dump proves).
# Only configure/config.status are run -- never make, whose regeneration rules are what broke before.
set -u
TP=/d/Nesting/nestfab/third_party
export PATH="$TP/_shim:/c/Program Files/JetBrains/CLion 2025.3.3/bin/mingw/bin:$PATH"
export SHELL="C:/PROGRA~1/Git/usr/bin/sh.exe"
export CONFIG_SHELL=/bin/sh
export AUTOCONF=: AUTOMAKE=: ACLOCAL=: AUTOHEADER=: AUTORECONF=: LIBTOOLIZE=:

SRC=$TP/src/clp-1.15.3
B=$TP/build/clp153
rm -rf "$B"; mkdir -p "$B"; cd "$B" || exit 1

# freeze timestamps in automake dependency order so make never wants to regenerate anything
find "$SRC" -type f -exec touch -d '2020-01-01 00:00' {} + 2>/dev/null
[ -f "$SRC/aclocal.m4" ] && touch -d '2021-01-01 00:00' "$SRC/aclocal.m4"
find "$SRC" -name configure -type f -exec touch -d '2022-01-01 00:00' {} + 2>/dev/null
find "$SRC" -name 'Makefile.in' -type f -exec touch -d '2023-01-01 00:00' {} + 2>/dev/null
find "$SRC" -name 'config.h.in' -type f -exec touch -d '2023-01-01 00:00' {} + 2>/dev/null

echo "=== configure Clp 1.15.3 ==="
"$SRC/configure" --prefix="$TP/install" --host=x86_64-w64-mingw32 --build=x86_64-pc-mingw32 \
    --disable-shared --enable-static --without-blas --without-lapack \
    --with-coinutils-incdir="$TP/src/coinutils-2.10/CoinUtils/src" \
    --with-coinutils-lib="-L$TP/build-cmake -lcoinutils" \
    SHELL="C:/PROGRA~1/Git/usr/bin/sh.exe" CFLAGS=-O2 CXXFLAGS=-O2 > cfg.log 2>&1
echo "  configure exit=$?"
tail -n 2 cfg.log

echo "=== generated config headers ==="
find "$B" -name 'config*.h' | sed "s|$B/||"
for f in $(find "$B" -name 'config_clp.h'); do
  cp "$f" "$TP/gen/clp/config_clp.h"
  echo "  copied $(basename $f) -> gen/clp/"
  grep -E 'CLP_VERSION' "$TP/gen/clp/config_clp.h" | sed 's/^/    /'
done
for f in $(find "$B" -name 'config.h' | head -n 1); do
  cp "$f" "$TP/gen/clp/config.h"; echo "  copied config.h -> gen/clp/"
done
