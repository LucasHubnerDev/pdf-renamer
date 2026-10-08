# renaming/normalizer.py
"""
Sanitização de valores antes de entrarem no nome do arquivo.
"""
import re

# Caracteres proibidos em nomes de arquivo (interseção Windows/Linux/macOS),
# incluindo caracteres de controle (quebras de linha, tabs etc.).
_RE_PROIBIDOS = re.compile(r'[\\/:*?"<>|\x00-\x1f\x7f]')

# Espaços, tabs e quebras de linha repetidos colapsam para um espaço.
_RE_ESPACOS = re.compile(r"\s+")

MAX_TAMANHO_PADRAO = 80


def normalizar(valor: str, max_tamanho: int = MAX_TAMANHO_PADRAO) -> str:
    """Limpa um pedaço de texto para uso seguro em nome de arquivo.

    - preserva acentos;
    - substitui caracteres proibidos por espaço, e não por vazio
      ('Lucas/Hubner' -> 'Lucas Hubner', mantendo a leitura);
    - remove pontos e espaços das pontas (ponto final confunde com
      a extensão);
    - limita o tamanho sem cortar no meio de uma palavra.
    """
    if not valor:
        return ""
    texto = _RE_PROIBIDOS.sub(" ", valor)
    texto = _RE_ESPACOS.sub(" ", texto).strip()
    texto = texto.strip(" .")
    if len(texto) > max_tamanho:
        texto = texto[:max_tamanho].rsplit(" ", 1)[0].strip()
    return texto