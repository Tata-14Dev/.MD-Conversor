# conversor

Convierte archivos (PDF, Word, PowerPoint, Excel, HTML, imágenes, audio, etc.) a Markdown desde la consola, usando [MarkItDown](https://github.com/microsoft/markitdown).

## Uso rápido (sin instalar nada)

Descargá `conversor.exe` desde la sección [Releases](../../releases) de este repo y ejecutalo. Es un único archivo, no necesita Python ni ninguna otra instalación.

```
conversor
```

Te va a pedir la ruta del archivo (con autocompletado por Tab) y guarda el `.md` en la misma carpeta.

Otras formas de usarlo:

```
conversor archivo.pdf                # convierte un archivo puntual
conversor carpeta -c                 # convierte todos los archivos de una carpeta
conversor carpeta -c -r              # ídem, incluyendo subcarpetas
conversor archivo.pdf -o otra_carpeta  # guarda el resultado en otra carpeta
conversor -u                         # combina varios archivos en un solo .md, en el orden que indiques
```

## Desarrollo

Requiere [uv](https://docs.astral.sh/uv/).

```
uv sync
uv run conversor
```

Para instalarlo como comando global (`conversor` disponible en cualquier consola):

```
uv tool install --editable .
```

## Generar el .exe

```
.\build.ps1
```

Deja el ejecutable en `dist\conversor.exe`. También se genera automáticamente en cada tag `vX.Y.Z` publicado (ver `.github/workflows/release.yml`), quedando adjunto a la Release correspondiente.
