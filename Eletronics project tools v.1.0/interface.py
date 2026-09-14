"""
interface.py
------------
Interface gráfica (Tkinter) da Ferramenta de Orçamento de Projetos.

Fluxo em abas, no mesmo espírito de uma tela de "cadastro de usuário":
    1) Cadastro do Cliente / Obra
    2) Serviços a Orçar (seleção + parâmetros técnicos de cada serviço)
    3) Comercial (adicionais, margem, desconto, imposto)
    4) Resumo / Orçamento (calcular, salvar no banco, exportar para Word)
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from database import get_connection, init_db
from seed_data import (
    seed, TIPOS_EDIFICACAO, USOS_EDIFICACAO, SITUACAO_OBRA, NIVEL_ENTREGA, PRAZO,
)
import calculo
from gerar_documento import gerar_proposta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAIDA_DIR = os.path.join(BASE_DIR, "orcamentos_gerados")

COR_PRIMARIA = "#1F3A5F"
COR_FUNDO = "#F4F6F8"
FONTE_TITULO = ("Segoe UI", 15, "bold")
FONTE_LABEL = ("Segoe UI", 10)
FONTE_SECAO = ("Segoe UI", 11, "bold")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ferramenta de Orçamento de Projetos")
        self.geometry("980x680")
        self.configure(bg=COR_FUNDO)
        self.minsize(900, 620)

        init_db()
        seed()  # garante que as tabelas de referência estejam sempre atualizadas

        self.cliente_id = None
        self.servicos_vars = {}       # codigo -> BooleanVar (incluir?)
        self.servicos_widgets = {}    # codigo -> dict de widgets de parâmetros
        self.adicionais_vars = {}     # codigo -> BooleanVar
        self.ultimo_resultado = None
        self.ultimo_cliente = None

        self._montar_header()
        self._montar_abas()

    # ------------------------------------------------------------------ UI
    def _montar_header(self):
        header = tk.Frame(self, bg=COR_PRIMARIA, height=70)
        header.pack(fill="x", side="top")
        tk.Label(header, text="Ferramenta de Orçamento de Projetos", font=FONTE_TITULO,
                 bg=COR_PRIMARIA, fg="white").pack(side="left", padx=20, pady=18)
        tk.Label(header, text="Cadastro  →  Serviços  →  Comercial  →  Orçamento",
                 font=FONTE_LABEL, bg=COR_PRIMARIA, fg="#CFE0F0").pack(side="right", padx=20)

    def _montar_abas(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(16, 8))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.aba_cadastro = tk.Frame(self.notebook, bg=COR_FUNDO)
        self.aba_servicos = tk.Frame(self.notebook, bg=COR_FUNDO)
        self.aba_comercial = tk.Frame(self.notebook, bg=COR_FUNDO)
        self.aba_resumo = tk.Frame(self.notebook, bg=COR_FUNDO)

        self.notebook.add(self.aba_cadastro, text=" 1. Cadastro do Cliente ")
        self.notebook.add(self.aba_servicos, text=" 2. Serviços a Orçar ")
        self.notebook.add(self.aba_comercial, text=" 3. Comercial ")
        self.notebook.add(self.aba_resumo, text=" 4. Resumo / Orçamento ")

        self._montar_aba_cadastro()
        self._montar_aba_servicos()
        self._montar_aba_comercial()
        self._montar_aba_resumo()

    # ---------------------------------------------------------- Aba 1
    def _montar_aba_cadastro(self):
        frame = tk.Frame(self.aba_cadastro, bg=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(frame, text="Cadastro do Cliente / Obra", font=FONTE_SECAO, bg=COR_FUNDO,
                 fg=COR_PRIMARIA).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        campos = [
            ("Cliente / Empresa *", "entry", "cliente_empresa"),
            ("Endereço da obra", "entry", "endereco_obra"),
            ("Cidade/UF", "entry", "cidade_uf"),
            ("Tipo de edificação *", "combo", "tipo_edificacao", TIPOS_EDIFICACAO),
            ("Uso da edificação", "combo", "uso_edificacao", USOS_EDIFICACAO),
            ("Área aproximada (m²) *", "entry", "area_m2"),
            ("Obra nova ou existente *", "combo", "situacao_obra", SITUACAO_OBRA),
        ]

        self.vars_cadastro = {}
        r = 1
        for campo in campos:
            label, tipo, chave = campo[0], campo[1], campo[2]
            tk.Label(frame, text=label, font=FONTE_LABEL, bg=COR_FUNDO).grid(
                row=r, column=0, sticky="w", pady=6, padx=(0, 10))
            if tipo == "entry":
                var = tk.StringVar()
                ttk.Entry(frame, textvariable=var, width=45).grid(row=r, column=1, sticky="w", pady=6)
            else:
                opcoes = campo[3]
                var = tk.StringVar()
                cb = ttk.Combobox(frame, textvariable=var, values=opcoes, width=42, state="readonly")
                cb.grid(row=r, column=1, sticky="w", pady=6)
            self.vars_cadastro[chave] = var
            r += 1

        tk.Label(frame, text="Observações", font=FONTE_LABEL, bg=COR_FUNDO).grid(
            row=r, column=0, sticky="nw", pady=6)
        self.txt_observacoes = tk.Text(frame, width=45, height=4, font=FONTE_LABEL)
        self.txt_observacoes.grid(row=r, column=1, sticky="w", pady=6)
        r += 1

        self.lbl_status_cadastro = tk.Label(frame, text="Status: Pendente", font=FONTE_LABEL,
                                             bg=COR_FUNDO, fg="#B00020")
        self.lbl_status_cadastro.grid(row=r, column=0, columnspan=2, sticky="w", pady=(10, 0))
        r += 1

        btn = tk.Button(frame, text="Salvar Cadastro do Cliente", font=("Segoe UI", 10, "bold"),
                         bg=COR_PRIMARIA, fg="white", padx=16, pady=8, relief="flat",
                         command=self.salvar_cliente)
        btn.grid(row=r, column=0, columnspan=2, sticky="w", pady=20)

    def salvar_cliente(self):
        dados = {k: v.get().strip() for k, v in self.vars_cadastro.items()}
        dados["observacoes"] = self.txt_observacoes.get("1.0", "end").strip()

        if not dados["cliente_empresa"] or not dados["tipo_edificacao"] or not dados["situacao_obra"]:
            messagebox.showwarning("Campos obrigatórios",
                                    "Preencha ao menos: Cliente/Empresa, Tipo de edificação e Situação da obra.")
            return
        try:
            area = float(dados["area_m2"].replace(",", ".")) if dados["area_m2"] else 0.0
        except ValueError:
            messagebox.showerror("Erro", "Área aproximada (m²) deve ser um número.")
            return

        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO clientes (cliente_empresa, endereco_obra, cidade_uf, tipo_edificacao,
                                      uso_edificacao, area_m2, situacao_obra, observacoes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (dados["cliente_empresa"], dados["endereco_obra"], dados["cidade_uf"],
             dados["tipo_edificacao"], dados["uso_edificacao"], area, dados["situacao_obra"],
             dados["observacoes"]),
        )
        conn.commit()
        self.cliente_id = cur.lastrowid
        dados["area_m2"] = area
        self.ultimo_cliente = dados
        conn.close()

        self.lbl_status_cadastro.config(text=f"Status: Cadastrado (ID {self.cliente_id})", fg="#1B7A1B")
        messagebox.showinfo("Sucesso", "Cadastro do cliente salvo no banco de dados.")
        self._atualizar_quantidade_area()

    def _atualizar_quantidade_area(self):
        # Preenche automaticamente a quantidade (m²) do serviço "Projeto elétrico BT" com a área cadastrada
        if "EL-BT" in self.servicos_widgets:
            area_var = self.servicos_widgets["EL-BT"].get("quantidade_var")
            if area_var is not None and not area_var.get():
                area = self.vars_cadastro["area_m2"].get()
                area_var.set(area)

    # ---------------------------------------------------------- Aba 2
    def _montar_aba_servicos(self):
        outer = tk.Frame(self.aba_servicos, bg=COR_FUNDO)
        outer.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(outer, text="Serviços a Orçar", font=FONTE_SECAO, bg=COR_FUNDO,
                 fg=COR_PRIMARIA).pack(anchor="w", pady=(0, 10))

        canvas = tk.Canvas(outer, bg=COR_FUNDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COR_FUNDO)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        conn = get_connection()
        indicadores = conn.execute("SELECT * FROM indicadores").fetchall()
        conn.close()

        for ind in indicadores:
            codigo = ind["codigo"]
            box = tk.LabelFrame(scroll_frame, text=ind["tipo_projeto"], font=("Segoe UI", 10, "bold"),
                                 bg="white", fg=COR_PRIMARIA, padx=12, pady=10)
            box.pack(fill="x", pady=8, padx=4)

            incluir_var = tk.BooleanVar(value=(codigo == "EL-BT"))
            self.servicos_vars[codigo] = incluir_var
            chk = tk.Checkbutton(box, text="Incluir este serviço no orçamento", variable=incluir_var,
                                  bg="white", font=FONTE_LABEL)
            chk.grid(row=0, column=0, columnspan=4, sticky="w")

            tk.Label(box, text=f"Indicador principal: {ind['indicador_principal']} ({ind['unidade']})",
                     bg="white", font=("Segoe UI", 9), fg="#555").grid(row=1, column=0, columnspan=4,
                                                                        sticky="w", pady=(0, 6))

            tk.Label(box, text="Quantidade:", bg="white", font=FONTE_LABEL).grid(row=2, column=0, sticky="w")
            qtd_var = tk.StringVar()
            ttk.Entry(box, textvariable=qtd_var, width=12).grid(row=2, column=1, sticky="w", padx=(0, 20))

            widgets = {"quantidade_var": qtd_var, "fatores_vars": {}}

            fatores = calculo.listar_fatores_especificos(ind["tipo_projeto"])
            criterios = {}
            for f in fatores:
                criterios.setdefault(f["criterio"], []).append(f["opcao"])

            col = 2
            row_f = 2
            for criterio, opcoes in criterios.items():
                tk.Label(box, text=f"{criterio}:", bg="white", font=FONTE_LABEL).grid(
                    row=row_f, column=col, sticky="w")
                fvar = tk.StringVar(value=opcoes[0])
                ttk.Combobox(box, textvariable=fvar, values=opcoes, width=22, state="readonly").grid(
                    row=row_f, column=col + 1, sticky="w", padx=(0, 20), pady=3)
                widgets["fatores_vars"][criterio] = fvar
                row_f += 1

            self.servicos_widgets[codigo] = widgets

    # ---------------------------------------------------------- Aba 3
    def _montar_aba_comercial(self):
        frame = tk.Frame(self.aba_comercial, bg=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(frame, text="Parâmetros Comerciais", font=FONTE_SECAO, bg=COR_FUNDO,
                 fg=COR_PRIMARIA).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        tk.Label(frame, text="Nível de entrega", font=FONTE_LABEL, bg=COR_FUNDO).grid(
            row=1, column=0, sticky="w", pady=6)
        self.var_nivel_entrega = tk.StringVar(value=NIVEL_ENTREGA[2])
        ttk.Combobox(frame, textvariable=self.var_nivel_entrega, values=NIVEL_ENTREGA, width=30,
                     state="readonly").grid(row=1, column=1, sticky="w")

        tk.Label(frame, text="Prazo", font=FONTE_LABEL, bg=COR_FUNDO).grid(row=2, column=0, sticky="w", pady=6)
        self.var_prazo = tk.StringVar(value=PRAZO[0])
        ttk.Combobox(frame, textvariable=self.var_prazo, values=PRAZO, width=30,
                     state="readonly").grid(row=2, column=1, sticky="w")

        tk.Label(frame, text="Adicionais", font=FONTE_SECAO, bg=COR_FUNDO, fg=COR_PRIMARIA).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(20, 10))

        conn = get_connection()
        adicionais = conn.execute("SELECT * FROM adicionais WHERE tipo='Valor fixo'").fetchall()
        conn.close()

        r = 4
        for ad in adicionais:
            var = tk.BooleanVar(value=(ad["codigo"] == "ART"))
            self.adicionais_vars[ad["codigo"]] = var
            texto = f"{ad['nome']}  (R$ {ad['valor_fator']:.2f})" if ad["valor_fator"] > 0 else \
                    f"{ad['nome']} (valor a definir)"
            tk.Checkbutton(frame, text=texto, variable=var, bg=COR_FUNDO, font=FONTE_LABEL).grid(
                row=r, column=0, columnspan=2, sticky="w", pady=2)
            r += 1

        tk.Label(frame, text="Margem (%)", font=FONTE_LABEL, bg=COR_FUNDO).grid(
            row=r, column=0, sticky="w", pady=(20, 6))
        self.var_margem = tk.StringVar(value="10")
        ttk.Entry(frame, textvariable=self.var_margem, width=10).grid(row=r, column=1, sticky="w", pady=(20, 6))
        r += 1

        tk.Label(frame, text="Desconto (%)", font=FONTE_LABEL, bg=COR_FUNDO).grid(row=r, column=0, sticky="w", pady=6)
        self.var_desconto = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.var_desconto, width=10).grid(row=r, column=1, sticky="w", pady=6)
        r += 1

        tk.Label(frame, text="Imposto / NF (%)", font=FONTE_LABEL, bg=COR_FUNDO).grid(row=r, column=0, sticky="w", pady=6)
        self.var_imposto = tk.StringVar(value="6")
        ttk.Entry(frame, textvariable=self.var_imposto, width=10).grid(row=r, column=1, sticky="w", pady=6)

    # ---------------------------------------------------------- Aba 4
    def _montar_aba_resumo(self):
        frame = tk.Frame(self.aba_resumo, bg=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=20, pady=15)

        botoes = tk.Frame(frame, bg=COR_FUNDO)
        botoes.pack(fill="x", pady=(0, 10))

        tk.Button(botoes, text="Calcular Orçamento", font=("Segoe UI", 10, "bold"), bg=COR_PRIMARIA,
                  fg="white", padx=14, pady=8, relief="flat", command=self.calcular).pack(side="left", padx=(0, 10))
        tk.Button(botoes, text="Salvar Orçamento no Banco", font=("Segoe UI", 10, "bold"), bg="#3B6E3B",
                  fg="white", padx=14, pady=8, relief="flat", command=self.salvar_orcamento).pack(side="left", padx=(0, 10))
        tk.Button(botoes, text="Exportar para Word (.docx)", font=("Segoe UI", 10, "bold"), bg="#7A4B1F",
                  fg="white", padx=14, pady=8, relief="flat", command=self.exportar_word).pack(side="left")

        self.txt_resumo = tk.Text(frame, font=("Consolas", 10), bg="white", wrap="word")
        self.txt_resumo.pack(fill="both", expand=True)
        self.txt_resumo.insert("1.0", "Preencha o cadastro e os serviços, depois clique em 'Calcular Orçamento'.")
        self.txt_resumo.config(state="disabled")

    def _ler_servicos_selecionados(self):
        servicos = []
        tipo_edif = self.vars_cadastro["tipo_edificacao"].get()
        situacao = self.vars_cadastro["situacao_obra"].get()
        nivel = self.var_nivel_entrega.get()
        prazo = self.var_prazo.get()

        if not tipo_edif or not situacao:
            raise ValueError("Preencha o cadastro do cliente (tipo de edificação e situação da obra) antes de calcular.")

        fator_geral = calculo.obter_fator_geral(tipo_edif, situacao, nivel, prazo)

        for codigo, incluir_var in self.servicos_vars.items():
            if not incluir_var.get():
                continue
            widgets = self.servicos_widgets[codigo]
            qtd_txt = widgets["quantidade_var"].get().replace(",", ".").strip()
            if not qtd_txt:
                raise ValueError(f"Informe a quantidade/base para o serviço '{codigo}'.")
            try:
                quantidade = float(qtd_txt)
            except ValueError:
                raise ValueError(f"Quantidade inválida para o serviço '{codigo}'.")

            opcoes_especificas = {crit: var.get() for crit, var in widgets["fatores_vars"].items()}
            servico = calculo.calcular_servico(codigo, quantidade, fator_geral, opcoes_especificas)
            servicos.append(servico)

        if not servicos:
            raise ValueError("Selecione ao menos um serviço para orçar.")

        return servicos, nivel, prazo

    def calcular(self):
        try:
            servicos, nivel, prazo = self._ler_servicos_selecionados()
            codigos_adicionais = [c for c, v in self.adicionais_vars.items() if v.get()]
            margem = float(self.var_margem.get().replace(",", ".")) / 100
            desconto = float(self.var_desconto.get().replace(",", ".")) / 100
            imposto = float(self.var_imposto.get().replace(",", ".")) / 100

            resultado = calculo.calcular_orcamento(servicos, codigos_adicionais, margem, desconto, imposto)
            self.ultimo_resultado = resultado
            self.ultimo_nivel_entrega = nivel
            self.ultimo_prazo = prazo
            self._exibir_resumo(resultado)
        except ValueError as e:
            messagebox.showwarning("Atenção", str(e))
        except Exception as e:
            messagebox.showerror("Erro inesperado", str(e))

    def _fmt(self, v):
        return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _exibir_resumo(self, resultado):
        linhas = []
        linhas.append("RESUMO PRELIMINAR DO ORÇAMENTO")
        linhas.append("=" * 60)
        for s in resultado["servicos"]:
            linhas.append(f"- {s.tipo_projeto}")
            linhas.append(f"    Indicador principal : {s.indicador_principal}")
            linhas.append(f"    Quantidade / base    : {s.quantidade:g}")
            linhas.append(f"    Valor unitário base  : {self._fmt(s.valor_unitario_base)}")
            linhas.append(f"    Valor mínimo         : {self._fmt(s.valor_minimo)}")
            linhas.append(f"    Fator geral          : {s.fator_geral:.4f}")
            linhas.append(f"    Fator específico     : {s.fator_especifico:.4f}")
            linhas.append(f"    Fator total aplicado : {s.fator_total:.4f}")
            linhas.append(f"    Valor técnico        : {self._fmt(s.valor_tecnico)}")
            linhas.append("")

        linhas.append("-" * 60)
        linhas.append("COMPOSIÇÃO COMERCIAL")
        linhas.append(f"Subtotal técnico            : {self._fmt(resultado['subtotal_tecnico'])}")
        for ad in resultado["adicionais"]:
            linhas.append(f"  + {ad['nome']:<28}: {self._fmt(ad['valor'])}")
        linhas.append(f"Custos diretos (adicionais)  : {self._fmt(resultado['custos_diretos'])}")
        linhas.append(f"Margem ({resultado['margem_pct']*100:.1f}%)             : {self._fmt(resultado['valor_margem'])}")
        linhas.append(f"Desconto ({resultado['desconto_pct']*100:.1f}%)          : - {self._fmt(resultado['valor_desconto'])}")
        linhas.append(f"Imposto / NF ({resultado['imposto_pct']*100:.1f}%)       : {self._fmt(resultado['valor_imposto'])}")
        linhas.append("=" * 60)
        linhas.append(f"VALOR FINAL ESTIMADO         : {self._fmt(resultado['valor_final'])}")

        self.txt_resumo.config(state="normal")
        self.txt_resumo.delete("1.0", "end")
        self.txt_resumo.insert("1.0", "\n".join(linhas))
        self.txt_resumo.config(state="disabled")

    def salvar_orcamento(self):
        if not self.ultimo_resultado:
            messagebox.showwarning("Atenção", "Calcule o orçamento antes de salvar.")
            return
        if not self.cliente_id:
            messagebox.showwarning("Atenção", "Salve o cadastro do cliente antes de salvar o orçamento.")
            return

        r = self.ultimo_resultado
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO orcamentos (cliente_id, nivel_entrega, prazo, margem_pct, desconto_pct, imposto_pct,
                                        subtotal_tecnico, custos_diretos, valor_margem, valor_desconto,
                                        valor_imposto, valor_final)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (self.cliente_id, self.ultimo_nivel_entrega, self.ultimo_prazo, r["margem_pct"], r["desconto_pct"],
             r["imposto_pct"], r["subtotal_tecnico"], r["custos_diretos"], r["valor_margem"], r["valor_desconto"],
             r["valor_imposto"], r["valor_final"]),
        )
        orcamento_id = cur.lastrowid

        for s in r["servicos"]:
            conn.execute(
                """INSERT INTO orcamento_servicos (orcamento_id, codigo_indicador, tipo_projeto, indicador_principal,
                                                     quantidade, valor_unitario_base, valor_minimo, fator_geral,
                                                     fator_especifico, fator_total, valor_tecnico)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (orcamento_id, s.codigo_indicador, s.tipo_projeto, s.indicador_principal, s.quantidade,
                 s.valor_unitario_base, s.valor_minimo, s.fator_geral, s.fator_especifico, s.fator_total,
                 s.valor_tecnico),
            )

        for ad in r["adicionais"]:
            conn.execute(
                "INSERT INTO orcamento_adicionais (orcamento_id, codigo, nome, valor) VALUES (?, ?, ?, ?)",
                (orcamento_id, ad["codigo"], ad["nome"], ad["valor"]),
            )

        conn.commit()
        conn.close()
        self.ultimo_orcamento_id = orcamento_id
        messagebox.showinfo("Sucesso", f"Orçamento nº {orcamento_id} salvo no banco de dados.")

    def exportar_word(self):
        if not self.ultimo_resultado or not self.ultimo_cliente:
            messagebox.showwarning("Atenção", "Salve o cadastro do cliente e calcule o orçamento antes de exportar.")
            return

        os.makedirs(SAIDA_DIR, exist_ok=True)
        nome_sugerido = f"Orcamento_{self.ultimo_cliente['cliente_empresa'].replace(' ', '_')}.docx"
        caminho = filedialog.asksaveasfilename(
            title="Salvar proposta como",
            initialdir=SAIDA_DIR,
            initialfile=nome_sugerido,
            defaultextension=".docx",
            filetypes=[("Documento Word", "*.docx")],
        )
        if not caminho:
            return

        try:
            numero = getattr(self, "ultimo_orcamento_id", None)
            gerar_proposta(
                cliente=self.ultimo_cliente,
                resultado=self.ultimo_resultado,
                nivel_entrega=self.ultimo_nivel_entrega,
                prazo=self.ultimo_prazo,
                caminho_saida=caminho,
                numero_proposta=str(numero) if numero else None,
            )
            messagebox.showinfo("Sucesso", f"Proposta exportada para:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro ao exportar", str(e))


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
