# extraction/ocr/factory.py
"""
Fábrica/registro de motores de OCR.

Para plugar um motor novo:
    1. Crie uma subclasse de OcrEngine (ex.: easyocr_engine.py);
    2. Importe-a aqui e adicione ao dicionário _MOTORES;
    3. Aponte config.OCR_ENGINE para o nome dela.
O pipeline inteiro continua intacto.
"""
from extraction.ocr.base import OcrEngine
from extraction.ocr.tesseract_engine import TesseractEngine

_MOTORES: dict[str, type[OcrEngine]] = {
    TesseractEngine.name: TesseractEngine,
}


def criar_motor_ocr(nome: str, **kwargs) -> OcrEngine:
    try:
        return _MOTORES[nome](**kwargs)
    except KeyError:
        disponiveis = ", ".join(sorted(_MOTORES))
        raise ValueError(
            f"Motor de OCR '{nome}' não registrado. Disponíveis: {disponiveis}"
        ) from None