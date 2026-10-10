"""
Fixtures compartilhadas: textos extraídos dos documentos reais que o
projeto já processou (boleto Sicoob, fatura com DANFEs anexos e DANFE
de NF-e). Servem de referência para extratores e classificador.

Se um ajuste futuro quebrar a extração, o teste falha aqui primeiro,
antes de um arquivo ser renomeado errado em produção.
"""
import pytest

TEXTO_BOLETO = """\
756-5 BANCO COOPERATIVO SICOOB S.A.

BLOQUETO DE COBRANÇA

Nosso Número 0818850-2        N. do Documento 134386
Data do Documento 08/08/2026  Vencimento 18/08/2026

Multa R$ 10,29 / DIA          Juros de mora R$ 10,29 / DIA

Pagador: MAYKON VON RONDOV RODRIGUES - CPF/CNPJ: 957.642.242-68

Beneficiário: JUMBINHO 01 - CNPJ/CPF: 52.360.060/0001-19

Valor do Documento: 3.630,49

Linha Digitável:
75691.11004 01888.500293 81343.860005 1 92260000036304

Ficha de Compensação
"""

TEXTO_FATURA_PAGINA_1 = """\
DETALHAMENTO DE FATURAS

Fatura nr.: 139647
Data da Fatura: 07/10/2026
Vencimento: 22/10/2026

Cliente.: 010765 TRES MARIAS INDUSTRIA E COMERCIO LTDA
CGC/CPF 69.252.617/0008-77

VALOR TOTAL 847,17
"""

# Texto completo da fatura: página 1 + cópias dos DANFEs das NFC-e.
# A cópia traz EMISSAO própria, que polui o filtro de período se o
# texto completo for usado na extração (ver TIPOS_PRIMEIRA_PAGINA).
TEXTO_FATURA_COMPLETO = TEXTO_FATURA_PAGINA_1 + """\

DANFE - NOTA FISCAL ELETRONICA
EMISSAO: 02/09/26
CHAVE DE ACESSO 3526090013536500010655000000029680
"""

TEXTO_DANFE = """\
DANFE
NOTA FISCAL

Emissão: 15/08/2026

Nº 000.029.680  Série 11

Nome / Razão Social
PARTIDO DEMOCRATICO TRABALHISTA     05.711.064/0001-14     15/08/2026

VALOR TOTAL DA NOTA:
0,00    0,00    0,00    0,00    0,00    358,74

CHAVE DE ACESSO
"""


@pytest.fixture
def texto_boleto():
    return TEXTO_BOLETO


@pytest.fixture
def texto_fatura_pagina_1():
    return TEXTO_FATURA_PAGINA_1


@pytest.fixture
def texto_fatura_completo():
    return TEXTO_FATURA_COMPLETO


@pytest.fixture
def texto_danfe():
    return TEXTO_DANFE