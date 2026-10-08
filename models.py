"""
Estruturas de dados compartilhadas por todo o projeto.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path


class ExtractionMethod(str, Enum):
    """Como o texto foi obtido; aparece no relatório e ajuda no debug."""
    TEXTO_NATIVO = "texto nativo"
    OCR = "OCR"
    FALHOU = "falhou"


@dataclass
class PdfContent:
    """Texto bruto de um PDF, independente de como foi extraído."""
    text: str
    method: ExtractionMethod
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class DocumentInfo:
    """Estado do processamento de um único arquivo PDF."""
    original_path: Path
    content: PdfContent | None = None
    doc_type: str = "OUTROS"        # tipo completo, ex.: "NOTA FISCAL"
    doc_rotulo: str = "OUTROS"      # apelido curto no arquivo, ex.: "NF"
    fields: dict[str, str] = field(default_factory=dict)
    document_date: date | None = None
    date_found: bool = False
    skip_reason: str | None = None  # None = elegível para renomear
    new_name: str | None = None
    renamed: bool = False
    error: str | None = None

    @property
    def status(self) -> str:
        if self.error:
            return "ERRO"
        if self.skip_reason:
            return "IGNORADO"
        return "OK"