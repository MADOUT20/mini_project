$ErrorActionPreference = "Stop"

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

if (-not (Test-Path $BackendVenvPython)) {
  throw "Backend dependencies are missing. Run .\scripts\setup-local.ps1 first."
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
  throw "Frontend dependencies are missing. Run .\scripts\setup-local.ps1 first."
}

$ShellExe = Get-ShellExecutable
$FrontendCommand = if (Get-Command pnpm -ErrorAction SilentlyContinue) { "pnpm dev" } else { "npm run dev" }
$NpcapService = Get-Service -Name npcap -ErrorAction SilentlyContinue

if (-not $NpcapService) {
  Write-Warning "Npcap was not detected. Install Npcap before using live packet capture on Windows."
}

$EscapedBackendDir = Escape-SingleQuotes $BackendDir
$EscapedFrontendDir = Escape-SingleQuotes $FrontendDir
$EscapedBackendPython = Escape-SingleQuotes $BackendVenvPython
$EscapedBackendApiUrl = Escape-SingleQuotes $BackendApiUrl
$EscapedAllowedOrigins = Escape-SingleQuotes $AllowedOrigins

$BackendCommand = "& { Set-Location '$EscapedBackendDir'; `$env:ALLOWED_ORIGINS='$EscapedAllowedOrigins'; & '$EscapedBackendPython' -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload }"
$FrontendCommandBlock = "& { Set-Location '$EscapedFrontendDir'; `$env:BACKEND_API_URL='$EscapedBackendApiUrl'; `$env:NEXT_PUBLIC_API_URL='$EscapedBackendApiUrl'; $FrontendCommand }"

Start-Process -FilePath $ShellExe -Verb RunAs -ArgumentList @("-NoExit", "-Command", $BackendCommand) -WorkingDirectory $BackendDir | Out-Null
Start-Process -FilePath $ShellExe -ArgumentList @("-NoExit", "-Command", $FrontendCommandBlock) -WorkingDirectory $FrontendDir | Out-Null

Write-Host ""
Write-Host "ChaosFaction capture mode is starting in separate PowerShell windows."
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend:  http://localhost:8000"
Write-Host "The backend window should request Administrator access."
Write-Host "Close the two PowerShell windows to stop the app."
