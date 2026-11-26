$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Require-Command($Name, $Hint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is not on PATH. $Hint"
    }
}

function Test-LocalPort([int]$Port) {
    $listener = [System.Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $Port)
    try {
        $listener.Start()
        $listener.Stop()
        return $false
    } catch {
        return $true
    }
}

function Stop-ProcessTree([int]$ProcessId) {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ParentProcessId -eq $ProcessId } |
        ForEach-Object { Stop-ProcessTree -ProcessId $_.ProcessId }
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

Require-Command uv "Install uv, then run .\scripts\setup.ps1"
Require-Command npm "Install Node.js 20+, then run .\scripts\setup.ps1"

if (-not (Test-Path (Join-Path $Root ".env"))) {
    throw "Missing .env. Copy .env.example to .env, set CTF_WORKBENCH_SESSION_SECRET (>= 32 chars), then retry."
}

$ApiPort = 8745
$WebPort = 5173
if (Test-LocalPort $ApiPort) {
    throw "127.0.0.1:$ApiPort is already in use. Stop that process or change CTF_WORKBENCH_BIND_PORT."
}
if (Test-LocalPort $WebPort) {
    throw "127.0.0.1:$WebPort is already in use. Stop that process or change the Vite port."
}

$owned = @()
try {
    Write-Host "API     http://127.0.0.1:$ApiPort/api/v1/health"
    Write-Host "UI      http://127.0.0.1:$WebPort"
    Write-Host "Ctrl+C stops only these processes."

    $api = Start-Process -FilePath "uv" -ArgumentList @("run", "python", "-m", "ctf_workbench.api") -WorkingDirectory $Root -PassThru -NoNewWindow
    $owned += $api.Id
    $worker = Start-Process -FilePath "uv" -ArgumentList @("run", "python", "-m", "ctf_workbench.jobs") -WorkingDirectory $Root -PassThru -NoNewWindow
    $owned += $worker.Id

    npm --prefix (Join-Path $Root "apps\web") run dev
} finally {
    foreach ($id in $owned) {
        Stop-ProcessTree -ProcessId $id
    }
}
