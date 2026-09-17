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

# The engine must import as an installed package rather than because the
# working directory happens to be on sys.path, so check it from elsewhere.
Push-Location ([System.IO.Path]::GetTempPath())
try {
    uv run --project $PSScriptRoot/.. python -c "from py2048 import Board; print('py2048: Board imports from', Board.__module__)"
}
finally {
    Pop-Location
}
Write-Host ""
Write-Host "Smoke test passed."
