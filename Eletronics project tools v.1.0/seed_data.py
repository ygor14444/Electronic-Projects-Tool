"""
seed_data.py
------------
Popula o banco de dados com as tabelas de referência extraídas da planilha
"Ferramenta_Orcamento_Projetos" (aba 03_BD_Indicadores e Base_Listas).

Rodar uma vez (ou sempre que precisar reiniciar os dados de referência):
    python seed_data.py
"""

from database import get_connection, init_db

# ---------------------------------------------------------------------------
# 1) Indicadores principais de cada tipo de projeto
# ---------------------------------------------------------------------------
INDICADORES = [
    # codigo, tipo_projeto, indicador_principal, unidade, valor_unit_base, valor_minimo, fator_base, obs
    ("EL-BT", "Projeto elétrico BT", "Área construída", "m²", 6.5, 1200, 1,
     "Usar para projeto elétrico de baixa tensão em edificações."),
    ("SPDA", "SPDA", "Área de cobertura/projeção", "m²", 3.5, 1500, 1,
     "Projeto SPDA; gerenciamento de risco pode entrar como adicional."),
    ("SE-AER", "Subestação aérea", "Potência do transformador", "kVA", 18, 2500, 1,
     "Usar potência estimada ou transformador previsto."),
    ("SE-ABR", "Subestação abrigada", "Potência total instalada", "kVA", 28, 4500, 1,
     "Maior complexidade por envolver módulos, layout e proteção MT."),
    ("CAB", "Cabeamento estruturado", "Quantidade estimada de pontos", "ponto", 55, 900, 1,
     "Quando não houver pontos definidos, estimar por área/tipo de uso."),
    ("AUT", "Automação", "Área automatizada", "m²", 5, 1200, 1,
     "Refinar pelo nível de automação e sistemas integrados."),
    ("MED", "Medição agrupada", "Quantidade de unidades consumidoras", "unidade", 180, 1500, 1,
     "Aplicar adicional por aprovação, reforma e centros de medição."),
]

# ---------------------------------------------------------------------------
# 2) Fatores gerais (aplicam-se a qualquer tipo de projeto)
# ---------------------------------------------------------------------------
FATORES_GERAIS = [
    # categoria, opcao, fator, observacoes
    ("Tipo de edificação", "Residencial", 1.0, "Base simples."),
    ("Tipo de edificação", "Comercial", 1.3, "Lojas, escritórios, clínicas simples."),
    ("Tipo de edificação", "Industrial", 1.8, "Galpões e indústrias com maior complexidade."),
    ("Tipo de edificação", "Institucional", 1.5, "Escolas, igrejas, órgãos públicos."),
    ("Tipo de edificação", "Condomínio", 1.6, "Edificações multifamiliares, áreas comuns e medições."),
    ("Tipo de edificação", "Rural", 1.4, "Fazendas, barracões e instalações rurais."),
    ("Tipo de edificação", "Especial", 2.2, "Hospitalar, laboratório, posto de combustível, data center."),

    ("Situação da obra", "Obra nova", 1.0, "Projeto a partir de base arquitetônica ou layout definido."),
    ("Situação da obra", "Reforma", 1.3, "Exige análise do existente e adequações."),
    ("Situação da obra", "Ampliação", 1.25, "Exige compatibilização com instalação existente."),
    ("Situação da obra", "Regularização", 1.4, "Pode exigir levantamento, correções e documentação adicional."),
    ("Situação da obra", "Adequação", 1.35, "Adequação de padrão, concessionária ou norma."),

    ("Nível de entrega", "Básico", 1.0, "Projeto simples para estudo/orçamento."),
    ("Nível de entrega", "Legal/Aprovação", 1.2, "Projeto voltado à aprovação em órgão/concessionária."),
    ("Nível de entrega", "Executivo", 1.35, "Projeto detalhado para execução."),
    ("Nível de entrega", "Executivo + BIM", 1.6, "Projeto modelado/compatibilizado."),

    ("Prazo", "Normal", 1.0, "Prazo padrão comercial."),
    ("Prazo", "Urgente", 1.25, "Acréscimo por prioridade de entrega."),
]

