# Fetch the third party libraries libcns was linked against, using curl + git.
# Evidence for every entry is in third_party/README.md and third_party/fetch.py's manifest.
$ErrorActionPreference = 'Continue'
$root = 'D:\Nesting\nestfab\third_party'
$arch = Join-Path $root '_archives'
$src  = Join-Path $root 'src'
New-Item -ItemType Directory -Force -Path $arch, $src | Out-Null

function Get-File($url, $out) {
    if ((Test-Path $out) -and ((Get-Item $out).Length -gt 0)) {
        "   [skip] $([IO.Path]::GetFileName($out)) already present ($([math]::Round((Get-Item $out).Length/1MB,2)) MB)"
        return
    }
    if (Test-Path $out) { "   [warn] $([IO.Path]::GetFileName($out)) was 0 bytes (failed earlier) -- refetching"; Remove-Item -Force $out }
    "   [curl] $url"
    & curl.exe -sS -L --retry 5 --retry-delay 3 --retry-all-errors --max-time 3600 -o $out $url
    if ($LASTEXITCODE -eq 0 -and (Test-Path $out) -and (Get-Item $out).Length -gt 0) {
        "          -> $([math]::Round((Get-Item $out).Length/1MB,2)) MB"
    } else { "          FAILED ($LASTEXITCODE)" }
}

function Get-Repo($url, $tag, $dir) {
    $target = Join-Path $src $dir
    if (Test-Path (Join-Path $target '.git')) { "   [skip] $dir already cloned"; return }
    if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    "   [git ] $url @ $tag"
    & git clone --quiet --depth 1 --branch $tag $url $target
    if ($LASTEXITCODE -ne 0) { "          FAILED (exit $LASTEXITCODE)" }
}

"=== boost 1.63.0 (source release, 78 MB) ==="
Get-File 'https://archives.boost.io/release/1.63.0/source/boost_1_63_0.tar.bz2' (Join-Path $arch 'boost_1_63_0.tar.bz2')

"=== COIN-OR (CMake capable releases) ==="
Get-Repo 'https://github.com/coin-or/CoinUtils' 'releases/2.11.12' 'CoinUtils'
Get-Repo 'https://github.com/coin-or/Osi'       'releases/0.108.11' 'Osi'
Get-Repo 'https://github.com/coin-or/Clp'       'releases/1.17.10' 'Clp'

"=== jsoncpp / cryptopp ==="
Get-Repo 'https://github.com/open-source-parsers/jsoncpp' '1.9.5' 'jsoncpp'
Get-Repo 'https://github.com/weidai11/cryptopp'           'CRYPTOPP_8_9_0' 'cryptopp'

"=== result ==="
Get-ChildItem $arch -ErrorAction SilentlyContinue | ForEach-Object { "   archive: $($_.Name)  $([math]::Round($_.Length/1MB,2)) MB" }
Get-ChildItem $src -ErrorAction SilentlyContinue | ForEach-Object { "   src:     $($_.Name)" }
