#! /usr/bin/pwsh
#
# Run after any change to the container definition, and after a
# "Rebuild Without Cache". A definition that only works incrementally is
# broken for the next person who clones.

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

Write-Host "uv:     $(uv --version)"
Write-Host "gh:     $(gh --version | Select-Object -First 1)"
Write-Host "pwsh:   $($PSVersionTable.PSVersion)"
Write-Host "node:   $(node --version)"

# The check that matters most: the interpreter must come from .venv, not from
# a system Python that won on PATH.
$python = uv run python -c "import sys; print(sys.executable)"
Write-Host "python: $(uv run python --version) at $python"
if ($python -notlike "*.venv*") {
    throw "Python is not coming from .venv - a second interpreter is winning on PATH."
}

uv run python -c "import pygame; print('pygame:', pygame.version.ver)"
Write-Host ""
Write-Host "Smoke test passed."
