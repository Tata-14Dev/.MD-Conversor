# conversor

Convierte archivos (PDF, Word, PowerPoint, Excel, HTML, imágenes, audio, etc.) a Markdown, usando [MarkItDown](https://github.com/microsoft/markitdown).

## Uso rápido (sin instalar nada)

Descargá el ejecutable desde la sección [Releases](../../releases) de este repo. No necesitan Python ni ninguna otra instalación.

- **`conversor.exe`** — interfaz gráfica, pensada para cualquiera.
- **`conversor-cli.exe`** — versión de consola, para uso avanzado o scripting.

## OCR (imágenes y PDF escaneados)

Si convertís una imagen (`.png`, `.jpg`...) o un PDF que resulta ser un escaneo (sin texto seleccionable, por ejemplo apuntes fotografiados), el conversor detecta automáticamente que necesita OCR y usa **Tesseract** para leer el texto (en español e inglés). Un PDF normal con texto seleccionable sigue extrayéndose directo, sin pasar por OCR.

Para que esto funcione hace falta tener **Tesseract OCR** instalado en la máquina (no viene incluido en el ejecutable, como pasa con `ffmpeg` para audio):

```
winget install UB-Mannheim.TesseractOCR
```

Si no está instalado, el conversor te lo va a avisar claramente en el registro de errores en vez de devolver un `.md` vacío.

> Nota sobre calidad: Tesseract anda bien con texto impreso/tipeado (diapositivas escaneadas, fotocopias). Con **escritura a mano** los resultados van a ser limitados — es una limitación del motor gratuito, no de la configuración.

## Interfaz gráfica

Doble clic en `conversor.exe`:

1. **Agregar archivos...** / **Agregar carpeta...** para sumar lo que querés convertir (con Subir/Bajar podés reordenar la lista).
2. Opcional: elegir una carpeta de salida, o activar **Unificar todo en un solo archivo** para combinar todo en un único `.md` (en el orden de la lista).
3. **Convertir**. El resultado y cualquier error queda en el registro de abajo.

## Consola (`conversor` / `conversor-cli.exe`)

```
conversor
```

Te va a pedir la ruta del archivo (con autocompletado por Tab) y guarda el `.md` en la misma carpeta.

Otras formas de usarlo:

```
conversor archivo.pdf                  # convierte un archivo puntual
conversor carpeta -c                   # convierte todos los archivos de una carpeta
conversor carpeta -c -r                # ídem, incluyendo subcarpetas
conversor archivo.pdf -o otra_carpeta  # guarda el resultado en otra carpeta
conversor -u                           # combina varios archivos en un solo .md, en el orden que indiques
```

## Desarrollo

Requiere [uv](https://docs.astral.sh/uv/).

```
uv sync
uv run conversor       # CLI
uv run conversor-gui   # interfaz gráfica
```

Para instalar la CLI como comando global (`conversor` disponible en cualquier consola):

```
uv tool install --editable .
```

## Generar los ejecutables

```
.\build.ps1
```

Deja `dist\conversor.exe` (interfaz gráfica) y `dist\conversor-cli.exe` (consola). También se generan automáticamente en cada tag `vX.Y.Z` publicado (ver `.github/workflows/release.yml`), quedando adjuntos a la Release correspondiente.

Si `assets\icon.ico` existe, se usa como ícono de ambos ejecutables.
