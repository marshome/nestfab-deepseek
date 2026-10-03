# The gate, in one place, because it is run after every batch and a mistyped environment is a lost round.
#
#   pwsh -NoProfile -File re/gate.ps1
#
# Build with zero errors and zero warnings, delete the test binaries first so a stale one cannot fake a pass, run ctest,
# then the four checks. Every stage prints OK or the failure; the exit code is the first failure.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$lcns = Join-Path $root 'lcns'
$build = Join-Path $lcns 'build'

$mingw = 'C:\Program Files\JetBrains\CLion 2025.3.3\bin\mingw\bin'
$cmake = 'C:\Program Files\JetBrains\CLion 2025.3.3\bin\cmake\win\x64\bin\cmake.exe'
$ninjaDir = 'C:\Program Files\JetBrains\CLion 2025.3.3\bin\ninja\win\x64'
$py = 'C:\Users\16479\AppData\Local\Python\bin\python.exe'
$env:PATH = "$mingw;$ninjaDir;" + $env:PATH

function Stage([string]$name, [scriptblock]$body) {
    Write-Host ("== " + $name)
    & $body
    if ($LASTEXITCODE -ne 0) {
        Write-Host ("GATE FAILED at " + $name)
        exit 1
    }
}

if (-not (Test-Path (Join-Path $build 'build.ninja'))) {
    Stage 'configure' { & $cmake -S $lcns -B $build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER=g++ -DCMAKE_MAKE_PROGRAM=ninja }
}

Stage 'clean test binaries' {
    Get-ChildItem -Path $build -Filter 'test_*.exe' -ErrorAction SilentlyContinue | Remove-Item -Force
    $global:LASTEXITCODE = 0
}

$log = Join-Path $build 'gate_build.log'
Stage 'build' { & $cmake --build $build 2>&1 | Tee-Object -FilePath $log | Select-Object -Last 4 }

# Both words are matched as regular expressions, so "0 errors" and "0 warnings" do not trip the check while a real
# diagnostic always does. The summary lines ninja prints are counted only when their number is not zero.
$bad = Select-String -Path $log -Pattern 'warning|error' | Where-Object { $_.Line -notmatch '0 (warning|error)s?' }
if ($bad) {
    Write-Host 'GATE FAILED: the build log has warnings or errors'
    $bad | Select-Object -First 20 | ForEach-Object { $_.Line }
    exit 1
}
Write-Host 'build clean: no warnings, no errors'

$ctest = Join-Path (Split-Path -Parent $cmake) 'ctest.exe'
Stage 'ctest' { & $ctest --test-dir $build --output-on-failure 2>&1 | Select-Object -Last 6 }
Stage 'check_recovery' { & $py (Join-Path $lcns 'tools\check_recovery.py') }
Stage 'check_arch' { & $py (Join-Path $lcns 'tools\check_arch.py') }
Stage 'embeddings' { & $py (Join-Path $root 're\check_embeddings.py') }
Stage 'coverage' { & $py (Join-Path $root 're\g_coverage.py') }
Stage 'acceptance' { & $py (Join-Path $root 're\g_acceptance.py') }
# **AND THE OFFSET COMPENSATION CHECK**, because `lcns` declared `Nester` with no data while the module's base part is 0x18 bytes and a constant plus five
# `member + gap == offset` assertions made that look measured. **An offset that needs arithmetic to reach is an offset the model does not have.** It was added after
# the human asked "Nester 这个基类没有字段？" and the answer was no.
Stage 'offset-compensation' { & $py (Join-Path $root 're\g_gap_compensation.py') }
# **AND THE OFFSET-ACCESSOR CHECK**, because round 135 gave `EngineBase` and `EquivalentEngine` a `static int32_t offsetOfAtNN()` **so that a test could read a protected
# member's offset** -- a class growing an API for a test, when the project's own form is `static_assert(offsetof(T, member) == 0xNN, "RE 0xADDR")` beside the member, 86 of
# which already exist. **The replacement was two `static_assert`s on `sizeof`, which need no API at all.** `re/g_prove_no_offset_accessor.py` plants the mistake back.
Stage 'offset-accessor' { & $py (Join-Path $root 're\g_no_offset_accessor.py') }
# **AND THE LEADS CHECK**, because a question noticed while reading one function used to live in a prose comment -- and a comment is not a queue, nothing iterates a comment.
# `re/leads.json` holds what has been NOTICED AND NOT YET ANSWERED, each with a closing condition and an evidence pointer, and `re/g_leads.py sweep` derives candidates from
# the ledger's witnesses and the headers' comments. **This is what makes the work systematic instead of remembered**, and it is the answer to "can you record these
# scattered points and not drop them" -- the queue is machine-checked, so a question that reaches the tree and not the queue fails the gate.
Stage 'leads' { & $py (Join-Path $root 're\g_check_leads.py') }

Write-Host 'GATE GREEN'
# The verdict goes to a file so re/g_rules.py can check "门禁保持全绿" without paying two minutes for it. A rule checker that
# is slow is a rule checker nobody runs; a rule checker that reads a stale file is worse, so the header hash is written too and
# g_rules.py reports UNCHECKED when the file is older than the newest commit.
$gateStamp = (git -C $root log -1 --format='%H' 2>$null)
Set-Content -Path (Join-Path $build 'gate_result.txt') -Encoding utf8 -Value @(
    "GATE GREEN",
    "at $((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))",
    "head $gateStamp"
)
exit 0
