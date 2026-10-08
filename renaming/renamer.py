# renaming/renamer.py
"""
Construção do nome final e execução segura da renomeação.

Separei de propósito:
    - PLANEJAR (funções puras, testáveis, rodam na prévia);
    - EXECUTAR (única função que toca no disco, só após confirmação).
"""
from pathlib import Path

from config import MAIUSCULAS
from models import DocumentInfo
from renaming.normalizer import normalizar


def construir_nome(doc_rotulo: str, campos: dict[str, str],
                   template: list[str]) -> str:
    """Monta o nome a partir do template escolhido pelo usuário.

    template ex.: ["TIPO", "NUMERO", "CLIENTE"] -> "FATURA 1920 LUCAS"
    - "TIPO" usa o rótulo da classificação; os demais vêm dos campos;
    - campos ausentes são omitidos, nunca aparecem como 'None'.
    """
    partes: list[str] = []
    for fid in template:
        bruto = doc_rotulo if fid == "TIPO" else campos.get(fid, "")
        limpo = normalizar(bruto)
        if limpo:
            partes.append(limpo)
    nome = " ".join(partes)
    if MAIUSCULAS:
        nome = nome.upper()
    return nome or "DOCUMENTO_SEM_NOME"


def resolver_duplicado(destino: Path,
                       ocupados: set[str] | None = None) -> Path:
    """Nunca sobrescreve. Se o nome existe no disco (ou já foi planejado
    nesta execução), acrescenta (1), (2), ...:

    FATURA 1920 LUCAS.pdf -> FATURA 1920 LUCAS (1).pdf
    """
    ocupados = ocupados or set()
    if not destino.exists() and destino.name not in ocupados:
        return destino
    contador = 1
    while True:
        candidato = destino.with_name(
            f"{destino.stem} ({contador}){destino.suffix}")
        if not candidato.exists() and candidato.name not in ocupados:
            return candidato
        contador += 1


def planejar_renomeacoes(
    resultados: list[DocumentInfo], template: list[str]
) -> list[tuple[DocumentInfo, Path]]:
    """Calcula o novo nome de cada arquivo elegível, sem tocar no disco.

    Também marca arquivos cujo nome já está correto (nada a fazer).
    """
    planos: list[tuple[DocumentInfo, Path]] = []
    ocupados: set[str] = set()
    for info in resultados:
        if info.error or info.skip_reason:
            continue
        nome = construir_nome(info.doc_rotulo, info.fields, template)
        destino = info.original_path.with_name(f"{nome}.pdf")
        if destino.name == info.original_path.name:
            info.new_name = destino.name
            info.skip_reason = "já está com o nome desejado"
            continue
        destino = resolver_duplicado(destino, ocupados)
        ocupados.add(destino.name)
        info.new_name = destino.name
        planos.append((info, destino))
    return planos


def executar_renomeacoes(
    planos: list[tuple[DocumentInfo, Path]]
) -> list[tuple[DocumentInfo, Path, str | None]]:
    """Único ponto do programa que modifica o sistema de arquivos.

    Reconfere duplicidades no instante da execução: outro processo pode
    ter criado um arquivo entre a prévia e a confirmação. Nesse caso o
    sufixo (1), (2)... é aplicado e o relatório mostra o nome final real.
    """
    executados: list[tuple[DocumentInfo, Path, str | None]] = []
    for info, destino_planejado in planos:
        destino = resolver_duplicado(destino_planejado)
        try:
            info.original_path.rename(destino)
            info.renamed = True
            info.new_name = destino.name
            executados.append((info, destino, None))
        except OSError as exc:
            executados.append((info, destino, str(exc)))
    return executados