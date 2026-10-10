"""
Extração de campos via expressões regulares.

Lição dos documentos reais (fatura, DANFE de NF-e e boleto): os
layouts são COLUNARES. O rótulo frequentemente fica em uma linha e
os valores em outra ("VALOR TOTAL DA NOTA:" / "0,00 0,00 358,74").
A estratégia central é a "janela do rótulo": achado o rótulo, olha-se
o resto da linha dele mais a linha seguinte, e extrai-se o valor
relevante dessa janela (o último valor monetário, no caso de colunas).
"""
import re
from collections.abc import Callable, Iterable
from datetime import date

# ---------------------------------------------------------------------------
# Padrões compartilhados
# ---------------------------------------------------------------------------

RE_DATA = re.compile(r"\b(\d{2})[/\-.](\d{2})[/\-.](\d{2,4})\b")

RE_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}\b")

RE_CNPJ = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")

# Valor monetário brasileiro: 847,17 ou 3.630,49
RE_MONETARIO = re.compile(r"\d{1,3}(?:\.\d{3})*,\d{2}")

RE_VENCIMENTO = re.compile(
    r"vencimento\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{2,4})", re.IGNORECASE
)

# Número do documento nos três layouts reais:
#   fatura: "Fatura nr.: 139647"   boleto: "N. do Documento 134386"
#   DANFE:  "Nº 000.029.680" (pontuado; os pontos são removidos depois)
RE_NUMERO = re.compile(
    r"""
    (?:
          fatura\s*(?:nr|n[ºo°]|no)\.?\s*[:\-]?   # Fatura nr.:
        | n[ºo°.]?\s*do\s+documento               # N. do Documento
        | n[uú]mero\s+do\s+documento
        | n[ºo°]\s*                               # Nº 000.029.680
        | n[uú]mero\s*[:\-]\s*(?=\d)              # Número: 123
    )
    \s*[:\-]?\s*
    (\d{1,3}(?:\.\d{3})+|\d{1,15})
    """,
    re.IGNORECASE | re.VERBOSE,
)

RE_CLIENTE = re.compile(
    r"(?:nome\s+do\s+cliente|raz[ãa]o\s+social|cliente|titular"
    r"|sacado|pagador|destinat[áa]rio|emitente)\s*[.:\-]+\s*",
    re.IGNORECASE,
)

