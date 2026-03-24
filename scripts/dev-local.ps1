$ErrorActionPreference = "Stop"

param(
  [switch]$Check
)

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$BackendVenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$BackendApiUrl = if ($env:BACKEND_API_URL) { $env:BACKEND_API_URL } else { "http://localhost:8000" }
$AllowedOrigins = if ($env:ALLOWED_ORIGINS) { $env:ALLOWED_ORIGINS } else { "http://localhost:3000" }

function Get-ShellExecutable {
  $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
  if ($pwsh) {
    return $pwsh.Source
  }

  $powershell = Get-Command powershell -ErrorAction SilentlyContinue
  if ($powershell) {
    return $powershell.Source
  }

  throw "PowerShell was not found."
}

function Escape-SingleQuotes {
  param([string]$Value)
  return $Value.Replace("'", "''")
}

function Test-BackendReady {
  if (Test-Path $BackendVenvPython) {
    Write-Host "Backend: ready ($BackendVenvPython)"
    return $true
  }

  try {
    & python -c "import fastapi, uvicorn, dotenv" *> $null
    Write-Host "Backend: ready (system python)"
    return $true
  } catch {
    Write-Host "Backend: missing dependencies. Run .\scripts\setup-local.ps1 first."
    return $false
  }
}

function Test-FrontendReady {
  if (Test-Path (Join-Path $FrontendDir "node_modules")) {
    Write-Host "Frontend: ready"
    return $true
  }

  Write-Host "Frontend: missing dependencies. Run .\scripts\setup-local.ps1 first."
  return $false
}

if ($Check) {
  $backendOk = Test-BackendReady
  $frontendOk = Test-FrontendReady

  if (-not ($backendOk -and $frontendOk)) {
    exit 1
  }

  exit 0
}

if (-not (Test-BackendReady)) {
  exit 1
}

if (-not (Test-FrontendReady)) {
  exit 1
}

$ShellExe = Get-ShellExecutable
$BackendPython = if (Test-Path $BackendVenvPython) { $BackendVenvPython } else { "python" }
$FrontendCommand = if (Get-Command pnpm -ErrorAction SilentlyContinue) { "pnpm dev" } else { "npm run dev" }

$EscapedBackendDir = Escape-SingleQuotes $BackendDir
$EscapedFrontendDir = Escape-SingleQuotes $FrontendDir
$EscapedBackendPython = Escape-SingleQuotes $BackendPython
$EscapedBackendApiUrl = Escape-SingleQuotes $BackendApiUrl
$EscapedAllowedOrigins = Escape-SingleQuotes $AllowedOrigins

$BackendCommand = "& { Set-Location '$EscapedBackendDir'; `$env:ALLOWED_ORIGINS='$EscapedAllowedOrigins'; & '$EscapedBackendPython' -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload }"
$FrontendCommandBlock = "& { Set-Location '$EscapedFrontendDir'; `$env:BACKEND_API_URL='$EscapedBackendApiUrl'; `$env:NEXT_PUBLIC_API_URL='$EscapedBackendApiUrl'; $FrontendCommand }"

Start-Process -FilePath $ShellExe -ArgumentList @("-NoExit", "-Command", $BackendCommand) -WorkingDirectory $BackendDir | Out-Null
Start-Process -FilePath $ShellExe -ArgumentList @("-NoExit", "-Command", $FrontendCommandBlock) -WorkingDirectory $FrontendDir | Out-Null

Write-Host ""
Write-Host "ChaosFaction is starting in separate PowerShell windows."
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend:  http://localhost:8000"
Write-Host "Close the two PowerShell windows to stop the app."
Write-Host ""
Write-Host "If you want live packet capture on Windows, use .\scripts\dev-local-capture.ps1"
Write-Host "and make sure Npcap is installed."
