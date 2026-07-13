from __future__ import annotations

import importlib
import re
from pathlib import Path

from pypdf import PdfReader

from .langchain_compat import Document

SUPPORTED_EXTENSIONS = {".md", ".pdf", ".docx"}


def _normalize_segment(segment: str) -> str:
    return re.sub(r"[\s_\-]+", "", segment.lower().strip())


def is_existing_design_document(path: Path, existing_design_folder: str) -> bool:
    target = _normalize_segment(existing_design_folder)
    if not target:
        return False

    for part in path.parts:
        if _normalize_segment(part) == target:
            return True

    return False


def discover_corpus_files(data_root: Path) -> list[Path]:
    if not data_root.exists():
        return []

    files = []
    for candidate in data_root.rglob("*"):
        if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(candidate)

    return sorted(files)


def _read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    pages = []
    reader = PdfReader(str(path))
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            pages.append(extracted)
    return "\n".join(pages)


def _read_docx(path: Path) -> str:
    try:
        module = importlib.import_module("docx")
        docx_loader = getattr(module, "Document")
    except Exception as exc:
        raise RuntimeError(
            "python-docx is required to parse .docx files. Install dependency: python-docx"
        ) from exc

    doc = docx_loader(str(path))
    lines = [paragraph.text.strip() for paragraph in doc.paragraphs if paragraph.text.strip()]
    return "\n".join(lines)


def load_file_text(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".md":
        return _read_markdown(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".docx":
        return _read_docx(path)

    return ""


def load_corpus_documents(data_root: Path, existing_design_folder: str) -> list:
    documents: list = []

    for file_path in discover_corpus_files(data_root):
        text = load_file_text(file_path).strip()
        if not text:
            continue

        rel_path = file_path.relative_to(data_root)
        parts = rel_path.parts
        top_folder = parts[0] if len(parts) > 1 else "root"

        metadata = {
            "source_path": rel_path.as_posix(),
            "source_file": file_path.name,
            "title": file_path.stem.replace("_", " ").strip(),
            "folder": top_folder,
            "doc_type": file_path.suffix.lower().lstrip("."),
            "is_existing_design": is_existing_design_document(rel_path, existing_design_folder),
            "size_bytes": file_path.stat().st_size,
        }

        documents.append(Document(page_content=text, metadata=metadata))

    return documents
