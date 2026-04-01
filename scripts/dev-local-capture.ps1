$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$BackendVenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$BackendApiUrl = if ($env:BACKEND_API_URL) { $env:BACKEND_API_URL } else { "http://localhost:8000" }
$AllowedOrigins = if ($env:ALLOWED_ORIGINS) { $env:ALLOWED_ORIGINS } else { "http://localhost:3000" }
$ProxyHost = if ($env:PROXY_HOST) { $env:PROXY_HOST } else { "0.0.0.0" }
$ProxyPort = if ($env:PROXY_PORT) { $env:PROXY_PORT } else { "8888" }

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

function Get-LanIPv4Address {
  try {
    $routes = Get-NetRoute -AddressFamily IPv4 -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue |
      Sort-Object RouteMetric, InterfaceMetric

    foreach ($route in $routes) {
      $config = Get-NetIPConfiguration -InterfaceIndex $route.InterfaceIndex -ErrorAction SilentlyContinue
      if (-not $config -or -not $config.IPv4Address) {
        continue
      }

      foreach ($address in $config.IPv4Address) {
        if ($address.IPAddress -and -not $address.IPAddress.StartsWith("169.254.")) {
          return $address.IPAddress
        }
      }
    }
  } catch {
  }

  return $null
}

if (-not (Test-Path $BackendVenvPython)) {
  throw "Backend dependencies are missing. Run .\scripts\setup-local.ps1 first."
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
  throw "Frontend dependencies are missing. Run .\scripts\setup-local.ps1 first."
}

$ShellExe = Get-ShellExecutable
$FrontendNext = Join-Path $FrontendDir "node_modules\.bin\next.cmd"
$NpcapService = Get-Service -Name npcap -ErrorAction SilentlyContinue
$LanIp = Get-LanIPv4Address

if (-not $NpcapService) {
  Write-Warning "Npcap was not detected. Install Npcap before using live packet capture on Windows."
}

if (-not (Test-Path $FrontendNext)) {
  throw "Next.js local binary is missing. Run .\scripts\setup-local.ps1 first."
}

$EscapedBackendDir = Escape-SingleQuotes $BackendDir
$EscapedFrontendDir = Escape-SingleQuotes $FrontendDir
$EscapedBackendPython = Escape-SingleQuotes $BackendVenvPython
$EscapedBackendApiUrl = Escape-SingleQuotes $BackendApiUrl
$EscapedAllowedOrigins = Escape-SingleQuotes $AllowedOrigins
$EscapedFrontendNext = Escape-SingleQuotes $FrontendNext
$EscapedProxyHost = Escape-SingleQuotes $ProxyHost
$EscapedProxyPort = Escape-SingleQuotes $ProxyPort

$BackendCommand = "& { Set-Location '$EscapedBackendDir'; `$env:ALLOWED_ORIGINS='$EscapedAllowedOrigins'; `$env:PROXY_ENABLED='1'; `$env:PROXY_HOST='$EscapedProxyHost'; `$env:PROXY_PORT='$EscapedProxyPort'; if (Get-Command Get-NetFirewallRule -ErrorAction SilentlyContinue) { if (-not (Get-NetFirewallRule -DisplayName 'ChaosFaction Proxy 8888' -ErrorAction SilentlyContinue)) { New-NetFirewallRule -DisplayName 'ChaosFaction Proxy 8888' -Direction Inbound -Profile Any -Protocol TCP -LocalPort $EscapedProxyPort -Action Allow | Out-Null } else { Set-NetFirewallRule -DisplayName 'ChaosFaction Proxy 8888' -Profile Any -Enabled True -Action Allow | Out-Null } ; if (-not (Get-NetFirewallRule -DisplayName 'ChaosFaction Backend 8000' -ErrorAction SilentlyContinue)) { New-NetFirewallRule -DisplayName 'ChaosFaction Backend 8000' -Direction Inbound -Profile Any -Protocol TCP -LocalPort 8000 -Action Allow | Out-Null } else { Set-NetFirewallRule -DisplayName 'ChaosFaction Backend 8000' -Profile Any -Enabled True -Action Allow | Out-Null } } ; & '$EscapedBackendPython' -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload }"
$FrontendCommandBlock = "& { Set-Location '$EscapedFrontendDir'; `$env:BACKEND_API_URL='$EscapedBackendApiUrl'; `$env:NEXT_PUBLIC_API_URL='$EscapedBackendApiUrl'; & '$EscapedFrontendNext' dev --turbo --hostname 0.0.0.0 --port 3000 }"

Start-Process -FilePath $ShellExe -Verb RunAs -ArgumentList @("-NoExit", "-Command", $BackendCommand) -WorkingDirectory $BackendDir | Out-Null
Start-Process -FilePath $ShellExe -ArgumentList @("-NoExit", "-Command", $FrontendCommandBlock) -WorkingDirectory $FrontendDir | Out-Null

Write-Host ""
Write-Host "ChaosFaction capture mode is starting in separate PowerShell windows."
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend:  http://localhost:8000"
if ($LanIp) {
  Write-Host "Proxy:    ${LanIp}:$ProxyPort"
  Write-Host "Use that Windows LAN IP as the phone proxy server on the same Wi-Fi or hotspot."
}
Write-Host "The backend window should request Administrator access."
Write-Host "If the phone loses access later, unblock the site from the dashboard or set the phone proxy back to None."
Write-Host "Close the two PowerShell windows to stop the app."
