# extraction/pdf_reader.py
"""
Orquestrador da leitura, implementando a estratégia do projeto:

    PDF -> possui texto útil?
             |-> SIM  -> extração de texto nativo
             |-> NÃO  -> rasteriza páginas em imagens -> OCR

Devolve sempre um PdfContent, com sucesso ou com erro descrito;
quem chama nunca precisa tratar exceção para decidir o fluxo.
"""
from pathlib import Path

from config import OCR_DPI, OCR_ENGINE, OCR_LANG
from extraction.ocr.factory import criar_motor_ocr
from extraction.text_extractor import TextExtractor, texto_e_util
from models import ExtractionMethod, PdfContent


class PdfContentReader:
    def __init__(self, motor: str = OCR_ENGINE, dpi: int = OCR_DPI,
                 lang: str = OCR_LANG):
        self.text_extractor = TextExtractor()
        self.ocr = criar_motor_ocr(motor, lang=lang)
        self.dpi = dpi

    def read(self, path: Path) -> PdfContent:
        try:
            texto = self.text_extractor.extract(path)
            if texto_e_util(texto):
                return PdfContent(text=texto,
                                  method=ExtractionMethod.TEXTO_NATIVO)
            return self._ler_com_ocr(path)
        except Exception as exc:
            return PdfContent(text="", method=ExtractionMethod.FALHOU,
                              error=str(exc))

    def _ler_com_ocr(self, path: Path) -> PdfContent:
        # Import tardio: pdf2image só é carregado se realmente houver OCR.
        from pdf2image import convert_from_path

        paginas = convert_from_path(path, dpi=self.dpi)
        partes = [self.ocr.recognize(imagem) for imagem in paginas]
        return PdfContent(text="\n".join(partes),
                          method=ExtractionMethod.OCR)