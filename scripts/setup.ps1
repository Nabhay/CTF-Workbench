$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Require-Command($Name, $Hint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is not on PATH. $Hint"
    }
}

Require-Command uv "Install uv from https://docs.astral.sh/uv/getting-started/installation/"
Require-Command npm "Install Node.js 20+ from https://nodejs.org/"

if (-not (Test-Path (Join-Path $Root ".env"))) {
    Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
    Write-Host "Created .env from .env.example. Set CTF_WORKBENCH_SESSION_SECRET before starting."
}

Write-Host "Installing Python dependencies..."
uv sync --group dev

Write-Host "Installing frontend dependencies..."
npm --prefix (Join-Path $Root "apps\web") install

Write-Host "Install complete. Run .\scripts\dev.ps1"
