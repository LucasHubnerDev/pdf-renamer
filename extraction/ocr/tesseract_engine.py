# extraction/ocr/tesseract_engine.py
"""
Implementação concreta do contrato de OCR usando Tesseract.

Dependências de sistema (instaladas fora do pip):
    - binário tesseract
    - pacote de idioma português (tesseract-ocr-por)
"""
import pytesseract
from PIL import Image

from extraction.ocr.base import OcrEngine


class TesseractEngine(OcrEngine):
    name = "tesseract"

    def __init__(self, lang: str = "por", config: str = ""):
        self.lang = lang
        self.config = config

    def recognize(self, image: Image.Image) -> str:
        return pytesseract.image_to_string(image, lang=self.lang,
                                           config=self.config)