# Índice da documentação

Este diretório reúne as especificações de produto, arquitetura, dados, experiência de uso e execução do Financeiro Kairo.

## Ordem recomendada de leitura

1. [Visão geral](01-visao-geral.md)
2. [Requisitos funcionais](02-requisitos-funcionais.md)
3. [Requisitos não funcionais](11-requisitos-nao-funcionais.md)
4. [Arquitetura técnica](03-arquitetura.md)
5. [Modelo de dados](04-modelo-de-dados.md)
6. [Interface e experiência de uso](07-interface-ux.md)
7. [Importação JSON](05-importacao-json.md)
8. [Categorização e aprendizado](06-categorizacao-e-aprendizado.md)
9. [Relatórios e análises](08-relatorios-e-analises.md)
10. [Segurança e backup](09-seguranca-e-backup.md)
11. [Decisões arquiteturais](13-decisoes-arquiteturais.md)
12. [Critérios de aceite do MVP](14-criterios-aceitacao-mvp.md)
13. [Roadmap](10-roadmap.md)
14. [Guia de desenvolvimento](12-guia-desenvolvimento.md)

## Mapa por objetivo

### Entender o produto

- `01-visao-geral.md`
- `02-requisitos-funcionais.md`
- `11-requisitos-nao-funcionais.md`
- `14-criterios-aceitacao-mvp.md`

### Implementar o sistema

- `03-arquitetura.md`
- `04-modelo-de-dados.md`
- `12-guia-desenvolvimento.md`
- `13-decisoes-arquiteturais.md`

### Implementar recursos especializados

- `05-importacao-json.md`
- `06-categorizacao-e-aprendizado.md`
- `07-interface-ux.md`
- `08-relatorios-e-analises.md`
- `09-seguranca-e-backup.md`

### Planejar entregas

- `10-roadmap.md`
- `14-criterios-aceitacao-mvp.md`

## Convenções documentais

- **MUST / deve:** requisito obrigatório.
- **SHOULD / deveria:** recomendação forte, desviável mediante justificativa.
- **MAY / pode:** decisão opcional.
- Valores monetários são representados em centavos inteiros, salvo indicação explícita.
- Quantidades físicas usam precisão decimal.
- Datas de calendário usam ISO 8601 (`YYYY-MM-DD`).
- Data e hora persistidas devem declarar claramente o fuso ou usar UTC.

## Manutenção

Toda alteração que modifique comportamento, modelo de dados, fluxo de interface ou segurança deve atualizar a documentação correspondente no mesmo pull request. Decisões estruturais relevantes devem ser registradas em `13-decisoes-arquiteturais.md`.