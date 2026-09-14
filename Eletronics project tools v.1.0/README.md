# Ferramenta de Orçamento de Projetos

Programa em **Python** com **banco de dados SQL (SQLite)** e **interface gráfica**
(Tkinter), criado a partir da planilha `Ferramenta_Orcamento_Projetos_v1.xlsm`.

Reproduz as abas da planilha original:

| Aba original            | Onde ficou no programa                                   |
|--------------------------|------------------------------------------------------------|
| `01_Cadastro`             | Aba **"1. Cadastro do Cliente"** da interface + tabela `clientes` |
| `02_Servicos`             | Aba **"2. Serviços a Orçar"** da interface                |
| `Base_Listas`             | Listas de apoio em `seed_data.py` (tipos, usos, situações...) |
| `03_BD_Indicadores`       | Tabelas `indicadores`, `fatores_gerais`, `fatores_especificos`, `adicionais` |
| `Calc_Eletrico_BT`        | Motor de cálculo (`calculo.py`) + aba **"4. Resumo/Orçamento"** + documento Word final |

## Estrutura do projeto

```
OrcamentoProjetos/
├── main.py                 # ponto de entrada (rode este arquivo)
├── interface.py             # interface gráfica (Tkinter) - cadastro, serviços, comercial, resumo
├── database.py               # criação e conexão com o banco SQLite
├── seed_data.py               # dados de referência (indicadores, fatores, adicionais, listas)
├── calculo.py                 # motor de cálculo do orçamento
├── gerar_documento.py         # geração da proposta em Word (.docx)
├── requirements.txt
├── README.md
├── data/
│   └── orcamento.db           # banco de dados (criado automaticamente na 1ª execução)
└── orcamentos_gerados/        # pasta onde as propostas em Word são salvas
```

## Como instalar e rodar (modo fácil, com duplo clique)

Se o computador já tem Python instalado, basta:

1. Copie a pasta inteira `OrcamentoProjetos` para o computador.
2. Dê **duplo clique em `instalar.bat`** (só na primeira vez, para instalar
   as dependências). Uma janela preta vai abrir e fechar sozinha, ou vai
   pedir para você apertar uma tecla no final — é normal.
3. Depois disso, sempre que quiser abrir o programa, dê **duplo clique em
   `abrir_programa.bat`**.

Se aparecer a mensagem "Nao foi encontrado nenhum Python instalado", é
porque o Python não está instalado (ou não foi adicionado ao PATH) nesse
computador. Baixe em https://www.python.org/downloads/ e, durante a
instalação, marque a caixinha **"Add python.exe to PATH"**. Depois rode o
`instalar.bat` de novo.

## Como instalar e rodar (modo manual, via terminal)

1. Tenha o Python 3.9+ instalado.
2. Abra o PowerShell ou CMD dentro da pasta do projeto e instale as dependências:
   ```
   python -m pip install -r requirements.txt
   ```
3. Rode o programa:
   ```
   python main.py
   ```

A interface abrirá com 4 abas:

1. **Cadastro do Cliente** — nome/empresa, endereço, tipo de edificação, uso,
   área, situação da obra etc. Ao clicar em **"Salvar Cadastro do Cliente"**,
   os dados vão para a tabela `clientes` no banco.
2. **Serviços a Orçar** — marque os serviços desejados (Projeto elétrico BT,
   SPDA, Subestação aérea/abrigada, Cabeamento estruturado, Automação,
   Medição agrupada), informe a quantidade/base de cada um (ex.: área em m²,
   potência em kVA, nº de pontos) e escolha os fatores específicos
   (ex.: cargas especiais, pavimentos, altura, risco).
3. **Comercial** — nível de entrega, prazo, adicionais (ART, visita técnica,
   memorial etc.), margem, desconto e imposto/NF.
4. **Resumo / Orçamento** —
   - **Calcular Orçamento**: mostra o resumo técnico e comercial na tela;
   - **Salvar Orçamento no Banco**: grava o orçamento completo no SQLite
     (tabelas `orcamentos`, `orcamento_servicos`, `orcamento_adicionais`);
   - **Exportar para Word (.docx)**: gera a proposta final em Word, com os
     dados do cliente, o resumo técnico por serviço e a composição comercial
     (subtotal, adicionais, margem, desconto, imposto e valor final em destaque).

## Lógica de cálculo (por serviço)

```
fator_geral       = fator(Tipo de edificação) × fator(Situação da obra)
                     × fator(Nível de entrega) × fator(Prazo)
fator_especifico  = produto dos fatores específicos escolhidos para o serviço
fator_total        = fator_geral × fator_especifico
valor_tecnico       = quantidade × valor_unitario_base × fator_base × fator_total
valor_tecnico_final = máximo(valor_tecnico, valor_minimo)
```

## Composição comercial do orçamento

```
subtotal_tecnico = soma do valor técnico de todos os serviços incluídos
custos_diretos     = soma dos adicionais de valor fixo marcados (ART, visita...)
valor_margem       = (subtotal_tecnico + custos_diretos) × margem%
valor_desconto     = (subtotal_tecnico + custos_diretos) × desconto%
base                = subtotal_tecnico + custos_diretos + valor_margem - valor_desconto
valor_final         = base / (1 - imposto%)      # imposto calculado "por fora" (gross-up)
valor_imposto       = valor_final - base
```

## Observações importantes

- Todos os valores de indicadores, fatores e adicionais em `seed_data.py`
  foram construídos a partir da estrutura da planilha original
  (`03_BD_Indicadores`). Como se trata de uma tabela de referência de
  negócio, **revise e ajuste os valores unitários, mínimos e fatores**
  conforme a realidade da sua empresa antes de usar em orçamentos reais —
  isso pode ser feito diretamente no arquivo `seed_data.py` (e rodando
  `python seed_data.py` novamente) ou, futuramente, criando uma tela de
  manutenção dessas tabelas.
- O banco é local (SQLite), então todos os cadastros e orçamentos ficam
  salvos no arquivo `data/orcamento.db` — sem depender de servidor externo.
- Cada proposta gerada fica em `orcamentos_gerados/`, mas você pode escolher
  outra pasta na hora de salvar.
