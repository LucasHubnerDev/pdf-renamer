# paths.py
"""Localiza Tesseract e Poppler em qualquer cenário:
- rodando do código-fonte: usa o PATH do sistema;
- dentro do .exe: usa os binários embutidos pelo PyInstaller."""
import os
import sys
from pathlib import Path


def _base() -> Path | None:
    """Dentro do .exe, os arquivos extras ficam em _MEIPASS."""
    return Path(sys._MEIPASS) if getattr(sys, "frozen", False) else None


def configurar_ocr() -> None:
    """Liga os binários embutidos ao pytesseract. Chamar UMA vez,
    na inicialização do programa."""
    base = _base()
    if not base:
        return  # fora do .exe: pytesseract usa o PATH do sistema

    import pytesseract
    exe = base / "tesseract" / "tesseract.exe"
    if exe.exists():
        pytesseract.pytesseract.tesseract_cmd = str(exe)
        tessdata = exe.parent / "tessdata"
        if tessdata.exists():
            os.environ["TESSDATA_PREFIX"] = str(tessdata)


def caminho_poppler() -> str | None:
    base = _base()
    if base and (base / "poppler" / "bin").exists():
        return str(base / "poppler" / "bin")
    return None