# DANFE: rótulo no fim da linha, valor na linha seguinte
RE_CLIENTE_DANFE = re.compile(
    r"nome\s*[/\s]\s*raz[ãa]o\s+social\s*[:\-]?\s*\n\s*(\S.*?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Palavras que, no FIM do texto capturado, indicam que capturamos o
# rótulo da coluna seguinte e não um valor ("Pagador: ... Nosso Número").
_FIM_DE_ROTULO = ("número", "numero", "documento", "social", "fatura",
                  "boleto", "vencimento", "valor", "data", "emissão",
                  "emissao", "cnpj", "cpf", "espécie", "especie")

# Rótulos de data em ordem de prioridade para a data "oficial"
# usada no filtro de período.
_ROTULOS_DE_DATA: list[tuple[str, str]] = [
    ("emissão",
     r"emiss[ãa]o\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{2,4})"),
    ("data do documento",
     r"data\s+do\s+documento\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{2,4})"),
    ("data no início da linha",
     r"^data\s*[:\-]\s*(\d{2}[/\-.]\d{2}[/\-.]\d{2,4})"),
    ("competência",
     r"compet[êe]ncia\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{2,4})"),
    ("vencimento",
     r"vencimento\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{2,4})"),
]

# Rótulos de valor em ordem de prioridade.
_ROTULOS_VALOR = [
    r"valor\s+do\s+documento",       # boleto
    r"valor\s+total\s+da\s+nota",    # DANFE/NF-e
    r"valor\s+total",                # fatura
    r"valor\s+da\s+fatura",
]

# ---------------------------------------------------------------------------
# Datas
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

    Rótulos explícitos na ordem de prioridade; se nenhum casar, usa a
    primeira data plausível do texto. Nunca usa a data do sistema de
    arquivos. Para tipos em TIPOS_PRIMEIRA_PAGINA, rode esta função no
    texto da primeira página: páginas seguintes (cópias de NFC-e)
    trazem datas próprias que atrapalham o filtro.
    """
    for _, padrao in _ROTULOS_DE_DATA:
        m = re.search(padrao, texto, re.IGNORECASE | re.MULTILINE)
        if m:
            d = _data_de(m.group(1))
            if _data_plausivel(d):
                return d
    return _primeira_data(texto)

# ---------------------------------------------------------------------------
# Campos
# ---------------------------------------------------------------------------

def extrair_numero(texto: str) -> str | None:
    m = RE_NUMERO.search(texto)
    if not m:
        return None
    return m.group(1).replace(".", "")   # "000.029.680" -> "000029680"


def _limpar_nome(bruto: str) -> str | None:
    nome = bruto.strip()
    # "MAYKON ... - CPF/CNPJ: 957..." -> "MAYKON ..."
    nome = re.split(r"\s+-\s+(?:cpf|cnpj|cgc)", nome,
                    flags=re.IGNORECASE)[0]
    # "Cliente.: 010765 TRES MARIAS..." -> "TRES MARIAS..."
    nome = re.sub(r"^\d+\s+", "", nome).strip()
    nome = re.sub(
        r"\s*-\s*(?:\d{3}\.?\d{3}\.?\d{3}-?\d{2}"
        r"|\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\s*$",
        "", nome)
    if not nome:
        return None
    fim = nome.lower()
    if any(fim.endswith(p) for p in _FIM_DE_ROTULO):
        return None
    return nome


def extrair_cliente(texto: str) -> str | None:
    """1) rótulo e valor na mesma linha (fatura, boleto);
    2) DANFE: valor na linha seguinte ao rótulo, em colunas."""
    for m in RE_CLIENTE.finditer(texto):
        linha = texto[m.end():].split("\n", 1)[0]
        nome = _limpar_nome(linha)
        if nome:
            return nome
    m = RE_CLIENTE_DANFE.search(texto)
    if m:
        # a linha do DANFE traz nome, CNPJ e data em colunas:
        # fica só a primeira coluna
        return re.split(r"\s{2,}", m.group(1))[0]
    return None


def extrair_cpf(texto: str) -> str | None:
    m = RE_CPF.search(texto)
    return m.group(0) if m else None


def extrair_cnpj(texto: str) -> str | None:
    """Prioridade ao CNPJ do cliente: os rótulos 'CNPJ/CPF' e 'CGC/CPF'
    se referem ao destinatário/pagador nos três layouts. Sem rótulo,
    devolve o primeiro CNPJ do texto."""
    m = re.search(r"(?:cnpj\s*[/]\s*cpf|cpf\s*[/]\s*cnpj|cgc\s*[/]\s*cpf)",
                  texto, re.IGNORECASE)
    if m:
        linha_atual, _, proxima = texto[m.end():].partition("\n")
        c = RE_CNPJ.search(f"{linha_atual}\n{proxima}")
        if c:
            return c.group(0)
    m = RE_CNPJ.search(texto)
    return m.group(0) if m else None


def _ultimo_valor_apos(texto: str, padrao_rotulo: str) -> str | None:
    m = re.search(padrao_rotulo, texto, re.IGNORECASE)
    if not m:
        return None
    linha_atual, _, proxima = texto[m.end():].partition("\n")
    valores = RE_MONETARIO.findall(f"{linha_atual}\n{proxima}")
    return valores[-1] if valores else None


def extrair_valor(texto: str) -> str | None:
    """Rótulos específicos primeiro; dentro da janela do rótulo, vale o
    ÚLTIMO valor monetário (o total fica na última coluna). Sem rótulo,
    cai para o primeiro 'R$' do texto."""
    for padrao in _ROTULOS_VALOR:
        valor = _ultimo_valor_apos(texto, padrao)
        if valor:
            return valor
    m = re.search(r"R\$\s*(" + RE_MONETARIO.pattern + r")", texto)
    return m.group(1) if m else None


def extrair_vencimento(texto: str) -> str | None:
    m = RE_VENCIMENTO.search(texto)
    if not m:
        return None
    return m.group(1).replace("/", "-").replace(".", "-")


def extrair_data(texto: str) -> str | None:
    d = encontrar_data_documento(texto)
    return d.strftime("%d-%m-%Y") if d else None


def extrair_codigo_barras(texto: str) -> str | None:
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


def extrair_fields(texto: str,
                   ids_selecionados: Iterable[str]) -> dict[str, str]:
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