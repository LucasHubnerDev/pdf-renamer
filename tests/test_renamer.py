from models import DocumentInfo
from renaming.renamer import (
    construir_nome,
    executar_renomeacoes,
    planejar_renomeacoes,
    resolver_duplicado,
)


# ---------------------------------------------------------------------------
# construir_nome
# ---------------------------------------------------------------------------

def test_ordem_e_maiusculas():
    nome = construir_nome(
        "FATURA",
        {"NUMERO": "139647", "CLIENTE": "Tres Marias Industria"},
        ["TIPO", "NUMERO", "CLIENTE"])
    assert nome == "FATURA 139647 TRES MARIAS INDUSTRIA"


def test_campo_ausente_e_omitido():
    nome = construir_nome(
        "NF", {"NUMERO": "000029680"}, ["TIPO", "NUMERO", "CLIENTE"])
    assert nome == "NF 000029680"
    assert "None" not in nome


def test_nome_vazio_tem_fallback():
    assert construir_nome("", {}, ["TIPO", "NUMERO"]) == "DOCUMENTO_SEM_NOME"


# ---------------------------------------------------------------------------
# resolver_duplicado
# ---------------------------------------------------------------------------

def test_sem_colisao(tmp_path):
    destino = tmp_path / "FATURA 1 X.pdf"
    assert resolver_duplicado(destino) == destino


def test_colisao_no_disco(tmp_path):
    destino = tmp_path / "FATURA 1 X.pdf"
    destino.touch()
    assert resolver_duplicado(destino).name == "FATURA 1 X (1).pdf"
    (tmp_path / "FATURA 1 X (1).pdf").touch()
    assert resolver_duplicado(destino).name == "FATURA 1 X (2).pdf"


def test_colisao_no_planejamento(tmp_path):
    """Nome livre no disco, mas já planejado para outro arquivo
    nesta execução."""
    destino = tmp_path / "FATURA 1 X.pdf"
    assert resolver_duplicado(
        destino, ocupados={"FATURA 1 X.pdf"}).name == "FATURA 1 X (1).pdf"


# ---------------------------------------------------------------------------
# planejar_renomeacoes
# ---------------------------------------------------------------------------

def _info(pasta, nome, rotulo, campos, **kwargs):
    caminho = pasta / nome
    caminho.touch()
    return DocumentInfo(original_path=caminho, doc_rotulo=rotulo,
                        fields=campos, **kwargs)


def test_exclui_arquivo_ja_correto(tmp_path):
    info = _info(tmp_path, "FATURA 1 X.pdf", "FATURA",
                 {"NUMERO": "1", "CLIENTE": "X"})
    assert planejar_renomeacoes(info_e := [info],
                                ["TIPO", "NUMERO", "CLIENTE"]) == []
    assert info.skip_reason == "já está com o nome desejado"


def test_exclui_erro_e_ignorado(tmp_path):
    com_erro = _info(tmp_path, "a.pdf", "FATURA", {}, error="falha OCR")
    ignorado = _info(tmp_path, "b.pdf", "FATURA", {"NUMERO": "9"},
                     skip_reason="fora do período")
    planos = planejar_renomeacoes([com_erro, ignorado], ["TIPO", "NUMERO"])
    assert planos == []


def test_dois_arquivos_mesmo_destino(tmp_path):
    a = _info(tmp_path, "a.pdf", "FATURA", {"NUMERO": "1", "CLIENTE": "X"})
    b = _info(tmp_path, "b.pdf", "FATURA", {"NUMERO": "1", "CLIENTE": "X"})
    planos = planejar_renomeacoes([a, b], ["TIPO", "NUMERO", "CLIENTE"])
    assert [d.name for _, d in planos] == \
        ["FATURA 1 X.pdf", "FATURA 1 X (1).pdf"]


# ---------------------------------------------------------------------------
# executar_renomeacoes
# ---------------------------------------------------------------------------

def test_executa_e_renomeia(tmp_path):
    info = _info(tmp_path, "a.pdf", "FATURA", {"NUMERO": "1", "CLIENTE": "X"})
    planos = planejar_renomeacoes([info], ["TIPO", "NUMERO", "CLIENTE"])
    executar_renomeacoes(planos)
    assert info.renamed
    assert (tmp_path / "FATURA 1 X.pdf").exists()
    assert not (tmp_path / "a.pdf").exists()


def test_reconferencia_de_colisao_na_execucao(tmp_path):
    """Outro processo criou o arquivo de destino ENTRE o planejamento
    e a execução; o sufixo (1) deve ser aplicado na hora."""
    info = _info(tmp_path, "a.pdf", "FATURA", {"NUMERO": "1", "CLIENTE": "X"})
    planos = planejar_renomeacoes([info], ["TIPO", "NUMERO", "CLIENTE"])
    (tmp_path / "FATURA 1 X.pdf").touch()
    executar_renomeacoes(planos)
    assert (tmp_path / "FATURA 1 X (1).pdf").exists()