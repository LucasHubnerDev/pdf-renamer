# main_gui.py
"""
Interface gráfica do PDF Renamer (CustomTkinter).

Visual minimalista e moderno sobre a mesma lógica: extração,
classificação, campos, renomeação e relatório continuam sendo os
mesmos módulos; apenas a camada de interação muda.

Executar:  python main_gui.py
Requisito: pip install customtkinter
"""
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from config import DEFAULT_RULES, FIELD_CATALOG
from main import processar_pasta
from renaming.renamer import executar_renomeacoes, planejar_renomeacoes
from report import gerar_relatorio

# Em executável sem console (--windowed do PyInstaller), não existe
# stdout e qualquer print() derrubaria o programa. Redireciona para
# um log na pasta pessoal do usuário.
if getattr(sys, "frozen", False):
    log = Path.home() / "PDFRenamer.log"
    sys.stdout = sys.stderr = open(log, "a", encoding="utf-8")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Paleta minimalista
CARTAO = "#2b2b2b"        # fundo dos painéis
TEXTO_FRACO = "#9e9e9e"   # rótulos secundários
ACENTO = "#1f6aa5"        # seleção na tabela
VERDE = "#2FA572"         # botão de ação final
VERDE_ESCURO = "#278A60"


class AppPdfRenamer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PDF Renamer")
        self.geometry("1000x720")
        self.minsize(880, 620)
        self._centralizar()

        self.pasta: Path | None = None
        self.resultados: list = []
        self.planos: list = []
        self.vars_tipos: dict[str, ctk.BooleanVar] = {}
        self.vars_campos: dict[str, ctk.BooleanVar] = {}

        self._estilizar_tabela()
        self._montar_tela()

    # ------------------------------------------------------------------
    # Montagem da janela
    # ------------------------------------------------------------------
    def _centralizar(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 3
        self.geometry(f"+{x}+{y}")

    def _secao(self, titulo: str) -> ctk.CTkFrame:
        """Painel arredondado com rótulo em caixa alta.

        Devolve o quadro de CONTEÚDO interno. O rótulo fica no quadro
        externo (pack) e o conteúdo no interno; assim o conteúdo pode
        usar grid sem conflito, porque o Tkinter não permite misturar
        pack e grid dentro do MESMO contêiner.
        """
        quadro = ctk.CTkFrame(self, corner_radius=10, fg_color=CARTAO)
        quadro.pack(fill="x", padx=16, pady=(10, 0))
        ctk.CTkLabel(quadro, text=titulo.upper(),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXTO_FRACO).pack(
            anchor="w", padx=14, pady=(10, 2))
        conteudo = ctk.CTkFrame(quadro, fg_color="transparent")
        conteudo.pack(fill="x", padx=14, pady=(2, 12))
        return conteudo

    def _checkbox(self, pai, texto: str, var,
                  command=None) -> ctk.CTkCheckBox:
        return ctk.CTkCheckBox(pai, text=texto, variable=var,
                               checkbox_width=18, checkbox_height=18,
                               corner_radius=5, command=command)

    def _montar_tela(self):
        # Cabeçalho
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", padx=16, pady=(16, 4))
        ctk.CTkLabel(cabecalho, text="PDF Renamer",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkLabel(cabecalho,
                     text="  Classifica, extrai dados e renomeia seus documentos",
                     text_color=TEXTO_FRACO).pack(side="left", pady=(8, 0))

        # 1. Pasta
        quadro = self._secao("1. Pasta dos PDFs")
        self.lbl_pasta = ctk.CTkLabel(quadro, text="Nenhuma pasta selecionada",
                                      text_color=TEXTO_FRACO)
        self.lbl_pasta.pack(side="left")
        ctk.CTkButton(quadro, text="Selecionar…", width=110,
                      command=self._selecionar_pasta).pack(side="right")

        # 2. Período
        quadro = self._secao("2. Período (opcional)")
        ctk.CTkLabel(quadro, text="Data inicial:").pack(side="left")
        self.ent_ini = ctk.CTkEntry(quadro, width=110,
                                    placeholder_text="dd/mm/aaaa")
        self.ent_ini.pack(side="left", padx=(6, 16))
        ctk.CTkLabel(quadro, text="Data final:").pack(side="left")
        self.ent_fim = ctk.CTkEntry(quadro, width=110,
                                    placeholder_text="dd/mm/aaaa")
        self.ent_fim.pack(side="left", padx=6)

        # 3. Tipos (grid liberado: quadro agora é o contêiner de conteúdo)
        quadro = self._secao("3. Tipos a processar")
        self.var_todos = ctk.BooleanVar(value=True)
        self._checkbox(quadro, "Todos", self.var_todos,
                       command=self._alternar_todos).grid(
            row=0, column=0, sticky="w", padx=8, pady=3)
        tipos = [r.tipo for r in DEFAULT_RULES] + ["OUTROS"]
        for i, tipo in enumerate(tipos, start=1):
            var = ctk.BooleanVar(value=True)
            self.vars_tipos[tipo] = var
            self._checkbox(quadro, tipo, var).grid(
                row=i // 4, column=i % 4, sticky="w", padx=8, pady=3)

        # 4. Campos e ordem
        quadro = self._secao("4. Campos extraídos e ordem no nome")
        for i, (fid, rotulo) in enumerate(FIELD_CATALOG.items()):
            var = ctk.BooleanVar(value=fid in ("TIPO", "NUMERO", "CLIENTE"))
            self.vars_campos[fid] = var
            self._checkbox(quadro, rotulo, var).grid(
                row=i // 5, column=i % 5, sticky="w", padx=8, pady=3)
        linha_ordem = ctk.CTkFrame(quadro, fg_color="transparent")
        linha_ordem.grid(row=2, column=0, columnspan=5, sticky="w",
                         padx=8, pady=(6, 12))
        ctk.CTkLabel(linha_ordem,
                     text="Ordem no nome do arquivo:").pack(side="left")
        self.ent_ordem = ctk.CTkEntry(linha_ordem, width=320)
        self.ent_ordem.insert(0, "TIPO, NUMERO, CLIENTE")
        self.ent_ordem.pack(side="left", padx=8)

        # Ações
        acoes = ctk.CTkFrame(self, fg_color="transparent")
        acoes.pack(fill="x", padx=16, pady=10)
        self.btn_analisar = ctk.CTkButton(acoes, text="Analisar PDFs",
                                          command=self._analisar,
                                          height=36, corner_radius=8)
        self.btn_analisar.pack(side="left")
        self.btn_renomear = ctk.CTkButton(acoes, text="Renomear",
                                          command=self._renomear,
                                          height=36, corner_radius=8,
                                          fg_color=VERDE,
                                          hover_color=VERDE_ESCURO,
                                          state="disabled")
        self.btn_renomear.pack(side="left", padx=8)
        self.lbl_status = ctk.CTkLabel(acoes, text="",
                                       text_color=TEXTO_FRACO)
        self.lbl_status.pack(side="left", padx=10)

        # Barra de progresso (só aparece durante a análise)
        self.progresso = ctk.CTkProgressBar(self, mode="indeterminate",
                                            height=4)

        # Prévia em tabela
        self.frame_tabela = ctk.CTkFrame(self, corner_radius=10,
                                         fg_color=CARTAO)
        self.frame_tabela.pack(fill="both", expand=True, padx=16,
                               pady=(10, 16))
        ctk.CTkLabel(self.frame_tabela, text="PRÉVIA DAS ALTERAÇÕES",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXTO_FRACO).pack(
            anchor="w", padx=14, pady=(10, 4))
        tabela_quadro = ctk.CTkFrame(self.frame_tabela,
                                     fg_color="transparent")
        tabela_quadro.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        colunas = ("original", "novo", "situacao")
        self.tabela = ttk.Treeview(tabela_quadro, columns=colunas,
                                   show="headings")
        for col, titulo, largura in [("original", "Arquivo original", 300),
                                     ("novo", "Novo nome", 300),
                                     ("situacao", "Situação", 260)]:
            self.tabela.heading(col, text=titulo)
            self.tabela.column(col, width=largura)
        scroll = ctk.CTkScrollbar(tabela_quadro, command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scroll.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _estilizar_tabela(self):
        """O Treeview é o único widget ttk que sobrou; estilizado para
        combinar com o tema escuro do CustomTkinter."""
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("Treeview", background=CARTAO,
                         fieldbackground=CARTAO, foreground="#ffffff",
                         rowheight=30, borderwidth=0)
        estilo.configure("Treeview.Heading", background="#333333",
                         foreground="#cccccc", borderwidth=0,
                         font=("", 10, "bold"))
        estilo.map("Treeview", background=[("selected", ACENTO)])
        estilo.map("Treeview.Heading",
                   background=[("active", "#3a3a3a")])

    # ------------------------------------------------------------------
    # Comportamentos (idênticos à versão anterior)
    # ------------------------------------------------------------------
    def _selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta com os PDFs")
        if pasta:
            self.pasta = Path(pasta)
            self.lbl_pasta.configure(text=str(self.pasta),
                                     text_color="#ffffff")

    def _alternar_todos(self):
        for var in self.vars_tipos.values():
            var.set(self.var_todos.get())

    def _template(self) -> list[str]:
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
        self.btn_analisar.configure(state="disabled")
        self.lbl_status.configure(text="Analisando PDFs… (OCR pode demorar)")
        self.progresso.pack(fill="x", padx=16, before=self.frame_tabela)
        self.progresso.start()
        threading.Thread(target=self._analisar_em_fundo,
                         daemon=True).start()

    def _analisar_em_fundo(self):
        try:
            periodo = (self._ler_data(self.ent_ini),
                       self._ler_data(self.ent_fim))
            tipos = [t for t, v in self.vars_tipos.items() if v.get()]
            campos = [c for c, v in self.vars_campos.items() if v.get()]
            resultados = processar_pasta(self.pasta, periodo, tipos, campos)
            self.after(0, self._mostrar_resultados, resultados)
        except Exception as exc:
            self.after(0, messagebox.showerror, "Erro", str(exc))

    @staticmethod
    def _ler_data(entrada: ctk.CTkEntry):
        bruto = entrada.get().strip()
        if not bruto:
            return None
        return datetime.strptime(bruto, "%d/%m/%Y").date()

    def _mostrar_resultados(self, resultados):
        self.progresso.stop()
        self.progresso.pack_forget()
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
        self.btn_analisar.configure(state="normal")
        self.btn_renomear.configure(
            state="normal" if self.planos else "disabled")
        self.lbl_status.configure(
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
        self.btn_renomear.configure(state="disabled")
        messagebox.showinfo(
            "PDF Renamer",
            f"Processamento concluído.\nRelatório salvo em:\n"
            f"{caminho_relatorio}")


def main():
    import paths
    paths.configurar_ocr()
    AppPdfRenamer().mainloop()


if __name__ == "__main__":
    main()