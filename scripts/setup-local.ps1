$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$VenvDir = Join-Path $BackendDir ".venv"

function Get-PythonLauncher {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) {
    foreach ($version in @("-3.13", "-3.12", "-3.11", "-3.10", "-3")) {
      try {
        & py $version --version *> $null
        return @{
          Command = "py"
          Args = @($version)
          Version = (& py $version --version 2>&1 | Out-String).Trim()
        }
      } catch {
      }
    }
  }

  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    return @{
      Command = $python.Source
      Args = @()
      Version = (& $python.Source --version 2>&1 | Out-String).Trim()
    }
  }

  throw "A supported Python interpreter is required to set up the backend."
}

function Invoke-Python {
  param(
    [Parameter(Mandatory = $true)]
    [hashtable]$Launcher,

    [Parameter(Mandatory = $true)]
    [string[]]$Arguments
  )

  & $Launcher.Command @($Launcher.Args + $Arguments)
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  throw "Node.js is required to set up the frontend."
}

$PythonLauncher = Get-PythonLauncher
Write-Host "Using Python: $($PythonLauncher.Version)"

if (-not (Test-Path $VenvDir)) {
  Write-Host "Creating backend virtual environment..."
  Invoke-Python -Launcher $PythonLauncher -Arguments @("-m", "venv", $VenvDir)
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
  throw "Backend virtual environment is missing python.exe at $VenvPython"
}

Write-Host "Installing backend dependencies..."
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $BackendDir "requirements.txt")

Write-Host "Installing frontend dependencies..."
Push-Location $FrontendDir
try {
  if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    & pnpm install --frozen-lockfile
  } else {
    & npm install
  }
} finally {
  Pop-Location
}

$FrontendEnv = Join-Path $FrontendDir ".env.local"
if (-not (Test-Path $FrontendEnv)) {
  @(
    "BACKEND_API_URL=http://localhost:8000"
    "NEXT_PUBLIC_API_URL=http://localhost:8000"
  ) | Set-Content -Path $FrontendEnv
}

$BackendEnv = Join-Path $BackendDir ".env"
if (-not (Test-Path $BackendEnv)) {
  @(
    "ALLOWED_ORIGINS=http://localhost:3000"
    "BACKEND_HOST=0.0.0.0"
    "BACKEND_PORT=8000"
    "ENVIRONMENT=development"
  ) | Set-Content -Path $BackendEnv
}

Write-Host ""
Write-Host "Local setup is complete."
Write-Host "Start everything with:"
Write-Host "  .\scripts\dev-local.ps1"
Write-Host "If you want packet capture on Windows, use:"
Write-Host "  .\scripts\dev-local-capture.ps1"
Write-Host ""
Write-Host "Optional backend dev tools can be installed with:"
Write-Host "  .\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt"
