param(
    [string]$VivadoBin = "C:\Xilinx\Vivado\2020.2\bin",
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..\..\..")).Path
$logRoot = Join-Path $scriptRoot "logs"
$traceRoot = Join-Path $scriptRoot "traces"
$buildRoot = Join-Path ([System.IO.Path]::GetTempPath()) "ecg_soc_section4_axi_ip"
$resolvedTemp = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$resolvedBuild = [System.IO.Path]::GetFullPath($buildRoot)

if ([string]::IsNullOrWhiteSpace($Python)) {
    $bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path -LiteralPath $bundledPython) {
        $Python = $bundledPython
    }
    else {
        $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
        if ($null -eq $pythonCommand) {
            throw "Python was not found. Pass -Python with a Python 3 executable."
        }
        $Python = $pythonCommand.Source
    }
}

if (-not $resolvedBuild.StartsWith($resolvedTemp, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to replace a build directory outside TEMP: $resolvedBuild"
}
if (Test-Path -LiteralPath $resolvedBuild) {
    Remove-Item -LiteralPath $resolvedBuild -Recurse -Force
}
New-Item -ItemType Directory -Path $resolvedBuild,$logRoot,$traceRoot -Force | Out-Null

foreach ($tool in "xvlog.bat", "xelab.bat", "xsim.bat") {
    if (-not (Test-Path -LiteralPath (Join-Path $VivadoBin $tool))) {
        throw "Vivado simulator executable not found: $(Join-Path $VivadoBin $tool)"
    }
}

function Invoke-XSimStep {
    param(
        [string]$WorkingDirectory,
        [string]$LogFile,
        [string]$Executable,
        [string[]]$Arguments
    )
    Push-Location $WorkingDirectory
    try {
        $output = & $Executable @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        $repoForward = $repoRoot.Replace("\", "/")
        $userForward = $env:USERPROFILE.Replace("\", "/")
        $output = @($output | ForEach-Object {
            $_.ToString().TrimEnd().Replace($repoRoot, "<REPO>").Replace($repoForward, "<REPO>").Replace($env:USERPROFILE, "<USERPROFILE>").Replace($userForward, "<USERPROFILE>")
        })
        $output | Out-File -LiteralPath $LogFile -Append -Encoding utf8
        $output | Out-Host
        if ($exitCode -ne 0) {
            throw "Simulation command failed with exit code ${exitCode}: $Executable"
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-SmokeTest {
    param(
        [string]$Name,
        [string]$Top,
        [string]$SourceDirectory,
        [string]$CaptureTcl,
        [string]$VcdName,
        [string]$PassMarker,
        [string]$Profile
    )

    $work = Join-Path $resolvedBuild $Name
    New-Item -ItemType Directory -Path $work -Force | Out-Null
    $log = Join-Path $logRoot "$Name.log"
    if (Test-Path -LiteralPath $log) {
        Remove-Item -LiteralPath $log -Force
    }
    $sources = Get-ChildItem -LiteralPath $SourceDirectory -Filter "*.v" | Sort-Object Name | ForEach-Object { $_.FullName }
    if ($sources.Count -eq 0) {
        throw "No Verilog sources found in $SourceDirectory"
    }

    Invoke-XSimStep $work $log (Join-Path $VivadoBin "xvlog.bat") (@("-work", "work") + $sources)
    Invoke-XSimStep $work $log (Join-Path $VivadoBin "xelab.bat") @("-debug", "typical", "-top", $Top, "-snapshot", "${Name}_sim")
    $tclForward = $CaptureTcl.Replace("\", "/")
    Invoke-XSimStep $work $log (Join-Path $VivadoBin "xsim.bat") @("${Name}_sim", "-tclbatch", $tclForward)

    if (-not (Select-String -LiteralPath $log -Pattern "^$PassMarker$" -Quiet)) {
        throw "PASS marker missing from $log"
    }
    $vcd = Join-Path $work $VcdName
    if (-not (Test-Path -LiteralPath $vcd)) {
        throw "Expected VCD was not generated: $vcd"
    }
    $trace = Join-Path $traceRoot "$Name.selected_trace.json"
    & $Python (Join-Path $scriptRoot "normalize_vcd.py") --profile $Profile --input $vcd --output $trace
    if ($LASTEXITCODE -ne 0) {
        throw "VCD normalization failed for $Name"
    }

    $vcdInfo = Get-Item -LiteralPath $vcd
    return [ordered]@{
        name = $Name
        top = $Top
        simulator = "Vivado XSim 2020.2"
        status = "PASS"
        pass_marker = $PassMarker
        source_directory = $SourceDirectory.Substring($repoRoot.Length + 1).Replace("\", "/")
        testbench = ($sources | Where-Object { $_ -match "tb_.*\.v$" } | Select-Object -First 1).Substring($repoRoot.Length + 1).Replace("\", "/")
        log = $log.Substring($repoRoot.Length + 1).Replace("\", "/")
        selected_trace = $trace.Substring($repoRoot.Length + 1).Replace("\", "/")
        raw_vcd_bytes = $vcdInfo.Length
        raw_vcd_sha256 = (Get-FileHash -LiteralPath $vcd -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

$accelerator = Invoke-SmokeTest `
    -Name "accelerator_smoke" `
    -Top "tb_snn_ecg_axi_smoke" `
    -SourceDirectory (Join-Path $repoRoot "components\digital_accelerator\ip_repo\snn_ecg_axi_accelerator\src") `
    -CaptureTcl (Join-Path $scriptRoot "capture_accelerator.tcl") `
    -VcdName "accelerator_smoke.vcd" `
    -PassMarker "AXI_SMOKE_PASS" `
    -Profile "accelerator"

$feeder = Invoke-SmokeTest `
    -Name "sample_feeder_smoke" `
    -Top "tb_axi_lite_axis_sample_feeder" `
    -SourceDirectory (Join-Path $repoRoot "components\digital_accelerator\ip_repo\axi_lite_axis_sample_feeder\src") `
    -CaptureTcl (Join-Path $scriptRoot "capture_feeder.tcl") `
    -VcdName "sample_feeder_smoke.vcd" `
    -PassMarker "FEEDER_SMOKE_PASS" `
    -Profile "feeder"

$summary = [ordered]@{
    status = "PASS"
    simulator = "Vivado XSim 2020.2"
    tests = @($accelerator, $feeder)
    note = "Raw VCD/WDB files are regenerable temporary products; logs and selected traces are retained."
}
$summaryPath = Join-Path $scriptRoot "axi_ip_smoke_summary.json"
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $summaryPath -Encoding utf8
Write-Host "Section 4 AXI/IP validation PASS"
Write-Host "Summary: $summaryPath"
