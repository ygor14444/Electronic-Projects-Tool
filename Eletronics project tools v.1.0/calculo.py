"""
calculo.py
----------
Motor de cálculo do orçamento, reproduzindo a lógica da aba "Calc_Eletrico_BT"
(e generalizando-a para os demais tipos de projeto da aba 03_BD_Indicadores).

Fluxo do cálculo (por serviço):
    fator_geral      = fator(Tipo de edificação) x fator(Situação da obra) x fator(Nível de entrega) x fator(Prazo)
    fator_especifico = produto dos fatores específicos escolhidos para aquele tipo de projeto
    fator_total       = fator_geral x fator_especifico
    valor_tecnico      = quantidade x valor_unitario_base x fator_base x fator_total
    valor_tecnico_min = max(valor_tecnico, valor_minimo)

Fluxo do orçamento (composição comercial):
    subtotal_tecnico = soma do valor_tecnico_min de todos os serviços incluídos
    custos_diretos    = soma dos adicionais de "Valor fixo" marcados
    valor_margem      = (subtotal_tecnico + custos_diretos) x margem_pct
    valor_desconto    = (subtotal_tecnico + custos_diretos) x desconto_pct
    base               = subtotal_tecnico + custos_diretos + valor_margem - valor_desconto
    valor_final        = base / (1 - imposto_pct)      # imposto "por fora" (gross-up), como na planilha original
    valor_imposto      = valor_final - base
"""

from dataclasses import dataclass, field
from typing import List, Dict
from database import get_connection


@dataclass
class ServicoOrcado:
    codigo_indicador: str
    tipo_projeto: str
    indicador_principal: str
    quantidade: float
    valor_unitario_base: float
    valor_minimo: float
    fator_base: float
    fator_geral: float
    fator_especifico: float
    fator_total: float = field(init=False)
    valor_tecnico: float = field(init=False)

    def __post_init__(self):
        self.fator_total = self.fator_geral * self.fator_especifico
        bruto = self.quantidade * self.valor_unitario_base * self.fator_base * self.fator_total
        self.valor_tecnico = max(bruto, self.valor_minimo)


def obter_fator_geral(tipo_edificacao: str, situacao_obra: str, nivel_entrega: str, prazo: str = "Normal") -> float:
    conn = get_connection()
    cur = conn.cursor()
    fator = 1.0
    for categoria, opcao in [
        ("Tipo de edificação", tipo_edificacao),
        ("Situação da obra", situacao_obra),
        ("Nível de entrega", nivel_entrega),
        ("Prazo", prazo),
    ]:
        row = cur.execute(
            "SELECT fator FROM fatores_gerais WHERE categoria=? AND opcao=?", (categoria, opcao)
        ).fetchone()
        if row:
            fator *= row["fator"]
    conn.close()
    return fator


def obter_indicador(codigo: str) -> Dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM indicadores WHERE codigo=?", (codigo,)).fetchone()
    conn.close()
    return dict(row) if row else None


def listar_fatores_especificos(tipo_projeto: str) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM fatores_especificos WHERE tipo_projeto=? ORDER BY criterio, id", (tipo_projeto,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def calcular_servico(codigo_indicador: str, quantidade: float, fator_geral: float,
                      opcoes_especificas: Dict[str, str]) -> ServicoOrcado:
    """
    opcoes_especificas: dict {criterio: opcao_escolhida} ex.: {"Cargas especiais": "Sim", "Pavimentos": "Térreo"}
    """
    ind = obter_indicador(codigo_indicador)
    if not ind:
        raise ValueError(f"Indicador '{codigo_indicador}' não encontrado.")

    conn = get_connection()
    fator_especifico = 1.0
    for criterio, opcao in opcoes_especificas.items():
        row = conn.execute(
            "SELECT fator FROM fatores_especificos WHERE tipo_projeto=? AND criterio=? AND opcao=?",
            (ind["tipo_projeto"], criterio, opcao),
        ).fetchone()
        if row:
            fator_especifico *= row["fator"]
    conn.close()

    return ServicoOrcado(
        codigo_indicador=codigo_indicador,
        tipo_projeto=ind["tipo_projeto"],
        indicador_principal=ind["indicador_principal"],
        quantidade=quantidade,
        valor_unitario_base=ind["valor_unitario_base"],
        valor_minimo=ind["valor_minimo"],
        fator_base=ind["fator_base"],
        fator_geral=fator_geral,
        fator_especifico=fator_especifico,
    )


def obter_adicional(codigo: str) -> Dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM adicionais WHERE codigo=?", (codigo,)).fetchone()
    conn.close()
    return dict(row) if row else None


def calcular_orcamento(servicos: List[ServicoOrcado], codigos_adicionais_fixos: List[str],
                        margem_pct: float, desconto_pct: float, imposto_pct: float) -> Dict:
    subtotal_tecnico = sum(s.valor_tecnico for s in servicos)

    custos_diretos = 0.0
    adicionais_aplicados = []
    for codigo in codigos_adicionais_fixos:
        ad = obter_adicional(codigo)
        if ad and ad["tipo"] == "Valor fixo":
            custos_diretos += ad["valor_fator"]
            adicionais_aplicados.append({"codigo": codigo, "nome": ad["nome"], "valor": ad["valor_fator"]})

    valor_margem = (subtotal_tecnico + custos_diretos) * margem_pct
    valor_desconto = (subtotal_tecnico + custos_diretos) * desconto_pct
    base = subtotal_tecnico + custos_diretos + valor_margem - valor_desconto

    if imposto_pct >= 1:
        raise ValueError("Imposto (%) deve ser menor que 100%.")
    valor_final = base / (1 - imposto_pct)
    valor_imposto = valor_final - base

    return {
        "servicos": servicos,
        "adicionais": adicionais_aplicados,
        "subtotal_tecnico": subtotal_tecnico,
        "custos_diretos": custos_diretos,
        "margem_pct": margem_pct,
        "desconto_pct": desconto_pct,
        "imposto_pct": imposto_pct,
        "valor_margem": valor_margem,
        "valor_desconto": valor_desconto,
        "valor_imposto": valor_imposto,
        "valor_final": valor_final,
    }
