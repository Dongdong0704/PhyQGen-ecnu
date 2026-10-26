param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$frontendPath = Join-Path $PSScriptRoot 'frontend'
$runtimePath = Join-Path $PSScriptRoot '.runtime'
$prototypeUrl = 'http://127.0.0.1:5173'
Set-Location -LiteralPath $frontendPath
if (-not (Get-Command node.exe -ErrorAction SilentlyContinue)) { throw 'Install Node.js 18+ first.' }
if (-not (Test-Path -LiteralPath (Join-Path $frontendPath 'node_modules/vite/bin/vite.js'))) {
    & npm.cmd ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check your npm connection.' }
}
try {
    $existingPage = Invoke-WebRequest -Uri $prototypeUrl -UseBasicParsing -TimeoutSec 2
    if ($existingPage.Content -match 'PhyQGen') {
        if (-not $NoBrowser) { Start-Process $prototypeUrl }
        Write-Host "Prototype already running: $prototypeUrl"
        exit 0
    }
} catch { }
New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
$viteFile = Join-Path $frontendPath 'node_modules/vite/bin/vite.js'
$process = Start-Process -FilePath (Get-Command node.exe).Source -ArgumentList @(('"' + $viteFile + '"'), '--host', '127.0.0.1', '--port', '5173') -WorkingDirectory $frontendPath -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimePath 'frontend.log') -RedirectStandardError (Join-Path $runtimePath 'frontend-error.log')
Set-Content -LiteralPath (Join-Path $runtimePath 'frontend.pid') -Value $process.Id
for ($attempt = 0; $attempt -lt 40; $attempt++) {
    Start-Sleep -Milliseconds 500
    if ($process.HasExited) { throw "Frontend exited. Read $runtimePath/frontend-error.log; port 5173 may be in use." }
    try {
        $response = Invoke-WebRequest -Uri $prototypeUrl -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            if (-not $NoBrowser) { Start-Process $prototypeUrl }
            Write-Host "Prototype ready: $prototypeUrl"
            Write-Host 'Teacher: teacher / Teacher123'
            Write-Host 'Admin: admin / Admin123'
            exit 0
        }
    } catch { }
}
throw "Frontend did not respond. Read logs in $runtimePath."
