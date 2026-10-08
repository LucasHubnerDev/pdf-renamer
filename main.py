# main.py
"""
Ponto de entrada: conduz as 9 etapas do fluxo do projeto.

    1-4  preferências do usuário           (ui.py)
    5    leitura + classificação + campos  (extraction/, classification/, fields/)
    6-7  prévia e confirmação              (ui.py)
    8    renomeação                        (renaming/renamer.py)
    9    relatório                         (report.py)

Executar a partir da raiz do projeto:  python main.py
"""
from pathlib import Path

import ui
from classification.classifier import DocumentClassifier
from config import DEFAULT_RULES, FIELD_CATALOG, INCLUIR_SEM_DATA
from extraction.pdf_reader import PdfContentReader
from fields.extractors import encontrar_data_documento, extrair_fields
from models import DocumentInfo
from renaming.renamer import (
    construir_nome,
    executar_renomeacoes,
    planejar_renomeacoes,
)
from report import gerar_relatorio


def processar_pasta(
    pasta: Path,
    periodo: tuple,
    tipos: list[str],
    campos: list[str],
) -> list[DocumentInfo]:
    """Etapa 5: percorre os PDFs isolando falhas por arquivo.

    Um PDF com erro NUNCA interrompe o lote: ele entra no relatório
    e o processamento segue para os demais.
    """
    data_ini, data_fim = periodo
    pdfs = sorted(p for p in pasta.iterdir() if p.suffix.lower() == ".pdf")
    print(f"\nAnalisando {len(pdfs)} PDF(s) em {pasta} ...")

    leitor = PdfContentReader()
    classificador = DocumentClassifier(DEFAULT_RULES)

    resultados: list[DocumentInfo] = []
    for pdf in pdfs:
        info = DocumentInfo(original_path=pdf)
        resultados.append(info)
        try:
            info.content = leitor.read(pdf)
            if not info.content.ok:
                info.error = f"leitura do PDF: {info.content.error}"
                continue

            regra = classificador.classify(info.content.text)
            info.doc_type = regra.tipo if regra else "OUTROS"
            info.doc_rotulo = (regra.rotulo or regra.tipo) if regra else "OUTROS"
            info.fields = extrair_fields(info.content.text, campos)

            info.document_date = encontrar_data_documento(info.content.text)
            info.date_found = info.document_date is not None

            # Filtros do usuário: tipo e período.
            if info.doc_type not in tipos:
                info.skip_reason = f"tipo não selecionado ({info.doc_type})"
                continue
            if info.date_found and data_ini and info.document_date < data_ini:
                info.skip_reason = "fora do período (antes da data inicial)"
                continue
            if info.date_found and data_fim and info.document_date > data_fim:
                info.skip_reason = "fora do período (depois da data final)"
                continue
            if not info.date_found and not INCLUIR_SEM_DATA:
                info.skip_reason = "data não identificada no conteúdo"
        except Exception as exc:
            info.error = f"{type(exc).__name__}: {exc}"
    return resultados


def main() -> None:
    # 1. Pasta
    pasta = ui.selecionar_pasta()

    # 2. Período
    periodo = ui.ler_periodo()

    # 3. Tipos
    tipos_disponiveis = [regra.tipo for regra in DEFAULT_RULES] + ["OUTROS"]
    tipos = ui.escolher_tipos(tipos_disponiveis)

    # 4. Campos e ordem no nome
    campos = ui.escolher_campos(FIELD_CATALOG)
    template = ui.escolher_ordem(campos, FIELD_CATALOG)

    # 5. Leitura, classificação e extração
    resultados = processar_pasta(pasta, periodo, tipos, campos)

    # Aviso exigido pela especificação: data não identificada no conteúdo.
    sem_data = [r for r in resultados if not r.error and not r.date_found]
    if sem_data:
        print("\n⚠ Data não identificada no conteúdo de:")
        for r in sem_data:
            print(f"  - {r.original_path.name}")

    # 6-8. Prévia, confirmação e renomeação
    planos = planejar_renomeacoes(resultados, template)
    if not planos:
        print("\nNenhum arquivo elegível para renomeação.")
    elif ui.mostrar_previa([(i.original_path.name, d.name) for i, d in planos]):
        executar_renomeacoes(planos)
        print(f"\n{sum(1 for i in resultados if i.renamed)} arquivo(s) renomeado(s).")
    else:
        print("\nAlterações canceladas. Nenhum arquivo foi modificado.")

    # 9. Relatório
    gerar_relatorio(resultados, pasta)


if __name__ == "__main__":
    main()