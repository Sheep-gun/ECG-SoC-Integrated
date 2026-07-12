param(
    [string]$Vivado = "C:\Xilinx\Vivado\2020.2\bin\vivado.bat",
    [switch]$CaptureCurrent,
    [string]$CurrentOutput = "device_view_full.png",
    [switch]$FitCurrent,
    [switch]$ZoomCurrent,
    [switch]$ZoomOutCurrent,
    [switch]$TimingOnly
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = (Resolve-Path (Join-Path $here "..\..\..")).Path
$work = "C:\Users\YangGeon\_ecg_p05_vivado_work"
$tcl = Join-Path $here "export_vivado_figures.tcl"

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class P05Win32 {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint flags);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, int data, UIntPtr extra);
}
"@

function Save-WindowPng([System.Diagnostics.Process]$process, [string]$path) {
    $process.Refresh()
    $rect = New-Object P05Win32+RECT
    if (-not [P05Win32]::GetWindowRect($process.MainWindowHandle, [ref]$rect)) {
        throw "Could not obtain the Vivado window rectangle"
    }
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    $bitmap = New-Object System.Drawing.Bitmap $width, $height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    [P05Win32]::ShowWindow($process.MainWindowHandle, 3) | Out-Null
    [P05Win32]::SetForegroundWindow($process.MainWindowHandle) | Out-Null
    Start-Sleep -Seconds 2
    $hdc = $graphics.GetHdc()
    $printed = [P05Win32]::PrintWindow($process.MainWindowHandle, $hdc, 2)
    $graphics.ReleaseHdc($hdc)
    if (-not $printed) {
        $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
    }
    $bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}

function Export-View([string]$phase, [string]$filename, [bool]$zoom) {
    $marker = Join-Path $work ($phase + "_READY")
    Remove-Item -LiteralPath $marker -Force -ErrorAction SilentlyContinue
    $started = Get-Date
    $command = "& '$Vivado' -mode gui -source '$tcl' -tclargs $phase -nolog -nojournal"
    $launcher = Start-Process -FilePath powershell.exe -ArgumentList @("-NoProfile", "-Command", $command) -PassThru -WindowStyle Hidden
    $deadline = (Get-Date).AddMinutes(3)
    while ((-not (Test-Path -LiteralPath $marker)) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 500
        if ($launcher.HasExited) { throw "Vivado launcher exited before preparing $phase" }
    }
    if (-not (Test-Path -LiteralPath $marker)) { throw "Timed out waiting for $marker" }
    $process = Get-Process vivado -ErrorAction Stop | Where-Object { $_.StartTime -ge $started.AddSeconds(-2) } | Sort-Object StartTime -Descending | Select-Object -First 1
    if (-not $process) { throw "Could not locate the Vivado GUI process for $phase" }
    Start-Sleep -Seconds 8
    $process.Refresh()
    [P05Win32]::SetForegroundWindow($process.MainWindowHandle) | Out-Null
    Start-Sleep -Seconds 2
    if ($zoom) {
        $rect = New-Object P05Win32+RECT
        [P05Win32]::GetWindowRect($process.MainWindowHandle, [ref]$rect) | Out-Null
        # The selected accelerator cells are highlighted by Tcl. Zoom about the
        # central-right device region in the actual Device View; no image content
        # is synthesized or redrawn by this helper.
        $x = [int]($rect.Left + 0.66 * ($rect.Right - $rect.Left))
        $y = [int]($rect.Top + 0.52 * ($rect.Bottom - $rect.Top))
        [P05Win32]::SetCursorPos($x, $y) | Out-Null
        1..6 | ForEach-Object {
            [P05Win32]::mouse_event(0x0800, 0, 0, 120, [UIntPtr]::Zero)
            Start-Sleep -Milliseconds 250
        }
        Start-Sleep -Seconds 3
    }
    Save-WindowPng $process (Join-Path $here $filename)
    Stop-Process -Id $process.Id -Force
    $process.WaitForExit()
    Stop-Process -Id $launcher.Id -Force -ErrorAction SilentlyContinue
}

if ($CaptureCurrent) {
    $current = Get-Process vivado -ErrorAction Stop | Sort-Object StartTime -Descending | Select-Object -First 1
    $rect = New-Object P05Win32+RECT
    [P05Win32]::GetWindowRect($current.MainWindowHandle, [ref]$rect) | Out-Null
    [P05Win32]::ShowWindow($current.MainWindowHandle, 3) | Out-Null
    [P05Win32]::SetForegroundWindow($current.MainWindowHandle) | Out-Null
    Start-Sleep -Seconds 2
    if ($FitCurrent) {
        [P05Win32]::SetCursorPos([int]($rect.Left + 0.522 * ($rect.Right - $rect.Left)), [int]($rect.Top + 0.238 * ($rect.Bottom - $rect.Top))) | Out-Null
        [P05Win32]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)
        [P05Win32]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
        Start-Sleep -Seconds 3
    }
    if ($ZoomCurrent) {
        [P05Win32]::SetCursorPos([int]($rect.Left + 0.89 * ($rect.Right - $rect.Left)), [int]($rect.Top + 0.68 * ($rect.Bottom - $rect.Top))) | Out-Null
        1..5 | ForEach-Object {
            [P05Win32]::mouse_event(0x0800, 0, 0, 120, [UIntPtr]::Zero)
            Start-Sleep -Milliseconds 250
        }
        Start-Sleep -Seconds 3
    }
    if ($ZoomOutCurrent) {
        [P05Win32]::SetCursorPos([int]($rect.Left + 0.88 * ($rect.Right - $rect.Left)), [int]($rect.Top + 0.62 * ($rect.Bottom - $rect.Top))) | Out-Null
        1..4 | ForEach-Object {
            [P05Win32]::mouse_event(0x0800, 0, 0, -120, [UIntPtr]::Zero)
            Start-Sleep -Milliseconds 250
        }
        Start-Sleep -Seconds 3
    }
    Save-WindowPng $current (Join-Path $here $CurrentOutput)
    exit 0
}

if ($TimingOnly) {
    Export-View "gui_timing" "worst_setup_path.png" $false
} else {
    Export-View "gui_full" "device_view_full.png" $false
    Export-View "gui_zoom" "device_view_accelerator_zoom.png" $true
    Export-View "gui_timing" "worst_setup_path.png" $false
}
