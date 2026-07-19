param(
    [switch]$SkipMatlab,
    [switch]$ParseOnly,
    [string]$Python = '',
    [string]$Ltspice = '',
    [string]$SourceRoot = ''
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $SourceRoot) { $SourceRoot = Join-Path $Root 'source_inputs' }
if (-not $Python) { $Python = (Get-Command python -ErrorAction Stop).Source }
if (-not $Ltspice) {
    $DefaultLtspice = Join-Path $env:LOCALAPPDATA 'Programs\ADI\LTspice\LTspice.exe'
    if (Test-Path -LiteralPath $DefaultLtspice) { $Ltspice = $DefaultLtspice }
    else { $Ltspice = (Get-Command LTspice.exe -ErrorAction Stop).Source }
}
$Runner = Join-Path $PSScriptRoot 'run_ltspice.ps1'
$Deck = Join-Path $Root 'schematics\xmodel_aligned'
$Raw = Join-Path $Root 'results\xmodel_aligned\raw'
$Logs = Join-Path $Root 'results\xmodel_aligned\logs'

$Expected = @{
    'FULL_AFE_ADC_SH.asc' = 'A256FB8D38CB34825958BFE9CD9F7C0C44032A842190D9E8B9434B82E662EA31'
    'patient100_ecg_10s.txt' = '5C8DE5435F97C6F9320B398869538CD6992CAA6250825D89A9FD3D019FECCA36'
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
if(-not $SkipMatlab){
    $Matlab=(Get-Command matlab -ErrorAction Stop).Source
    $M=(Join-Path $PSScriptRoot 'run_fixed_matlab_patient.m').Replace("'","''")
    & $Matlab -batch "run('$M')"
    if($LASTEXITCODE -ne 0){ throw "MATLAB fixed-reference run failed: $LASTEXITCODE" }
    & $Python (Join-Path $PSScriptRoot 'compare_matlab_ltspice.py')
}
& $Python (Join-Path $PSScriptRoot 'qc_xmodel_aligned.py')

Write-Host 'XMODEL-aligned LTspice validation completed.'
Write-Host 'Fixed XMODEL correlation remains a separate licensed gate:'
Write-Host '  scripts/run_fixed_xmodel_correlation.sh'
Write-Host '  scripts/compare_xmodel_ltspice.py'
