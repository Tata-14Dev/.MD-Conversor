# Instala las dependencias y genera:
#   dist\conversor.exe      -> interfaz grafica (para el publico en general)
#   dist\conversor-cli.exe  -> version de consola (uso avanzado / scripting)

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Output "uv no esta instalado. Instalando..."
    irm https://astral.sh/uv/install.ps1 | iex
}

uv sync --dev
if (-not $?) { exit 1 }

Remove-Item -Recurse -Force build, dist, conversor.spec, conversor-cli.spec -ErrorAction SilentlyContinue

$iconArgs = @()
if (Test-Path "assets\icon.ico") {
    $iconArgs = @("--icon", "assets\icon.ico")
}

Write-Output "Generando conversor.exe (interfaz grafica)..."
uv run pyinstaller --onefile --windowed --name conversor `
    --collect-all markitdown --collect-all magika `
    --add-data "assets;assets" `
    @iconArgs `
    gui_main.py
if (-not $?) { exit 1 }

Write-Output "Generando conversor-cli.exe (consola)..."
uv run pyinstaller --onefile --console --name conversor-cli `
    --collect-all markitdown --collect-all magika `
    @iconArgs `
    main.py
if (-not $?) { exit 1 }

Write-Output ""
Write-Output "Listo: dist\conversor.exe y dist\conversor-cli.exe"
