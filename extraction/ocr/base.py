# extraction/ocr/base.py
"""
Contrato que todo mecanismo de OCR precisa cumprir.

O restante do programa só conversa com esta interface. Trocar o
Tesseract por EasyOCR, Google Vision, AWS Textract etc. significa
escrever uma nova subclasse e registrá-la na fábrica.
"""
from abc import ABC, abstractmethod

from PIL import Image


class OcrEngine(ABC):
    """Interface única entre o pipeline e o motor de OCR."""

    name: str = "base"

    @abstractmethod
    def recognize(self, image: Image.Image) -> str:
        """Recebe UMA página (imagem) e devolve o texto reconhecido."""