# ---------------------------------------------------------------------------
# 3) Fatores específicos por tipo de projeto
# ---------------------------------------------------------------------------
FATORES_ESPECIFICOS = [
    # tipo_projeto, criterio, opcao, fator, observacoes
    ("Projeto elétrico BT", "Cargas especiais", "Não", 1.0, "Sem motores/elevadores/AC central/carregador."),
    ("Projeto elétrico BT", "Cargas especiais", "Sim", 1.25, "Motores, bombas, elevadores, climatização pesada, carregador veicular."),
    ("Projeto elétrico BT", "Pavimentos", "Térreo", 1.0, "Sem prumadas complexas."),
    ("Projeto elétrico BT", "Pavimentos", "2 a 4 pavimentos", 1.15, "Mais detalhamento e prumadas."),
    ("Projeto elétrico BT", "Pavimentos", "5 ou mais pavimentos", 1.35, "Prumadas e quadros por pavimento."),

    ("SPDA", "Altura", "Até 10 m", 1.0, "Edificação baixa."),
    ("SPDA", "Altura", "10 a 20 m", 1.2, "Aumenta detalhamento de descidas."),
    ("SPDA", "Altura", "Acima de 20 m", 1.45, "Maior complexidade de captação/descidas."),
    ("SPDA", "Risco", "Normal", 1.0, "Uso comum."),
    ("SPDA", "Risco", "Alto", 1.5, "Inflamáveis, grande público, industrial crítico."),

    ("Subestação aérea", "Entrada", "Aérea", 1.0, "Padrão mais simples."),
    ("Subestação aérea", "Entrada", "Subterrânea", 1.35, "Muflas, eletrodutos, caixas e detalhes adicionais."),
    ("Subestação aérea", "Faixa de potência", "Até 75 kVA", 1.0, "Baixa complexidade."),
    ("Subestação aérea", "Faixa de potência", "112,5 a 150 kVA", 1.2, "Média complexidade."),
    ("Subestação aérea", "Faixa de potência", "225 a 300 kVA", 1.45, "Média/alta complexidade."),
    ("Subestação aérea", "Faixa de potência", "Acima de 300 kVA", 1.8, "Analisar caso a caso."),

    ("Subestação abrigada", "Proteção MT", "Chave fusível", 1.0, "Solução mais simples."),
    ("Subestação abrigada", "Proteção MT", "Disjuntor MT", 1.4, "Aumenta diagrama, memorial e especificação."),
    ("Subestação abrigada", "Relé de proteção", "Não", 1.0, "Sem relé."),
    ("Subestação abrigada", "Relé de proteção", "Sim", 1.35, "Parametrização e detalhamento do relé."),
    ("Subestação abrigada", "Quantidade de transformadores", "1", 1.0, "Base."),
    ("Subestação abrigada", "Quantidade de transformadores", "2", 1.45, "Mais módulos e diagramas."),
    ("Subestação abrigada", "Quantidade de transformadores", "3 ou mais", 1.9, "Orçamento específico."),

    ("Cabeamento estruturado", "Infraestrutura", "Simples", 1.0, "Poucos pontos, sem backbone complexo."),
    ("Cabeamento estruturado", "Infraestrutura", "Com rack/sala técnica", 1.25, "Adiciona detalhamento do rack."),
    ("Cabeamento estruturado", "Infraestrutura", "Com backbone/fibra", 1.55, "Maior complexidade."),

    ("Automação", "Nível", "Simples", 1.0, "Iluminação/cenas básicas."),
    ("Automação", "Nível", "Intermediária", 1.45, "Iluminação, climatização e cenas."),
    ("Automação", "Nível", "Completa", 1.9, "Cortinas, áudio, acesso, integração."),
    ("Automação", "Nível", "Alto padrão/corporativo", 2.4, "Integração avançada e detalhamento executivo."),

    ("Medição agrupada", "Quantidade de unidades", "Até 4", 1.0, "Pequeno padrão agrupado."),
    ("Medição agrupada", "Quantidade de unidades", "5 a 12", 1.3, "Média complexidade."),
    ("Medição agrupada", "Quantidade de unidades", "13 a 24", 1.7, "Maior detalhamento."),
    ("Medição agrupada", "Quantidade de unidades", "25 a 72", 2.4, "Prédio/condomínio."),
    ("Medição agrupada", "Quantidade de unidades", "Acima de 72", 3.0, "Orçamento específico."),
]

