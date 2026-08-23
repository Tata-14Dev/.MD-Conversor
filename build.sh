#!/usr/bin/env bash
# Instala las dependencias y genera:
#   dist/conversor.app    -> interfaz grafica (para el publico en general)
#   dist/conversor-cli    -> version de consola (uso avanzado / scripting)
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
    echo "uv no esta instalado. Instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

uv sync --dev

rm -rf build dist conversor.spec conversor-cli.spec

ICON_ARGS=()
if [ -f "assets/icon.icns" ]; then
    ICON_ARGS=(--icon assets/icon.icns)
fi

echo "Generando conversor.app (interfaz grafica)..."
uv run pyinstaller --onefile --windowed --name conversor \
    --collect-all markitdown --collect-all magika \
    --add-data "assets:assets" \
    "${ICON_ARGS[@]}" \
    gui_main.py

echo "Generando conversor-cli (consola)..."
uv run pyinstaller --onefile --console --name conversor-cli \
    --collect-all markitdown --collect-all magika \
    "${ICON_ARGS[@]}" \
    main.py

echo ""
echo "Listo: dist/conversor.app y dist/conversor-cli"
