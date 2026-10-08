"""
Classificador por pontuação de palavras-chave.

Por que regras em vez de machine learning?
  - Auditável: dá para dizer exatamente quais palavras casaram;
  - Não exige base de treinamento;
  - O usuário ajusta as regras sozinho em config.py.
Se o volume de documentos um dia justificar um modelo treinado,
esta é a única classe a substituir; a assinatura não muda.
"""
import re

from classification.rules import ClassificationRule


def _contem(texto: str, termo: str) -> bool:
    """Casa o termo como palavra inteira, ignorando maiúsculas/minúsculas."""
    padrao = r"\b" + re.escape(termo.lower()) + r"\b"
    return re.search(padrao, texto) is not None


class DocumentClassifier:
    def __init__(self, rules: list[ClassificationRule]):
        self.rules = rules

    def classify(self, text: str) -> ClassificationRule | None:
        """Devolve a regra com maior pontuação, ou None se nenhuma casar."""
        texto = text.lower()
        melhor: ClassificationRule | None = None
        melhor_pontos = 0
        for regra in self.rules:
            pontos = self._pontuar(regra, texto)
            if pontos is None or pontos < regra.min_pontos:
                continue
            # '>' mantém a primeira regra em caso de empate; por isso
            # as regras mais específicas vêm primeiro em config.py.
            if pontos > melhor_pontos:
                melhor, melhor_pontos = regra, pontos
        return melhor

    @staticmethod
    def _pontuar(regra: ClassificationRule, texto: str) -> int | None:
        """None = regra descartada (palavra obrigatória ausente)."""
        faltando = [t for t in regra.obrigatorias if not _contem(texto, t)]
        if faltando:
            return None
        return len(regra.obrigatorias) + sum(
            1 for t in regra.opcionais if _contem(texto, t)
        )