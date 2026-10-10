import pytest

from classification.classifier import DocumentClassifier, _contem
from config import DEFAULT_RULES


@pytest.fixture
def classificador():
    return DocumentClassifier(DEFAULT_RULES)


def test_boleto_sicoob_sem_palavra_boleto(classificador, texto_boleto):
    """O Sicoob não usa a palavra 'boleto' (usa 'bloqueto'); a regra
    exige 'nosso número', presente em qualquer boleto."""
    assert classificador.classify(texto_boleto).tipo == "BOLETO"


def test_fatura_vence_detalhamento(classificador, texto_fatura_pagina_1):
    """O documento se intitula 'DETALHAMENTO DE FATURAS', mas os
    opcionais da regra FATURA (fatura nr, valor total, cliente...)
    dão a ela mais pontos."""
    assert classificador.classify(texto_fatura_pagina_1).tipo == "FATURA"


def test_classificacao_usa_texto_completo(classificador, texto_fatura_completo):
    """A classificação roda no texto INTEIRO, mesmo em faturas; a
    restrição de primeira página vale só para campos e data."""
    assert classificador.classify(texto_fatura_completo).tipo == "FATURA"


def test_danfe_nota_fiscal(classificador, texto_danfe):
    assert classificador.classify(texto_danfe).tipo == "NOTA FISCAL"


def test_classifica_sem_acentos(classificador):
    """PDFs escaneados perdem acentos ('Nosso Numero'); o casamento
    precisa ignorar acentos dos dois lados."""
    regra = classificador.classify("Nosso Numero 123 Banco Coop")
    assert regra is not None and regra.tipo == "BOLETO"


def test_texto_desconhecido(classificador):
    assert classificador.classify("receita de bolo de chocolate") is None


def test_casamento_por_termo_inteiro():
    """'nf' não pode casar dentro de 'informativo' (bug clássico de
    busca sem \\b)."""
    assert not _contem("isto é informativo", "nf")
    assert _contem("NF-e de serviço", "nf")