"""
main.py
-------
Ponto de entrada da Ferramenta de Orçamento de Projetos.

Como usar:
    1) Instale as dependências:  pip install -r requirements.txt
    2) Rode:                      python main.py

Na primeira execução, o programa cria automaticamente o banco de dados
SQLite (pasta "data/orcamento.db") e o popula com os indicadores, fatores
e adicionais de referência.
"""

from interface import main

if __name__ == "__main__":
    main()
