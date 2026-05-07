from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Optional

import pypdfium2 as pdfium
from PIL import Image


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def guess_mime(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    if suffix == ".bmp":
        return "image/bmp"
    if suffix in {".tif", ".tiff"}:
        return "image/tiff"
    return "image/jpeg"


def file_to_data_url(path: str) -> str:
    file_path = Path(path).expanduser().resolve()
    raw = file_path.read_bytes()
    mime = guess_mime(file_path)
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def is_pdf(path: str) -> bool:
    return Path(path).suffix.lower() == ".pdf"


def pdf_to_data_urls(path: str, max_pages: int = 3, scale: float = 2.0) -> list[str]:
    file_path = Path(path).expanduser().resolve()
    doc = pdfium.PdfDocument(str(file_path))
    count = min(len(doc), max_pages)
    results: list[str] = []

    for index in range(count):
        page = doc[index]
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()

        if pil_image.mode not in {"RGB", "L"}:
            pil_image = pil_image.convert("RGB")

        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=90)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        results.append(f"data:image/jpeg;base64,{encoded}")

        bitmap.close()
        page.close()

    doc.close()
    return results


def normalize_image_inputs(image_url: Optional[str], image_file: Optional[str], max_pages: int) -> tuple[str, list[str]]:
    if image_url:
        return "image_url", [image_url]

    if not image_file:
        raise ValueError("Either image_url or image_file is required")

    if is_pdf(image_file):
        urls = pdf_to_data_urls(image_file, max_pages=max_pages)
        return "pdf", urls

    path = Path(image_file)
    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        # attempt to load anyway
        with Image.open(path) as _:
            pass

    return "image_file", [file_to_data_url(image_file)]
