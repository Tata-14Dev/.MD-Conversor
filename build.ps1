# Instala las dependencias y genera dist\conversor.exe (standalone, no requiere Python instalado).

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Output "uv no esta instalado. Instalando..."
    irm https://astral.sh/uv/install.ps1 | iex
}

uv sync --dev
if (-not $?) { exit 1 }

Remove-Item -Recurse -Force build, dist, conversor.spec -ErrorAction SilentlyContinue

uv run pyinstaller --onefile --console --name conversor `
    --collect-all markitdown `
    --collect-all magika `
    main.py
if (-not $?) { exit 1 }

Write-Output ""
Write-Output "Listo: dist\conversor.exe"
