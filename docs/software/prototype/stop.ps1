$ErrorActionPreference = 'Stop'
$pidPath = Join-Path $PSScriptRoot '.runtime/frontend.pid'
if (-not (Test-Path -LiteralPath $pidPath)) { Write-Host 'No one-click server is recorded. For npm run dev, use Ctrl+C in its terminal.'; exit 0 }
$serverProcessId = [int](Get-Content -LiteralPath $pidPath)
$serverProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $serverProcessId"
$expectedScript = Join-Path $PSScriptRoot 'frontend\node_modules\vite\bin\vite.js'
if ($serverProcess -and $serverProcess.Name -eq 'node.exe' -and $serverProcess.CommandLine.Contains($expectedScript)) {
    Stop-Process -Id $serverProcessId
    Write-Host 'Prototype server stopped.'
} elseif ($serverProcess) { throw 'Recorded PID belongs to a different process. It was not stopped.' }
Remove-Item -LiteralPath $pidPath
