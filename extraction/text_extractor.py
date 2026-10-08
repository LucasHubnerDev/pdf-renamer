# extraction/text_extractor.py
"""
Camada de leitura de texto nativo de PDFs (pypdf).
"""
from pathlib import Path

from pypdf import PdfReader

# Abaixo disso assumimos que o PDF é digitalizado (imagem).
MIN_CARACTERES = 40
# Fração mínima de alfanuméricos: PDFs "quebrados" devolvem muito
# símbolo/lixo de fontes sem mapa de caracteres.
MIN_ALFANUMERICOS = 0.30


def texto_e_util(texto: str) -> bool:
    """Heurística para decidir entre extração direta e OCR."""
    compacto = "".join(texto.split())
    if len(compacto) < MIN_CARACTERES:
        return False
    alfanumericos = sum(c.isalnum() for c in compacto)
    return alfanumericos / len(compacto) >= MIN_ALFANUMERICOS


class TextExtractor:
    """Extrai texto das páginas de um PDF nativo."""

    def extract(self, path: Path) -> str:
        reader = PdfReader(path)
        paginas: list[str] = []
        for pagina in reader.pages:
            try:
                paginas.append(pagina.extract_text() or "")
            except Exception:
                # Uma página problemática não pode derrubar o arquivo inteiro.
                paginas.append("")
        return "\n".join(paginas)