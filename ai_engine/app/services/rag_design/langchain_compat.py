from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FallbackDocument:
    page_content: str
    metadata: dict = field(default_factory=dict)


def get_document_class():
    candidates = [
        ("langchain_core.documents", "Document"),
        ("langchain.schema", "Document"),
    ]

    for module_name, symbol in candidates:
        try:
            module = importlib.import_module(module_name)
            return getattr(module, symbol)
        except Exception:
            continue

    return FallbackDocument


def create_recursive_splitter(chunk_size: int, chunk_overlap: int):
    candidates = [
        ("langchain_text_splitters", "RecursiveCharacterTextSplitter"),
        ("langchain.text_splitter", "RecursiveCharacterTextSplitter"),
    ]

    for module_name, symbol in candidates:
        try:
            module = importlib.import_module(module_name)
            splitter_type = getattr(module, symbol)
            return splitter_type(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
            )
        except Exception:
            continue

    return None


Document = get_document_class()
