from pathlib import Path
from typing import Callable

from markitdown import MarkItDown

SKIP_SUFFIXES = {".md"}


def iter_input_files(paths: list[Path], recursive: bool) -> tuple[list[Path], list[Path]]:
    """Devuelve (archivos_a_convertir, rutas_inexistentes)."""
    files: list[Path] = []
    missing: list[Path] = []
    for path in paths:
        if path.is_dir():
            pattern = "**/*" if recursive else "*"
            files.extend(p for p in path.glob(pattern) if p.is_file())
        elif path.is_file():
            files.append(path)
        else:
            missing.append(path)
    files = [f for f in files if f.suffix.lower() not in SKIP_SUFFIXES]
    return files, missing


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


def convert_many(
    files: list[Path],
    output_dir: Path | None,
    on_result: Callable[[Path, Path | None, Exception | None], None] | None = None,
) -> tuple[int, int]:
    """Convierte cada archivo a su propio .md. Llama on_result(src, dest, error) por cada uno."""
    md = MarkItDown()
    ok, failed = 0, 0
    for src in files:
        try:
            dest = convert_file(md, src, output_dir)
            ok += 1
            if on_result:
                on_result(src, dest, None)
        except Exception as exc:
            failed += 1
            if on_result:
                on_result(src, None, exc)
    return ok, failed


def unify_files(
    files: list[Path],
    salida: Path,
    on_result: Callable[[Path, Exception | None], None] | None = None,
) -> tuple[int, int]:
    """Convierte cada archivo (en el orden dado) y escribe un único .md combinado.

    Llama on_result(src, error) por cada uno. error es None si salió bien.
    """
    md = MarkItDown()
    secciones: list[str] = []
    ok, failed = 0, 0
    for src in files:
        try:
            texto = read_as_markdown(md, src)
            secciones.append(f"## {src.stem}\n\n{texto.strip()}")
            ok += 1
            if on_result:
                on_result(src, None)
        except Exception as exc:
            failed += 1
            if on_result:
                on_result(src, exc)

    if secciones:
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text("\n\n---\n\n".join(secciones), encoding="utf-8")

    return ok, failed
