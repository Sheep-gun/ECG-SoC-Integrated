param(
    [switch]$SkipMatlab,
    [switch]$ParseOnly,
    [string]$Python,
    [string]$Ltspice
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$SourceRoot = Split-Path -Parent $Root
$Runner = Join-Path $PSScriptRoot 'run_ltspice.ps1'
$Deck = Join-Path $Root 'schematics\xmodel_aligned'
$Raw = Join-Path $Root 'results\xmodel_aligned\raw'
$Logs = Join-Path $Root 'results\xmodel_aligned\logs'

if (-not $Python) { $Python = $env:PYTHON_EXE }
if (-not $Python) {
    $LocalPython = Join-Path $SourceRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $LocalPython) { $Python = $LocalPython }
}
if (-not $Python) {
    $PythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($PythonCommand) { $Python = $PythonCommand.Source }
}
if (-not $Python -or -not (Test-Path -LiteralPath $Python)) {
    throw 'Python not found. Pass -Python <python.exe> or set PYTHON_EXE. Python 3 with numpy is required.'
}
if (-not $Ltspice) { $Ltspice = $env:LTSPICE_EXE }
if (-not $Ltspice) {
    $Candidates = @(@(
        (Join-Path $env:LOCALAPPDATA 'Programs\ADI\LTspice\LTspice.exe'),
        (Join-Path $env:ProgramFiles 'ADI\LTspice\LTspice.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'ADI\LTspice\LTspice.exe')
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
    if ($Candidates) { $Ltspice = $Candidates[0] }
}
if (-not $Ltspice -or -not (Test-Path -LiteralPath $Ltspice)) {
    throw 'LTspice not found. Pass -Ltspice <LTspice.exe> or set LTSPICE_EXE.'
}

$Expected = @{
    'FULL_AFE_ADC_SH.asc' = 'A256FB8D38CB34825958BFE9CD9F7C0C44032A842190D9E8B9434B82E662EA31'
    'patient100_ecg_10s.txt' = '5C8DE5435F97C6F9320B398869538CD6992CAA6250825D89A9FD3D019FECCA36'
    'ECG_AFE_ADC_Schematic_정리.docx' = '03BFBCE909ED42B9B65BA3B8B8E9FAF516B9C4F97EA853BFDF7147537118D0BC'
}
function Get-SharedSha256([string]$Path) {
    $Stream = [System.IO.File]::Open($Path,[System.IO.FileMode]::Open,[System.IO.FileAccess]::Read,[System.IO.FileShare]::ReadWrite)
    try { $Sha=[System.Security.Cryptography.SHA256]::Create(); return (($Sha.ComputeHash($Stream)|ForEach-Object{$_.ToString('x2')})-join '').ToUpperInvariant() }
    finally { $Stream.Dispose() }
}
foreach($Name in $Expected.Keys){
    if((Get-SharedSha256 (Join-Path $SourceRoot $Name)) -ne $Expected[$Name]){ throw "Original SHA256 changed: $Name" }
}

if(-not $ParseOnly){
    & $Python (Join-Path $PSScriptRoot 'prepare_xmodel_aligned.py')
    $Asc=Join-Path $Deck 'FULL_AFE_ADC_SH_xmodel_aligned.asc'
    $p=Start-Process -FilePath $Ltspice -ArgumentList @('-netlist',$Asc) -WorkingDirectory $Deck -WindowStyle Hidden -Wait -PassThru
    if($p.ExitCode -ne 0){ throw "Aligned ASC netlist generation failed: $($p.ExitCode)" }
    & $Python (Join-Path $PSScriptRoot 'generate_xmodel_aligned_testbenches.py')
    New-Item -ItemType Directory -Force -Path $Raw,$Logs | Out-Null

    # Run the graphical 10 s source of truth first, then every independent AC,
    # mapping, convergence and fixed-XMODEL analog-stress deck.
    & $Runner -InputFile $Asc -RawDirectory $Raw -LogDirectory $Logs -Ltspice $Ltspice
    Get-ChildItem -LiteralPath $Deck -Filter 'xma_*.cir' | Sort-Object Name | ForEach-Object {
        & $Runner -InputFile $_.FullName -RawDirectory $Raw -LogDirectory $Logs -Ltspice $Ltspice
    }
}

& $Python (Join-Path $PSScriptRoot 'parse_xmodel_aligned_results.py')
Write-Host 'MATLAB source checkout is intentionally omitted from this LTspice-XMODEL handoff.'
& $Python (Join-Path $PSScriptRoot 'qc_xmodel_aligned.py')

Write-Host 'XMODEL-aligned LTspice validation completed.'
Write-Host 'Fixed XMODEL correlation remains a separate licensed gate:'
Write-Host '  scripts/run_fixed_xmodel_correlation.sh'
Write-Host '  scripts/compare_xmodel_ltspice.py'
