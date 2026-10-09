# config.py
"""
Painel de controle do sistema.

Tudo que um usuário avançado ajusta sem tocar na lógica.
Nenhuma lógica mora aqui, só declarações.
"""
from classification.rules import ClassificationRule

# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------
OCR_ENGINE = "tesseract"   # nome registrado em extraction/ocr/factory.py
OCR_LANG = "por"           # pacote de idioma do Tesseract
OCR_DPI = 300              # resolução ao rasterizar páginas escaneadas

# ---------------------------------------------------------------------------
# Políticas de renomeação
# ---------------------------------------------------------------------------
MAIUSCULAS = True          # "FATURA 1920 LUCAS" em vez de "Fatura 1920 Lucas"
INCLUIR_SEM_DATA = True    # mantém no fluxo PDFs cuja data não foi encontrada

# ---------------------------------------------------------------------------
# Catálogo de campos (id -> rótulo exibido no menu)
# ---------------------------------------------------------------------------
FIELD_CATALOG: dict[str, str] = {
    "TIPO": "Tipo do documento",
    "NUMERO": "Número",
    "CLIENTE": "Nome do cliente",
    "DATA": "Data",
    "CPF": "CPF",
    "CNPJ": "CNPJ",
    "VALOR": "Valor",
    "VENCIMENTO": "Vencimento",
    "CODIGO_BARRAS": "Código de barras",
}

# ---------------------------------------------------------------------------
# Regras de classificação
# ---------------------------------------------------------------------------
# A ORDEM IMPORTA: regras mais específicas primeiro, porque em caso de
# empate de pontuação vence a primeira da lista. "obrigatorias" = todas
# devem aparecer; "opcionais" = cada ocorrência soma ponto.
# Tipos cujos campos são extraídos SOMENTE da primeira página.
# Nas faturas deste layout, as páginas seguintes trazem cópias dos
# DANFEs das NFC-e, com datas, nomes e valores próprios que poluem
# a extração e confundem o filtro de período.
TIPOS_PRIMEIRA_PAGINA: set[str] = {"FATURA", "DETALHAMENTO DE FATURA"}

DEFAULT_RULES: list[ClassificationRule] = [
    ClassificationRule(
        tipo="NOTA FISCAL DE SERVIÇO",
        rotulo="NFS",
        obrigatorias=("nota fiscal de serviço",),
        opcionais=("cnpj", "discriminação", "código de verificação",
                   "valor dos serviços"),
    ),
    ClassificationRule(
        tipo="NOTA FISCAL",
        rotulo="NF",
        obrigatorias=("nota fiscal",),
        opcionais=("chave de acesso", "cnpj", "nf-e", "série",
                   "danfe", "icms"),
    ),
    ClassificationRule(
        tipo="FATURA",
        obrigatorias=("fatura",),
        opcionais=("fatura nr", "vencimento", "valor da fatura",
                   "valor total", "cliente"),
    ),
    ClassificationRule(
        tipo="DETALHAMENTO DE FATURA",
        obrigatorias=("detalhamento", "fatura"),
        opcionais=("vencimento", "valor"),
    ),
    ClassificationRule(
        tipo="BOLETO",
        obrigatorias=("nosso número",),
        opcionais=("bloqueto", "boleto", "linha digitável",
                   "ficha de compensação", "vencimento", "sacado",
                   "pagador", "beneficiário"),
    ),
    ClassificationRule(
        tipo="DETALHAMENTO DE BOLETO",
        obrigatorias=("detalhamento", "boleto"),
        opcionais=("linha digitável", "nosso número", "banco"),
    ),
]