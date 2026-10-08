# report.py
"""
Relatório de processamento.

Imprime um resumo no console e grava a versão completa em .txt na
própria pasta processada (com carimbo de data/hora), para auditoria.
"""
from datetime import datetime
from pathlib import Path

from models import DocumentInfo


def gerar_relatorio(resultados: list[DocumentInfo], pasta: Path) -> Path:
    ok = [r for r in resultados if r.status == "OK"]
    ignorados = [r for r in resultados if r.status == "IGNORADO"]
    erros = [r for r in resultados if r.status == "ERRO"]

    linhas = [
        "=" * 70,
        f"RELATÓRIO DE PROCESSAMENTO: {datetime.now():%d/%m/%Y %H:%M:%S}",
        f"Pasta: {pasta}",
        f"Arquivos analisados: {len(resultados)}",
        f"Renomeados: {sum(1 for r in resultados if r.renamed)}",
        f"Ignorados:  {len(ignorados)}",
        f"Com erro:   {len(erros)}",
        "=" * 70,
    ]

    if ok:
        linhas.append("\nPROCESSADOS COM SUCESSO:")
        for r in ok:
            destino = r.new_name or "-"
            situacao = "renomeado" if r.renamed else "aguardava confirmação"
            linhas.append(f"  {r.original_path.name}  ->  {destino}  [{situacao}]")

    if ignorados:
        linhas.append("\nIGNORADOS:")
        for r in ignorados:
            aviso = "" if r.date_found else "  (data não identificada)"
            linhas.append(f"  {r.original_path.name}: {r.skip_reason}{aviso}")

    if erros:
        linhas.append("\nERROS:")
        for r in erros:
            linhas.append(f"  {r.original_path.name}: {r.error}")

    relatorio = "\n".join(linhas) + "\n"
    print("\n" + relatorio)

    destino = pasta / f"relatorio_{datetime.now():%Y%m%d_%H%M%S}.txt"
    destino.write_text(relatorio, encoding="utf-8")
    return destino