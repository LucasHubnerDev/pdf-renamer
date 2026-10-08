"""
Extração de campos via expressões regulares.

Para adicionar um campo novo:
    1. Escreva a função aqui;
    2. Registre-a no dicionário FIELD_EXTRACTORS;
    3. Adicione o id em config.FIELD_CATALOG para aparecer no menu.
"""
import re
from collections.abc import Callable, Iterable
from datetime import date

# ---------------------------------------------------------------------------
# Padrões compartilhados
# ---------------------------------------------------------------------------

# 31/12/2026, 31-12-2026, 31.12.2026 (aceita ano com 2 ou 4 dígitos)
RE_DATA = re.compile(r"\b(\d{2})[/\-.](\d{2})[/\-.](\d{2,4})\b")

RE_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}\b")

RE_CNPJ = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")

RE_VALOR = re.compile(r"((?:\d{1,3}\.)*\d{1,3},\d{2})")

RE_VENCIMENTO = re.compile(
    r"vencimento\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{2,4})", re.IGNORECASE
)

RE_NUMERO = re.compile(
    r"""
    (?:
          n[ºo°]\s*          # Nº / No / N°
        | n[uú]mero\b        # Número / Numero
        | nf[-\s]?e          # NF-e
    )
    \s*(?:do\s+documento|da\s+nota|da\s+fatura)?\s*
    [:\-]?\s*
    (\d{1,15})
    """,
    re.IGNORECASE | re.VERBOSE,
)

RE_CLIENTE = re.compile(
    r"^\s*(?:cliente|titular|raz[ãa]o\s+social|nome\s+do\s+cliente"
    r"|sacado|destinat[áa]rio|emitente)\s*[:\-]\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Rótulos de data em ordem de prioridade para definir a data "oficial"
# usada no filtro de período. Ajuste a ordem conforme seus documentos.
_ROTULOS_DE_DATA: list[tuple[str, str]] = [
    ("emissão", r"emiss[ãa]o\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{2,4})"),
    ("data do documento",
     r"data\s+do\s+documento\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{2,4})"),
    ("competência",
     r"compet[êe]ncia\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{2,4})"),
    ("vencimento",
     r"vencimento\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{2,4})"),
]

# ---------------------------------------------------------------------------
# Funções de extração (uma por campo)
# ---------------------------------------------------------------------------

def _data_de(bruto: str) -> date | None:
    partes = re.split(r"\D", bruto)
    dia, mes, ano = (int(p) for p in partes)
    if ano < 100:
        ano += 2000
    try:
        return date(ano, mes, dia)
    except ValueError:
        return None


def _data_plausivel(d: date | None) -> bool:
    return d is not None and date(2000, 1, 1) <= d <= date(2100, 1, 1)


def _primeira_data(texto: str) -> date | None:
    for m in RE_DATA.finditer(texto):
        d = _data_de(m.group(0))
        if _data_plausivel(d):
            return d
    return None


def encontrar_data_documento(texto: str) -> date | None:
    """Data 'oficial' do documento para o filtro de período.

    Estratégia: rótulos explícitos na ordem de prioridade definida em
    _ROTULOS_DE_DATA; se nenhum casar, usa a primeira data plausível
    do texto. Nunca usa a data de modificação do sistema de arquivos.
    """
    for _, padrao in _ROTULOS_DE_DATA:
        m = re.search(padrao, texto, re.IGNORECASE)
        if m:
            d = _data_de(m.group(1))
            if _data_plausivel(d):
                return d
    return _primeira_data(texto)


def extrair_numero(texto: str) -> str | None:
    m = RE_NUMERO.search(texto)
    return m.group(1) if m else None


def extrair_cliente(texto: str) -> str | None:
    m = RE_CLIENTE.search(texto)
    return m.group(1) if m else None


def extrair_cpf(texto: str) -> str | None:
    m = RE_CPF.search(texto)
    return m.group(0) if m else None


def extrair_cnpj(texto: str) -> str | None:
    m = RE_CNPJ.search(texto)
    return m.group(0) if m else None


def extrair_valor(texto: str) -> str | None:
    """Procura valores monetários em ordem de confiança:
    'R$ 1.234,56' > 'VALOR: 1.234,56' > primeiro '1.234,56' do texto."""
    m = re.search(r"R\$\s*((?:\d{1,3}\.)*\d{1,3},\d{2})", texto)
    if not m:
        m = re.search(r"valor[^\n\d]{0,40}?((?:\d{1,3}\.)*\d{1,3},\d{2})",
                      texto, re.IGNORECASE)
    if not m:
        m = RE_VALOR.search(texto)
    return m.group(1) if m else None


def extrair_vencimento(texto: str) -> str | None:
    """Vencimento formatado para nome de arquivo (barras viram hífen)."""
    m = RE_VENCIMENTO.search(texto)
    if not m:
        return None
    return m.group(1).replace("/", "-").replace(".", "-")


def extrair_data(texto: str) -> str | None:
    """Data do documento formatada para nome de arquivo."""
    d = encontrar_data_documento(texto)
    return d.strftime("%d-%m-%Y") if d else None


def extrair_codigo_barras(texto: str) -> str | None:
    """Boletos: 44 dígitos (código de barras) ou 47 (linha digitável)."""
    for bloco in re.findall(r"\d(?:[\d \t.\-]{30,})\d", texto):
        digitos = re.sub(r"\D", "", bloco)
        if 44 <= len(digitos) <= 47:
            return digitos
    return None


# ---------------------------------------------------------------------------
# Registro de campos
# ---------------------------------------------------------------------------

FIELD_EXTRACTORS: dict[str, Callable[[str], str | None]] = {
    "NUMERO": extrair_numero,
    "CLIENTE": extrair_cliente,
    "DATA": extrair_data,
    "CPF": extrair_cpf,
    "CNPJ": extrair_cnpj,
    "VALOR": extrair_valor,
    "VENCIMENTO": extrair_vencimento,
    "CODIGO_BARRAS": extrair_codigo_barras,
}


def extrair_fields(texto: str, ids_selecionados: Iterable[str]) -> dict[str, str]:
    """Extrai somente os campos pedidos. Campos não encontrados são
    simplesmente omitidos; nunca viram 'None' no nome do arquivo."""
    campos: dict[str, str] = {}
    for fid in ids_selecionados:
        extrator = FIELD_EXTRACTORS.get(fid)
        if extrator is None:      # ex.: TIPO, que vem da classificação
            continue
        valor = extrator(texto)
        if valor:
            campos[fid] = valor
    return campos