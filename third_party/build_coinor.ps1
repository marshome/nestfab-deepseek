# Build the COIN-OR trio that libcns_dump_64.dll statically links, with CLion's MinGW GCC.
#
# Choices and why:
#   * VERSIONS: the dump's Clp-era API (OsiClpSolverInterface, specialOptions, cleanupScaling) and
#     the earlier finding "statically links Clp 1.15.3" => stable/1.15 + Osi stable/0.107 +
#     CoinUtils stable/2.10.  The tag trees ship no `configure` and there is no autoconf here, but
#     the STABLE BRANCHES do ship it (verified: HTTP 200, ~780 KB each).
#   * make: only CLion's mingw32-make exists => a make.exe shim goes on PATH inside bash.
#   * no gfortran => BLAS/LAPACK disabled; Clp itself is C++ only.
$ErrorActionPreference = 'Continue'
$root   = 'D:\Nesting\nestfab\third_party'
$src    = Join-Path $root 'src'
$build  = Join-Path $root 'build'
$prefix = Join-Path $root 'install'
$shim   = Join-Path $root '_shim'
$mingw  = 'C:\Program Files\JetBrains\CLion 2025.3.3\bin\mingw\bin'
$bash   = 'C:\Program Files\Git\bin\bash.exe'
New-Item -ItemType Directory -Force -Path $src, $build, $prefix, $shim | Out-Null
Copy-Item (Join-Path $mingw 'mingw32-make.exe') (Join-Path $shim 'make.exe') -Force

$pkgs = @(
  @{ n='CoinUtils'; br='stable/2.10';  dir='coinutils' },
  @{ n='Osi';       br='stable/0.107'; dir='osi' },
  @{ n='Clp';       br='stable/1.15';  dir='clp' }
)

foreach ($p in $pkgs) {
    $tree = Join-Path $src $p.dir
    if (-not (Test-Path (Join-Path $tree 'configure'))) {
        if (Test-Path $tree) { Remove-Item -Recurse -Force $tree }
        "=== clone $($p.n) @ $($p.br) ==="
        & git clone --quiet --depth 1 --branch $p.br "https://github.com/coin-or/$($p.n)" $tree 2>&1 |
            Select-String -Pattern 'fatal|error' | Select-Object -First 3
    } else { "=== $($p.n) tree present ===" }
    if (-not (Test-Path (Join-Path $tree 'configure'))) { "    NO configure -- skipped"; continue }

    $bdir = Join-Path $build $p.dir
    New-Item -ItemType Directory -Force -Path $bdir | Out-Null
    $u = '/d/Nesting/nestfab/third_party'
    $cmd = @"
export PATH="$u/_shim:/c/Program Files/JetBrains/CLion 2025.3.3/bin/mingw/bin:`$PATH"
export CFLAGS="-O2" CXXFLAGS="-O2"
cd $u/build/$($p.dir)
echo "--- configure $($p.n) ---"
../src/$($p.dir)/configure --prefix=$u/install \
    --host=x86_64-w64-mingw32 --disable-shared --enable-static \
    --without-blas --without-lapack \
    CPPFLAGS="-I$u/install/include" LDFLAGS="-L$u/install/lib" > configure.log 2>&1
echo "configure exit=`$?"
grep -iE "error|not found|cannot" configure.log | head -n 5
tail -n 3 configure.log
if [ -f Makefile ]; then
  echo "--- make $($p.n) ---"
  make -j8 > make.log 2>&1
  echo "make exit=`$?"
  grep -iE "error:|Error [0-9]" make.log | head -n 5
  if [ -f .libs/lib$($p.dir).a ] || ls *.a >/dev/null 2>&1; then
     make install > install.log 2>&1
     echo "install exit=`$?"
  fi
fi
"@
    "=== build $($p.n) ==="
    & $bash -c $cmd 2>&1 | Select-Object -Last 18
}

"=== install tree ==="
Get-ChildItem $prefix -Recurse -Include *.a -ErrorAction SilentlyContinue |
    ForEach-Object { "   $($_.FullName.Replace($root, ''))" }
