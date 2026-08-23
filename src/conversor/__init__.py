import argparse
import sys
from pathlib import Path

from markitdown import MarkItDown

from conversor.completion import prompt_path

SKIP_SUFFIXES = {".md"}


def iter_input_files(paths: list[Path], recursive: bool) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            pattern = "**/*" if recursive else "*"
            files.extend(p for p in path.glob(pattern) if p.is_file())
        elif path.is_file():
            files.append(path)
        else:
            print(f"Aviso: no existe '{path}', se omite.", file=sys.stderr)
    return [f for f in files if f.suffix.lower() not in SKIP_SUFFIXES]


def convert_file(md: MarkItDown, src: Path, output_dir: Path | None) -> Path:
    result = md.convert(str(src))
    dest_dir = output_dir if output_dir is not None else src.parent
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / (src.stem + ".md")
    dest.write_text(result.text_content, encoding="utf-8")
    return dest


def read_as_markdown(md: MarkItDown, src: Path) -> str:
    if src.suffix.lower() == ".md":
        return src.read_text(encoding="utf-8")
    return md.convert(str(src)).text_content


def run_unify_mode(output_dir: Path | None) -> None:
    md = MarkItDown()
    ordered_files: list[Path] = []
    print("Modo unir: indicá los archivos uno por uno, en el orden en que querés que queden en el resultado final.")
    n = 1
    while True:
        entrada = prompt_path(f"Archivo {n} (Enter vacío para terminar la lista): ").strip().strip('"')
        if not entrada:
            break
        path = Path(entrada)
        if not path.is_file():
            print(f"Aviso: '{entrada}' no es un archivo válido, se omite.", file=sys.stderr)
            continue
        ordered_files.append(path)
        n += 1

    if not ordered_files:
        print("No se indicó ningún archivo.", file=sys.stderr)
        sys.exit(1)

    salida_entrada = prompt_path("Nombre del archivo combinado (ej: resumen.md): ").strip().strip('"')
    if not salida_entrada:
        print("No se indicó un nombre de salida.", file=sys.stderr)
        sys.exit(1)
    salida = Path(salida_entrada)
    if salida.suffix.lower() != ".md":
        salida = salida.with_suffix(".md")
    if not salida.is_absolute():
        base_dir = output_dir if output_dir is not None else ordered_files[0].parent
        salida = base_dir / salida

    secciones: list[str] = []
    ok, failed = 0, 0
    for src in ordered_files:
        try:
            texto = read_as_markdown(md, src)
            secciones.append(f"## {src.stem}\n\n{texto.strip()}")
            print(f"OK  {src}")
            ok += 1
        except Exception as exc:
            print(f"ERROR {src}: {exc}", file=sys.stderr)
            failed += 1

    if not secciones:
        print("Ningún archivo pudo incluirse.", file=sys.stderr)
        sys.exit(1)

    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text("\n\n---\n\n".join(secciones), encoding="utf-8")

    print(f"\nCombinado -> {salida}")
    print(f"Listo: {ok} incluidos, {failed} con error.")
    if failed:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="conversor",
        description="Convierte archivos (de cualquier tipo soportado por MarkItDown) a Markdown.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Archivos y/o carpetas a convertir. Si no se pasa ninguno, se pregunta por consola.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Carpeta de salida. Por defecto se guarda junto al archivo original.",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Si se pasa una carpeta, buscar archivos recursivamente en subcarpetas.",
    )
    parser.add_argument(
        "-u", "--unir",
        action="store_true",
        help="Combina varios archivos en un solo .md, en el orden que indiques por consola.",
    )
    args = parser.parse_args()

    if args.unir:
        run_unify_mode(args.output)
        return

    paths = args.paths
    recursive = args.recursive
    if not paths:
        entrada = prompt_path(
            "Ruta del archivo o carpeta a convertir\n"
            "  (si es una carpeta agregá -c al final para convertir todo lo que tiene adentro,"
            " sumá -r para incluir subcarpetas): "
        ).strip()
        carpeta_confirmada = False
        while True:
            lower = entrada.lower()
            if lower.endswith(" -c"):
                entrada = entrada[:-3].strip()
                carpeta_confirmada = True
            elif lower.endswith(" -r"):
                entrada = entrada[:-3].strip()
                recursive = True
            else:
                break
        entrada = entrada.strip().strip('"')
        if not entrada:
            print("No se ingresó ninguna ruta.", file=sys.stderr)
            sys.exit(1)
        path = Path(entrada)
        if path.is_dir() and not carpeta_confirmada:
            print(
                f"'{entrada}' es una carpeta. Si querés convertir todos los archivos que contiene, "
                f"volvé a ejecutar y escribí la ruta agregando -c al final (ej: {entrada} -c). "
                f"Agregá también -r para incluir subcarpetas.",
                file=sys.stderr,
            )
            sys.exit(1)
        paths = [path]

    files = iter_input_files(paths, recursive)
    if not files:
        print("No se encontraron archivos para convertir.", file=sys.stderr)
        sys.exit(1)

    md = MarkItDown()
    ok, failed = 0, 0
    for src in files:
        try:
            dest = convert_file(md, src, args.output)
            print(f"OK  {src} -> {dest}")
            ok += 1
        except Exception as exc:
            print(f"ERROR {src}: {exc}", file=sys.stderr)
            failed += 1

    print(f"\nListo: {ok} convertidos, {failed} con error.")
    if failed:
        sys.exit(1)
