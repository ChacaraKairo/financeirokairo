# 15. Execução e desenvolvimento

## Requisitos

- Python 3.12 ou superior;
- Linux desktop com bibliotecas gráficas necessárias ao Qt;
- Git;
- ambiente virtual Python.

## Preparação

```bash
git clone https://github.com/ChacaraKairo/financeirokairo.git
cd financeirokairo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Banco de dados

Por padrão, os dados são armazenados em:

```text
~/.local/share/financeiro-kairo/financeiro-kairo.sqlite3
```

O diretório pode ser alterado com variáveis de ambiente que usam o prefixo `FINANCEIRO_KAIRO_`.

### Aplicar migrações

```bash
financeiro-kairo migrate
```

### Criação direta do schema em ambiente de desenvolvimento

```bash
financeiro-kairo init-db
```

A aplicação deve preferir migrações em instalações persistentes. A criação direta é útil para testes e protótipos descartáveis.

## Executar a interface desktop

```bash
financeiro-kairo-desktop
```

A interface inicial oferece:

- visão geral mensal;
- cadastro e consulta de contas;
- cadastro e consulta de receitas e despesas;
- navegação para compras, planejamento e relatórios;
- persistência local pelo mesmo banco utilizado pelos serviços.

## Comandos administrativos

```bash
financeiro-kairo backup
financeiro-kairo validate-backup CAMINHO_DO_ARQUIVO.sqlite3
```

## Qualidade

```bash
ruff check .
pytest
```

O GitHub Actions executa instalação, lint e testes a cada alteração relevante no pull request.

## Arquitetura atual

```text
src/financeiro_kairo/
├── application/
│   ├── schemas.py
│   └── services/
│       ├── backup.py
│       ├── catalog.py
│       ├── finance.py
│       ├── imports.py
│       ├── planning.py
│       └── reports.py
├── domain/
│   ├── models.py
│   └── planning_models.py
├── infrastructure/
│   └── database/
├── presentation/
│   └── app.py
├── cli.py
└── config.py
```

## Funcionalidades implementadas na fundação

- contas e saldos;
- receitas, despesas e transferências;
- categorias;
- produtos, marcas, variantes e aliases;
- compras detalhadas;
- importação JSON auditável;
- reconhecimento de produtos com RapidFuzz;
- preço normalizado por unidade;
- orçamentos e metas;
- recorrências e parcelamentos;
- relatórios financeiros e exportação;
- backup e validação;
- migrações Alembic;
- interface PySide6 inicial;
- testes automatizados e integração contínua.

## Limites da entrega atual

A aplicação já possui uma base executável, mas as telas de compras, planejamento e relatórios ainda devem evoluir de páginas de integração para interfaces completas. Também permanecem para ciclos seguintes: anexos, cartões com fechamento de fatura, regras visuais avançadas, internacionalização, empacotamento Linux e testes de interface.
