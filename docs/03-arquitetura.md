# 3. Arquitetura técnica

## Stack

- Python 3.12+
- PySide6
- SQLite
- SQLAlchemy 2
- Alembic
- Pydantic
- pandas
- RapidFuzz
- PyQtGraph ou Qt Charts
- ReportLab
- openpyxl
- pytest

## Estilo arquitetural

Arquitetura modular em camadas, sem misturar widgets, regras de negócio e persistência.

```text
Presentation (PySide6)
        ↓
Application (casos de uso)
        ↓
Domain (regras e entidades)
        ↓
Infrastructure (SQLite, arquivos, relatórios)
```

## Estrutura sugerida

```text
financeirokairo/
├── src/financeiro_kairo/
│   ├── presentation/
│   │   ├── windows/
│   │   ├── dialogs/
│   │   ├── widgets/
│   │   ├── table_models/
│   │   └── viewmodels/
│   ├── application/
│   │   ├── commands/
│   │   ├── queries/
│   │   ├── services/
│   │   └── dto/
│   ├── domain/
│   │   ├── finance/
│   │   ├── catalog/
│   │   ├── purchases/
│   │   ├── budgets/
│   │   └── reports/
│   ├── infrastructure/
│   │   ├── database/
│   │   ├── repositories/
│   │   ├── importers/
│   │   ├── exporters/
│   │   ├── backup/
│   │   └── logging/
│   ├── shared/
│   │   ├── money.py
│   │   ├── normalization.py
│   │   └── exceptions.py
│   └── main.py
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── ui/
├── docs/
├── examples/
├── assets/
└── pyproject.toml
```

## Módulos de domínio

### Finance

Contas, cartões, lançamentos, transferências, recorrências e parcelamentos.

### Catalog

Produtos-base, marcas, variantes, aliases, categorias, unidades e embalagens.

### Purchases

Compras, itens, descontos, preços observados e importações.

### Budgets

Orçamentos, metas, projeções e alertas.

### Reports

Consultas agregadas, indicadores, gráficos e exportações.

## Regras técnicas

- Dinheiro deve ser representado por centavos inteiros ou `Decimal` com escala explícita.
- Quantidades físicas devem usar `Decimal`.
- Datas devem ser armazenadas em ISO 8601.
- Chaves estrangeiras do SQLite devem permanecer habilitadas.
- Alterações de esquema devem passar por Alembic.
- Importações devem usar uma única transação.
- Operações pesadas não podem bloquear a thread da interface.
- Repositórios escondem detalhes do SQL da camada de aplicação.
- Widgets não executam SQL diretamente.

## Serviços principais

- `ImportPurchaseService`
- `ProductMatcherService`
- `CategorizationService`
- `PriceNormalizationService`
- `PriceComparisonService`
- `AutocompleteService`
- `ReportService`
- `BackupService`

## Estratégia de testes

- Testes unitários para dinheiro, preço normalizado, recorrências e categorização.
- Testes de integração para repositórios e migrações.
- Testes de contrato para JSON.
- Testes de interface para fluxos críticos.
- Base SQLite temporária por teste.