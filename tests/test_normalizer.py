from renaming.normalizer import normalizar


def test_exemplo_do_requisito():
    assert normalizar("  Lucas   Hubner / Empresa LTDA  ") == \
        "Lucas Hubner Empresa LTDA"


def test_remove_caracteres_proibidos():
    assert normalizar('a/b\\c:d*e?f"g<h>i|j') == "a b c d e f g h i j"


def test_preserva_acentos():
    assert normalizar("José Antônio") == "José Antônio"


def test_remove_quebras_e_tabs():
    assert normalizar("Lucas\nHubner\tEmpresa") == "Lucas Hubner Empresa"


def test_remove_ponto_final():
    # ponto final confunde com a extensão do arquivo
    assert normalizar("Empresa LTDA.") == "Empresa LTDA"


def test_limita_tamanho_sem_cortar_palavra():
    texto = "Razão Social de Uma Empresa com Nome Muito Extenso LTDA"
    assert normalizar(texto, max_tamanho=30) == "Razão Social de Uma Empresa"


def test_entrada_vazia_ou_nula():
    assert normalizar("") == ""
    assert normalizar(None) == ""