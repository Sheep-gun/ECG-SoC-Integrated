param(
    [Parameter(Mandatory = $true)][string]$InputFile,
    [Parameter(Mandatory = $true)][string]$RawDirectory,
    [Parameter(Mandatory = $true)][string]$LogDirectory,
    [string]$Ltspice = ''
)

$ErrorActionPreference = 'Stop'
if (-not $Ltspice) {
    $DefaultLtspice = Join-Path $env:LOCALAPPDATA 'Programs\ADI\LTspice\LTspice.exe'
    if (Test-Path -LiteralPath $DefaultLtspice) { $Ltspice = $DefaultLtspice }
    else { $Ltspice = (Get-Command LTspice.exe -ErrorAction Stop).Source }
}
if (-not (Test-Path -LiteralPath $Ltspice)) { throw "LTspice not found: $Ltspice" }

$InputPath = (Resolve-Path -LiteralPath $InputFile).Path
$Stem = [System.IO.Path]::GetFileNameWithoutExtension($InputPath)
$SourceDirectory = Split-Path -Parent $InputPath
$RawDirectory = [System.IO.Path]::GetFullPath($RawDirectory)
$LogDirectory = [System.IO.Path]::GetFullPath($LogDirectory)
New-Item -ItemType Directory -Force -Path $RawDirectory, $LogDirectory | Out-Null

$CommandRecord = Join-Path $LogDirectory "$Stem.command.txt"
@(
    "executable=$Ltspice"
    "arguments=-b -ascii `"$InputPath`""
    "working_directory=$SourceDirectory"
    "started_utc=$([DateTime]::UtcNow.ToString('o'))"
) | Set-Content -LiteralPath $CommandRecord -Encoding UTF8

$Process = Start-Process -FilePath $Ltspice -ArgumentList @('-b', '-ascii', $InputPath) -WorkingDirectory $SourceDirectory -WindowStyle Hidden -Wait -PassThru
$SourceRaw = Join-Path $SourceDirectory "$Stem.raw"
$SourceOpRaw = Join-Path $SourceDirectory "$Stem.op.raw"
$SourceLog = Join-Path $SourceDirectory "$Stem.log"
if (Test-Path -LiteralPath $SourceRaw) { Move-Item -Force -LiteralPath $SourceRaw -Destination (Join-Path $RawDirectory "$Stem.raw") }
if (Test-Path -LiteralPath $SourceOpRaw) { Move-Item -Force -LiteralPath $SourceOpRaw -Destination (Join-Path $RawDirectory "$Stem.op.raw") }
if (Test-Path -LiteralPath $SourceLog) { Move-Item -Force -LiteralPath $SourceLog -Destination (Join-Path $LogDirectory "$Stem.log") }

$FinalLog = Join-Path $LogDirectory "$Stem.log"
if (-not (Test-Path -LiteralPath $FinalLog)) { throw "LTspice did not create log: $FinalLog" }
$LogText = Get-Content -Raw -LiteralPath $FinalLog
$Completed = $LogText -match 'Total elapsed time:'
$Fatal = $LogText -match '(?i)timestep too small|singular matrix|fatal error|could not converge'
Add-Content -LiteralPath $CommandRecord -Encoding UTF8 -Value @(
    "return_code=$($Process.ExitCode)"
    "completed_in_log=$Completed"
    "fatal_pattern_in_log=$Fatal"
    "finished_utc=$([DateTime]::UtcNow.ToString('o'))"
)
if ($Process.ExitCode -ne 0 -or -not $Completed -or $Fatal) {
    throw "LTspice validation failed for $Stem (return=$($Process.ExitCode), completed=$Completed, fatal=$Fatal)"
}
Write-Host "PASS $Stem"
