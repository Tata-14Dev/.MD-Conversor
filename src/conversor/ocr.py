import os
import shutil
import sys
from pathlib import Path

import pypdfium2 as pdfium
import pytesseract
from PIL import Image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
OCR_LANGS = "spa+eng"
MIN_CHARS_PER_PAGE = 20

_TESSERACT_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "/opt/homebrew/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/usr/bin/tesseract",
]


def _resource_dir(*parts: str) -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = Path(__file__).resolve().parents[2]
    return Path(base).joinpath(*parts)


def _find_tesseract_cmd() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in _TESSERACT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def tesseract_available() -> bool:
    return _find_tesseract_cmd() is not None


def _ensure_configured() -> None:
    cmd = _find_tesseract_cmd()
    if cmd is None:
        raise RuntimeError(
            "No se encontró Tesseract OCR instalado. Instalalo y volvé a intentar "
            "(Windows: winget install UB-Mannheim.TesseractOCR / "
            "macOS: brew install tesseract tesseract-lang)."
        )
    pytesseract.pytesseract.tesseract_cmd = cmd

    tessdata_dir = _resource_dir("assets", "tessdata")
    if tessdata_dir.exists():
        os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)


def ocr_image(path: Path) -> str:
    _ensure_configured()
    with Image.open(path) as img:
        text = pytesseract.image_to_string(img, lang=OCR_LANGS)
    return text.strip()


def _count_pdf_pages(path: Path) -> int:
    pdf = pdfium.PdfDocument(str(path))
    try:
        return len(pdf)
    finally:
        pdf.close()


def pdf_needs_ocr(path: Path, extracted_text: str) -> bool:
    try:
        n_pages = max(_count_pdf_pages(path), 1)
    except Exception:
        n_pages = 1
    avg_chars_per_page = len(extracted_text.strip()) / n_pages
    return avg_chars_per_page < MIN_CHARS_PER_PAGE


def ocr_pdf(path: Path, dpi: int = 200) -> str:
    _ensure_configured()
    scale = dpi / 72

    chunks: list[str] = []
    pdf = pdfium.PdfDocument(str(path))
    try:
        for i, page in enumerate(pdf, start=1):
            try:
                bitmap = page.render(scale=scale)
                image = bitmap.to_pil()
                text = pytesseract.image_to_string(image, lang=OCR_LANGS).strip()
                if text:
                    chunks.append(f"### Página {i}\n\n{text}")
            finally:
                page.close()
    finally:
        pdf.close()

    return "\n\n".join(chunks)
