#! /usr/bin/pwsh
#
# Runs once when the dev container is created. Safe to re-run by hand after a
# partial failure.

$ErrorActionPreference = "Stop"
# Governs NATIVE commands (uv, gh, apt). Without this a non-zero exit from uv
# does not stop the script and the build reports success having done nothing.
$PSNativeCommandUseErrorActionPreference = $true

$workspace = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $workspace ".venv"

if ($env:CI) {
    Write-Host "CI is set - skipping local environment setup."
}
else {
    Write-Host "==> Installing uv"
    Invoke-RestMethod https://astral.sh/uv/install.sh | bash

    # The installer cannot modify the shell that is already running.
    $uvBin = Join-Path $HOME ".local/bin"
    if ($env:PATH -notlike "*$uvBin*") { $env:PATH = "${uvBin}:$env:PATH" }

    Write-Host "==> Syncing Python environment"
    Push-Location $workspace
    try { uv sync } finally { Pop-Location }
}

# The .claude volume is created root-owned on first mount, which leaves Claude
# Code unable to write its config. Harmless to repeat on later builds.
Write-Host "==> Claiming ~/.claude volume"
sudo chown -R vscode:vscode (Join-Path $HOME ".claude")

# A virtual environment that must be activated by hand eventually will not be.
# profile.ps1 is the AllHosts profile: it covers the integrated terminal and a
# bare `pwsh` alike.
Write-Host "==> Writing PowerShell profile"
$profileDir = Join-Path $HOME ".config/powershell"
New-Item -ItemType Directory -Force -Path $profileDir | Out-Null

@"
# Managed by .devcontainer/postCreateCommand.ps1 - edits will be overwritten.
`$venvActivate = "$venv/bin/activate.ps1"
if (Test-Path `$venvActivate) { . `$venvActivate }
"@ | Set-Content -Path (Join-Path $profileDir "profile.ps1") -Encoding utf8

Write-Host ""
Write-Host "Done. Next steps:"
Write-Host "  gh auth login                       # authorise GitHub access"
Write-Host "  uv run py2048                       # console game"
Write-Host "  pwsh .devcontainer/smoke-test.ps1   # verify the build"
