# classification/rules.py
"""
Definição da estrutura de uma regra de classificação.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ClassificationRule:
    """Regra declarativa de classificação por palavras-chave.

    obrigatorias: todas precisam aparecer no texto (termo inteiro,
                  ignorando maiúsculas/minúsculas).
    opcionais:    cada uma encontrada soma 1 ponto à regra.
    min_pontos:   pontuação mínima para a regra ser candidata.
    rotulo:       apelido usado no nome do arquivo (ex.: "NF");
                  se omitido, usa o próprio ``tipo``.
    """
    tipo: str
    obrigatorias: tuple[str, ...] = ()
    opcionais: tuple[str, ...] = ()
    min_pontos: int = 1
    rotulo: str | None = None