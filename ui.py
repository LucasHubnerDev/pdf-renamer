# ui.py
"""
Interface de linha de comando (etapas 1 a 4 e 6 a 7 do fluxo).
"""
from datetime import date, datetime
from pathlib import Path


def selecionar_pasta() -> Path:
    while True:
        bruto = input("\nCaminho da pasta com os PDFs: ").strip()
        bruto = bruto.strip('"').strip("'")
        pasta = Path(bruto).expanduser()
        if pasta.is_dir():
            return pasta
        print("  ✗ Pasta não encontrada, tente novamente.")


def _pedir_data(rotulo: str) -> date | None:
    while True:
        bruto = input(f"{rotulo} (dd/mm/aaaa, Enter ignora): ").strip()
        if not bruto:
            return None
        try:
            return datetime.strptime(bruto, "%d/%m/%Y").date()
        except ValueError:
            print("  ✗ Data inválida, use dd/mm/aaaa.")


def ler_periodo() -> tuple[date | None, date | None]:
    """Período opcional: Enter vazio desliga o filtro daquela ponta."""
    print("\nPeríodo dos documentos:")
    inicial = _pedir_data("  Data inicial")
    final = _pedir_data("  Data final")
    if inicial and final and inicial > final:
        inicial, final = final, inicial   # usuário digitou invertido
    return inicial, final


def _escolher_da_lista(opcoes: list[str], rotulos: dict[str, str] | None = None,
                       pergunta: str = "") -> list[str]:
    """Checkbox por número; Enter = todos. Preserva a ordem do menu."""
    print(pergunta)
    for i, opcao in enumerate(opcoes, 1):
        rotulo = rotulos[opcao] if rotulos else opcao
        print(f"  [{i}] {rotulo}")
    print("  [0] TODOS")
    while True:
        bruto = input("Números separados por vírgula (Enter = TODOS): ").strip()
        if not bruto:
            return list(opcoes)
        try:
            indices = [int(x) for x in bruto.replace(" ", "").split(",")]
            if any(i < 1 or i > len(opcoes) for i in indices):
                raise ValueError
            return list(dict.fromkeys(opcoes[i - 1] for i in indices))
        except ValueError:
            print("  ✗ Entrada inválida, use números da lista.")


def escolher_tipos(disponiveis: list[str]) -> list[str]:
    return _escolher_da_lista(
        disponiveis, pergunta="\nTipos de documentos a processar:")


def escolher_campos(catalogo: dict[str, str]) -> list[str]:
    return _escolher_da_lista(
        list(catalogo), catalogo, pergunta="\nCampos a extrair:")


def escolher_ordem(campos: list[str], catalogo: dict[str, str]) -> list[str]:
    """Define a sequência dos campos no nome final
    (ex.: TIPO + NUMERO + CLIENTE)."""
    print("\nOrdem dos campos no nome do arquivo:")
    for i, fid in enumerate(campos, 1):
        print(f"  [{i}] {catalogo[fid]}")
    bruto = input("Sequência (ex.: 1,3,2; Enter mantém a ordem acima): ").strip()
    if not bruto:
        return list(campos)
    try:
        indices = [int(x) for x in bruto.replace(" ", "").split(",")]
        if sorted(indices) != list(range(1, len(campos) + 1)):
            raise ValueError
        return [campos[i - 1] for i in indices]
    except ValueError:
        print("  ✗ Ordem inválida; mantendo a ordem padrão.")
        return list(campos)


LARGURA_COLUNA = 40


def _truncar(texto: str, largura: int) -> str:
    return texto if len(texto) <= largura else texto[: largura - 3] + "..."


def mostrar_previa(pares: list[tuple[str, str]]) -> bool:
    """Etapas 6 e 7: tabela antes de renomear + confirmação explícita."""
    largura = LARGURA_COLUNA
    separador = "=" * (largura * 2 + 3)
    print("\n" + separador)
    print(f"{'ARQUIVO ORIGINAL':<{largura}}   {'NOVO NOME':<{largura}}")
    print("-" * (largura * 2 + 3))
    for original, novo in pares:
        print(f"{_truncar(original, largura):<{largura}}   "
              f"{_truncar(novo, largura)}")
    print(separador)
    resposta = input("\nDeseja executar essas alterações? [S/N]: ").strip().lower()
    return resposta in ("s", "sim")