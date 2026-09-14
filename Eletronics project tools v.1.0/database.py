"""
database.py
------------
Camada de acesso ao banco de dados (SQLite) da Ferramenta de Orçamento de Projetos.

Cria e mantém as tabelas:
    clientes                -> cadastro do cliente / obra (aba 01_Cadastro)
    indicadores              -> indicadores base de cada tipo de projeto (aba 03_BD_Indicadores)
    fatores_gerais           -> fatores por tipo de edificação, situação da obra, nível de entrega e prazo
    fatores_especificos      -> fatores específicos de cada tipo de projeto (ex.: cargas especiais, pavimentos...)
    adicionais                -> itens adicionais (ART, visita técnica, aprovação, memorial, etc.)
    orcamentos                -> cabeçalho de cada orçamento gerado
    orcamento_servicos       -> serviços incluídos em cada orçamento (com o cálculo técnico)
    orcamento_adicionais     -> adicionais incluídos em cada orçamento
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "orcamento.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS clientes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_empresa     TEXT NOT NULL,
    endereco_obra       TEXT,
    cidade_uf           TEXT,
    tipo_edificacao     TEXT,
    uso_edificacao      TEXT,
    area_m2             REAL,
    situacao_obra       TEXT,
    observacoes         TEXT,
    data_cadastro       TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS indicadores (
    codigo              TEXT PRIMARY KEY,
    tipo_projeto        TEXT NOT NULL,
    indicador_principal TEXT NOT NULL,
    unidade             TEXT,
    valor_unitario_base REAL NOT NULL,
    valor_minimo        REAL NOT NULL,
    fator_base          REAL NOT NULL DEFAULT 1,
    observacoes         TEXT
);

CREATE TABLE IF NOT EXISTS fatores_gerais (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria    TEXT NOT NULL,      -- Tipo de edificação / Situação da obra / Nível de entrega / Prazo
    opcao        TEXT NOT NULL,
    fator        REAL NOT NULL,
    observacoes  TEXT,
    UNIQUE(categoria, opcao)
);

CREATE TABLE IF NOT EXISTS fatores_especificos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_projeto  TEXT NOT NULL,
    criterio      TEXT NOT NULL,     -- ex.: Cargas especiais, Pavimentos, Altura...
    opcao         TEXT NOT NULL,
    fator         REAL NOT NULL,
    observacoes   TEXT,
    UNIQUE(tipo_projeto, criterio, opcao)
);

CREATE TABLE IF NOT EXISTS adicionais (
    codigo        TEXT PRIMARY KEY,
    nome          TEXT NOT NULL,
    aplicacao     TEXT,
    tipo          TEXT NOT NULL,      -- 'Valor fixo' ou 'Fator'
    valor_fator   REAL NOT NULL,
    observacoes   TEXT
);

CREATE TABLE IF NOT EXISTS orcamentos (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id        INTEGER NOT NULL REFERENCES clientes(id),
    data_orcamento    TEXT DEFAULT (datetime('now','localtime')),
    nivel_entrega     TEXT,
    prazo             TEXT,
    margem_pct        REAL NOT NULL DEFAULT 0,
    desconto_pct      REAL NOT NULL DEFAULT 0,
    imposto_pct       REAL NOT NULL DEFAULT 0,
    subtotal_tecnico  REAL NOT NULL DEFAULT 0,
    custos_diretos    REAL NOT NULL DEFAULT 0,
    valor_margem      REAL NOT NULL DEFAULT 0,
    valor_desconto    REAL NOT NULL DEFAULT 0,
    valor_imposto     REAL NOT NULL DEFAULT 0,
    valor_final       REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orcamento_servicos (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    orcamento_id          INTEGER NOT NULL REFERENCES orcamentos(id) ON DELETE CASCADE,
    codigo_indicador      TEXT NOT NULL,
    tipo_projeto          TEXT NOT NULL,
    indicador_principal   TEXT,
    quantidade            REAL NOT NULL,
    valor_unitario_base   REAL NOT NULL,
    valor_minimo          REAL NOT NULL,
    fator_geral           REAL NOT NULL,
    fator_especifico      REAL NOT NULL,
    fator_total           REAL NOT NULL,
    valor_tecnico         REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS orcamento_adicionais (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    orcamento_id  INTEGER NOT NULL REFERENCES orcamentos(id) ON DELETE CASCADE,
    codigo        TEXT NOT NULL,
    nome          TEXT NOT NULL,
    valor         REAL NOT NULL
);
"""


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Banco de dados criado/atualizado em: {DB_PATH}")