# ---------------------------------------------------------------------------
# 4) Itens adicionais
# ---------------------------------------------------------------------------
ADICIONAIS = [
    # codigo, nome, aplicacao, tipo, valor_fator, observacoes
    ("ART", "ART de projeto", "Todos", "Valor fixo", 150, "Ajustar conforme custo real e responsabilidade."),
    ("VISITA", "Visita técnica local", "Todos", "Valor fixo", 250, "Usar quando houver necessidade de levantamento."),
    ("DESLOC", "Deslocamento fora da cidade", "Todos", "Valor fixo", 0, "Preencher manualmente conforme distância."),
    ("APROV", "Aprovação em concessionária", "Elétrico BT, Subestação, Medição", "Fator", 1.25,
     "Acréscimo por protocolo, ajustes e acompanhamento."),
    ("MEM", "Memorial descritivo", "Todos", "Valor fixo", 350, "Quando não estiver incluso no pacote básico."),
    ("LMAT", "Lista de materiais", "Todos", "Valor fixo", 300, "Quando solicitado para orçamento/execução."),
    ("GRSPDA", "Gerenciamento de risco SPDA", "SPDA", "Valor fixo", 750, "Item separado do projeto SPDA."),
    ("LAUDOSPD", "Laudo/inspeção SPDA", "SPDA", "Valor fixo", 900, "Para instalações existentes."),
    ("RELE", "Relé de proteção", "Subestação abrigada", "Valor fixo", 1200,
     "Detalhamento, parametrização preliminar e memorial."),
    ("GERADOR", "Integração com gerador", "Subestação/Elétrico", "Valor fixo", 900,
     "Intertravamentos, QTA/QGBT e diagramas."),
    ("RACK", "Rack/sala técnica", "Cabeamento", "Valor fixo", 400, "Detalhamento de rack e organização."),
    ("CMED", "Centro de medição adicional", "Medição agrupada", "Valor fixo", 500,
     "Quando houver mais de um centro de medição."),
]

# ---------------------------------------------------------------------------
# 5) Listas de apoio (usadas nos combos da interface)
# ---------------------------------------------------------------------------
TIPOS_EDIFICACAO = ["Residencial", "Comercial", "Industrial", "Institucional", "Condomínio", "Rural", "Especial"]

USOS_EDIFICACAO = ["Casa", "Loja", "Escritório", "Clínica", "Igreja", "Escola", "Galpão", "Indústria",
                   "Prédio residencial", "Condomínio", "Fazenda / Rural", "Eletroposto", "Outro"]

SITUACAO_OBRA = ["Obra nova", "Reforma", "Ampliação", "Regularização", "Adequação"]

NIVEL_ENTREGA = ["Básico", "Legal/Aprovação", "Executivo", "Executivo + BIM"]

PRAZO = ["Normal", "Urgente"]


def seed():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.executemany(
        """INSERT OR REPLACE INTO indicadores
           (codigo, tipo_projeto, indicador_principal, unidade, valor_unitario_base, valor_minimo, fator_base, observacoes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        INDICADORES,
    )

    cur.executemany(
        """INSERT OR REPLACE INTO fatores_gerais (categoria, opcao, fator, observacoes)
           VALUES (?, ?, ?, ?)""",
        FATORES_GERAIS,
    )

    cur.executemany(
        """INSERT OR REPLACE INTO fatores_especificos (tipo_projeto, criterio, opcao, fator, observacoes)
           VALUES (?, ?, ?, ?, ?)""",
        FATORES_ESPECIFICOS,
    )

    cur.executemany(
        """INSERT OR REPLACE INTO adicionais (codigo, nome, aplicacao, tipo, valor_fator, observacoes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ADICIONAIS,
    )

    conn.commit()
    conn.close()
    print("Dados de referência inseridos com sucesso.")


if __name__ == "__main__":
    seed()
