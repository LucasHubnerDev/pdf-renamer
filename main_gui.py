# main_gui.py
"""
Interface gráfica do PDF Renamer (Tkinter, já vem com o Python).

Reaproveita TODAS as camadas do projeto: extração, classificação,
campos, renomeação e relatório continuam sendo os mesmos módulos.
Apenas a interação com o usuário sai do terminal (ui.py) e vira
janelas. Esse é o payoff da arquitetura em camadas.

Executar:  python main_gui.py
"""
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from config import DEFAULT_RULES, FIELD_CATALOG
from main import processar_pasta
from renaming.renamer import executar_renomeacoes, planejar_renomeacoes
from report import gerar_relatorio

# Em executável sem console (--windowed do PyInstaller), não existe
# stdout e qualquer print() derrubaria o programa. Redireciona para
# um log na pasta pessoal (escrever ao lado do .exe falharia em
# C:\Program Files por falta de permissão).
if getattr(sys, "frozen", False):
    log = Path.home() / "PDFRenamer.log"
    sys.stdout = sys.stderr = open(log, "a", encoding="utf-8")


class AppPdfRenamer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDF Renamer")
        self.root.geometry("960x700")
        self.pasta: Path | None = None
        self.resultados: list = []
        self.planos: list = []
        self.vars_tipos: dict[str, tk.BooleanVar] = {}
        self.vars_campos: dict[str, tk.BooleanVar] = {}
        self._montar_tela()

    # ------------------------------------------------------------------
    # Construção da janela
    # ------------------------------------------------------------------
    def _montar_tela(self):
        # 1. Pasta
        quadro = ttk.LabelFrame(self.root, text="1. Pasta dos PDFs")
        quadro.pack(fill="x", padx=10, pady=4)
        self.lbl_pasta = ttk.Label(quadro, text="Nenhuma pasta selecionada")
        self.lbl_pasta.pack(side="left", padx=6, pady=6)
        ttk.Button(quadro, text="Selecionar…",
                   command=self._selecionar_pasta).pack(side="right", padx=6)

        # 2. Período
        quadro = ttk.LabelFrame(self.root, text="2. Período (opcional, dd/mm/aaaa)")
        quadro.pack(fill="x", padx=10, pady=4)
        ttk.Label(quadro, text="Data inicial:").pack(side="left", padx=(6, 2))
        self.ent_ini = ttk.Entry(quadro, width=12)
        self.ent_ini.pack(side="left", padx=2)
        ttk.Label(quadro, text="Data final:").pack(side="left", padx=(12, 2))
        self.ent_fim = ttk.Entry(quadro, width=12)
        self.ent_fim.pack(side="left", padx=2)

        # 3. Tipos
        quadro = ttk.LabelFrame(self.root, text="3. Tipos a processar")
        quadro.pack(fill="x", padx=10, pady=4)
        self.var_todos = tk.BooleanVar(value=True)
        ttk.Checkbutton(quadro, text="Todos", variable=self.var_todos,
                        command=self._alternar_todos).pack(side="left", padx=6)
        tipos = [r.tipo for r in DEFAULT_RULES] + ["OUTROS"]
        for tipo in tipos:
            var = tk.BooleanVar(value=True)
            self.vars_tipos[tipo] = var
            ttk.Checkbutton(quadro, text=tipo,
                            variable=var).pack(side="left", padx=6)

        # 4. Campos e ordem no nome
        quadro = ttk.LabelFrame(self.root,
                                text="4. Campos extraídos e ordem no nome")
        quadro.pack(fill="x", padx=10, pady=4)
        linha = ttk.Frame(quadro)
        linha.pack(fill="x", padx=6, pady=4)
        for fid, rotulo in FIELD_CATALOG.items():
            var = tk.BooleanVar(value=fid in ("TIPO", "NUMERO", "CLIENTE"))
            self.vars_campos[fid] = var
            ttk.Checkbutton(linha, text=rotulo,
                            variable=var).pack(side="left", padx=4)
        linha2 = ttk.Frame(quadro)
        linha2.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Label(linha2, text="Ordem no nome do arquivo:").pack(side="left")
        self.ent_ordem = ttk.Entry(linha2, width=40)
        self.ent_ordem.insert(0, "TIPO, NUMERO, CLIENTE")
        self.ent_ordem.pack(side="left", padx=6)

        # Ações
        quadro = ttk.Frame(self.root)
        quadro.pack(fill="x", padx=10, pady=6)
        self.btn_analisar = ttk.Button(quadro, text="Analisar PDFs",
                                       command=self._analisar)
        self.btn_analisar.pack(side="left")
        self.btn_renomear = ttk.Button(quadro, text="Renomear",
                                       command=self._renomear,
                                       state="disabled")
        self.btn_renomear.pack(side="left", padx=6)
        self.lbl_status = ttk.Label(quadro, text="")
        self.lbl_status.pack(side="left", padx=10)

        # Prévia em tabela
        quadro = ttk.LabelFrame(self.root, text="Prévia das alterações")
        quadro.pack(fill="both", expand=True, padx=10, pady=4)
        colunas = ("original", "novo", "situacao")
        self.tabela = ttk.Treeview(quadro, columns=colunas, show="headings")
        for col, titulo, largura in [("original", "Arquivo original", 300),
                                     ("novo", "Novo nome", 300),
                                     ("situacao", "Situação", 260)]:
            self.tabela.heading(col, text=titulo)
            self.tabela.column(col, width=largura)
        scroll = ttk.Scrollbar(quadro, orient="vertical",
                               command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scroll.set)
        self.tabela.pack(side="left", fill="both", expand=True,
                         padx=(6, 0), pady=6)
        scroll.pack(side="right", fill="y", pady=6)

    # ------------------------------------------------------------------
    # Comportamentos
    # ------------------------------------------------------------------
    def _selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta com os PDFs")
        if pasta:
            self.pasta = Path(pasta)
            self.lbl_pasta.config(text=str(self.pasta))

    def _alternar_todos(self):
        for var in self.vars_tipos.values():
            var.set(self.var_todos.get())

    def _template(self) -> list[str]:
        """Ordem dos campos no nome, a partir do campo de texto.
        IDs fora da ordem entram no final; sem seleção, usa só o TIPO."""
        selecionados = [f for f, v in self.vars_campos.items() if v.get()]
        pedidos = [p.strip().upper()
                   for p in self.ent_ordem.get().split(",")]
        template = [p for p in pedidos if p in selecionados]
        template += [f for f in selecionados if f not in template]
        return template or ["TIPO"]

    def _analisar(self):
        if not self.pasta:
            messagebox.showwarning("PDF Renamer",
                                   "Selecione uma pasta primeiro.")
            return
        self.btn_analisar.config(state="disabled")
        self.lbl_status.config(text="Analisando PDFs… (OCR pode demorar)")
        # OCR é pesado: roda em thread para a janela não congelar.
        threading.Thread(target=self._analisar_em_fundo,
                         daemon=True).start()

    def _analisar_em_fundo(self):
        try:
            periodo = (self._ler_data(self.ent_ini),
                       self._ler_data(self.ent_fim))
            tipos = [t for t, v in self.vars_tipos.items() if v.get()]
            campos = [c for c, v in self.vars_campos.items() if v.get()]
            resultados = processar_pasta(self.pasta, periodo, tipos, campos)
            self.root.after(0, self._mostrar_resultados, resultados)
        except Exception as exc:
            self.root.after(0, messagebox.showerror, "Erro", str(exc))

    @staticmethod
    def _ler_data(entrada: ttk.Entry):
        bruto = entrada.get().strip()
        if not bruto:
            return None
        return datetime.strptime(bruto, "%d/%m/%Y").date()

    def _mostrar_resultados(self, resultados):
        self.resultados = resultados
        self.planos = planejar_renomeacoes(resultados, self._template())
        self.tabela.delete(*self.tabela.get_children())
        for info in resultados:
            detalhe = info.skip_reason or info.error or ""
            self.tabela.insert("", "end", values=(
                info.original_path.name,
                info.new_name or "-",
                f"{info.status} {detalhe}".strip(),
            ))
        self.btn_analisar.config(state="normal")
        self.btn_renomear.config(
            state="normal" if self.planos else "disabled")
        self.lbl_status.config(
            text=f"{len(self.planos)} arquivo(s) prontos para renomear.")

    def _renomear(self):
        if not self.planos:
            return
        if not messagebox.askyesno(
                "Confirmar",
                f"Renomear {len(self.planos)} arquivo(s)?\n"
                "Os arquivos serão modificados na pasta selecionada."):
            return
        executar_renomeacoes(self.planos)
        pasta = self.planos[0][0].original_path.parent
        caminho_relatorio = gerar_relatorio(self.resultados, pasta)
        self.tabela.delete(*self.tabela.get_children())
        for info in self.resultados:
            self.tabela.insert("", "end", values=(
                info.original_path.name, info.new_name or "-",
                info.status))
        self.btn_renomear.config(state="disabled")
        messagebox.showinfo(
            "PDF Renamer",
            f"Processamento concluído.\nRelatório salvo em:\n"
            f"{caminho_relatorio}")


def main():
    import paths
    paths.configurar_ocr()
    root = tk.Tk()
    AppPdfRenamer(root)
    root.mainloop()


if __name__ == "__main__":
    main()