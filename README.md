# Financeiro Kairo

Sistema desktop de gestão financeira pessoal para Linux, desenvolvido em Python. O projeto combina controle financeiro doméstico, análise de compras por item, comparação entre marcas, histórico de preços, relatórios e importação estruturada por JSON.

## Objetivos

- Registrar receitas, despesas, transferências, compras e pagamentos.
- Organizar gastos por categorias, subcategorias, tags e períodos.
- Importar compras detalhadas por JSON.
- Reconhecer produtos já cadastrados e sugerir sua categoria.
- Diferenciar produto genérico, marca, variante, embalagem e unidade.
- Comparar marcas do mesmo produto.
- Acompanhar variações de preço por estabelecimento, data e quantidade.
- Gerar dashboards, gráficos e relatórios em PDF, Excel e CSV.
- Funcionar localmente e offline, com backup simples e seguro.

## Stack proposta

- Python 3.12+
- PySide6 / Qt 6
- SQLite
- SQLAlchemy 2
- Alembic
- Pydantic
- pandas
- PyQtGraph ou Qt Charts
- ReportLab
- openpyxl
- RapidFuzz
- pytest

## Conceito central de produtos

O sistema não deve tratar `Arroz Camil 5 kg` como apenas um texto. A modelagem separa:

- Produto base: Arroz
- Marca: Camil
- Variante: Tipo 1
- Quantidade: 5
- Unidade: kg
- Embalagem: pacote
- Categoria: Alimentação / Mercearia

Isso permite comparar `Arroz Camil 5 kg`, `Arroz Tio João 5 kg` e outras marcas usando preço total e preço normalizado por quilograma.

## Documentação

- [Visão geral](docs/01-visao-geral.md)
- [Requisitos funcionais](docs/02-requisitos-funcionais.md)
- [Arquitetura](docs/03-arquitetura.md)
- [Modelo de dados](docs/04-modelo-de-dados.md)
- [Importação JSON](docs/05-importacao-json.md)
- [Categorização e aprendizado](docs/06-categorizacao-e-aprendizado.md)
- [Interface e experiência de uso](docs/07-interface-ux.md)
- [Relatórios e análises](docs/08-relatorios-e-analises.md)
- [Segurança e backup](docs/09-seguranca-e-backup.md)
- [Roadmap](docs/10-roadmap.md)

## Exemplo de importação

Consulte [`examples/compra-exemplo.json`](examples/compra-exemplo.json).

## Status

Projeto em fase de especificação e planejamento técnico.